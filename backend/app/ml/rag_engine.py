from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app import models
from app.logger import logger


@dataclass(slots=True)
class KnowledgeChunk:
    id: str
    source: str
    title: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGEngine:
    """Build and query a lightweight RAG index from app data and repo docs."""

    def __init__(self) -> None:
        self._repo_root = Path(__file__).resolve().parents[3]
        self._static_chunks = self._load_static_chunks()
        self._chunks: List[KnowledgeChunk] = []
        self._vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self._matrix = None
        self._last_refresh_at: datetime | None = None
        self._rebuild_index(self._static_chunks)

    def refresh_from_db(self, db: Session) -> None:
        """Rebuild the RAG corpus from static docs plus current DB state."""
        db_chunks = self._build_database_chunks(db)
        self._rebuild_index(self._static_chunks + db_chunks)
        self._last_refresh_at = datetime.utcnow()
        logger.info("RAG index refreshed with %s chunks.", len(self._chunks))

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip() or not self._chunks or self._matrix is None:
            return []

        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix).flatten()
        ranked_indices = scores.argsort()[::-1]

        results: List[Dict[str, Any]] = []
        for index in ranked_indices:
            chunk = self._chunks[index]
            results.append(
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "title": chunk.title,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                    "score": float(scores[index]),
                }
            )
            if len(results) >= top_k:
                break

        return results

    def build_context(self, query: str, top_k: int = 5) -> str:
        results = self.search(query, top_k=top_k)
        if not results:
            return "Контекст не найден."

        blocks: List[str] = []
        for idx, item in enumerate(results, start=1):
            blocks.append(
                f"[{idx}] {item['source']} | {item['title']} | relevance={item['score']:.3f}\n"
                f"{self._truncate(item['text'], 700)}"
            )
        return "\n\n".join(blocks)

    def _rebuild_index(self, chunks: List[KnowledgeChunk]) -> None:
        self._chunks = [chunk for chunk in chunks if chunk.text.strip()]
        texts = [chunk.text for chunk in self._chunks]

        if not texts:
            self._matrix = None
            return

        self._matrix = self._vectorizer.fit_transform(texts)

    def _load_static_chunks(self) -> List[KnowledgeChunk]:
        static_files: List[Path] = []

        root_readme = self._repo_root / "README.md"
        if root_readme.exists():
            static_files.append(root_readme)

        frontend_readme = self._repo_root / "frontend" / "README.md"
        if frontend_readme.exists():
            static_files.append(frontend_readme)

        docs_dir = self._repo_root / "docs"
        if docs_dir.exists():
            static_files.extend(sorted(docs_dir.glob("*.md")))
            static_files.extend(sorted(docs_dir.glob("*.txt")))

        rag_docs_dir = self._repo_root / "backend" / "rag_sources"
        if rag_docs_dir.exists():
            static_files.extend(
                path
                for path in sorted(rag_docs_dir.rglob("*"))
                if path.is_file() and path.suffix.lower() in {".md", ".txt"}
            )

        chunks: List[KnowledgeChunk] = []
        for path in static_files:
            text_content = self._read_text_file(path)
            if not text_content:
                continue
            rel_path = path.relative_to(self._repo_root).as_posix()
            chunks.append(
                KnowledgeChunk(
                    id=f"static:{rel_path}",
                    source=f"static:{rel_path}",
                    title=path.stem,
                    text=text_content,
                    metadata={"path": rel_path},
                )
            )

        logger.info("Loaded %s static RAG documents.", len(chunks))
        return chunks

    def _build_database_chunks(self, db: Session) -> List[KnowledgeChunk]:
        chunks: List[KnowledgeChunk] = []

        chunks.extend(self._build_overview_chunk(db))
        chunks.extend(self._build_history_chunks(db))
        chunks.extend(self._build_menu_chunks(db))
        chunks.extend(self._build_forecast_chunks(db))
        chunks.extend(self._build_item_mix_chunks(db))
        chunks.extend(self._build_category_chunks(db))

        return chunks

    def _build_overview_chunk(self, db: Session) -> List[KnowledgeChunk]:
        stats = db.query(
            func.sum(models.Order.total_amount).label("total_revenue"),
            func.count(models.Order.id).label("total_orders"),
        ).first()

        total_revenue = float(stats.total_revenue or 0.0)
        total_orders = int(stats.total_orders or 0)
        total_qty = float(db.query(func.sum(models.OrderItem.quantity)).scalar() or 0.0)
        avg_check = round(total_revenue / total_orders, 2) if total_orders else 0.0
        avg_items_per_check = round(total_qty / total_orders, 1) if total_orders else 0.0

        text_content = (
            "Restaurant overview. "
            f"Total revenue: {total_revenue:.2f}. "
            f"Total orders: {total_orders}. "
            f"Average check: {avg_check:.2f}. "
            f"Average items per check: {avg_items_per_check:.1f}."
        )

        return [
            KnowledgeChunk(
                id="db:overview",
                source="database:overview",
                title="Restaurant overview",
                text=text_content,
                metadata={
                    "total_revenue": total_revenue,
                    "total_orders": total_orders,
                    "avg_check": avg_check,
                    "avg_items_per_check": avg_items_per_check,
                },
            )
        ]

    def _build_history_chunks(self, db: Session) -> List[KnowledgeChunk]:
        rows = db.execute(
            text(
                """
                SELECT DATE(timestamp) AS day,
                       SUM(total_amount) AS revenue,
                       COUNT(*) AS orders_count
                FROM orders
                GROUP BY DATE(timestamp)
                ORDER BY day DESC
                LIMIT 30
                """
            )
        ).fetchall()

        chunks: List[KnowledgeChunk] = []
        for row in reversed(rows):
            day = str(row[0])
            revenue = float(row[1] or 0.0)
            orders_count = int(row[2] or 0)
            chunks.append(
                KnowledgeChunk(
                    id=f"db:history:{day}",
                    source="database:history",
                    title=f"Daily sales {day}",
                    text=f"Daily sales for {day}: revenue {revenue:.2f}, orders {orders_count}.",
                    metadata={"day": day, "revenue": revenue, "orders_count": orders_count},
                )
            )
        return chunks

    def _build_menu_chunks(self, db: Session) -> List[KnowledgeChunk]:
        rows = (
            db.query(models.MenuAnalysis)
            .order_by(models.MenuAnalysis.popularity_sales.desc(), models.MenuAnalysis.updated_at.desc())
            .limit(25)
            .all()
        )

        chunks: List[KnowledgeChunk] = []
        for row in rows:
            avg_margin = float(row.avg_margin or 0.0)
            total_revenue = float(row.total_revenue or 0.0)
            chunks.append(
                KnowledgeChunk(
                    id=f"db:menu:{row.item_name}",
                    source="database:menu_analysis",
                    title=f"Menu item {row.item_name}",
                    text=(
                        f"Menu analysis for {row.item_name}. "
                        f"Category: {row.category or 'Other'}. "
                        f"Popularity sales: {int(row.popularity_sales or 0)}. "
                        f"Average margin: {avg_margin:.2f}. "
                        f"Total revenue: {total_revenue:.2f}. "
                        f"Cluster: {row.cluster_label}."
                    ),
                    metadata={
                        "item_name": row.item_name,
                        "category": row.category,
                        "popularity_sales": int(row.popularity_sales or 0),
                        "avg_margin": avg_margin,
                        "total_revenue": total_revenue,
                        "cluster_label": row.cluster_label,
                    },
                )
            )
        return chunks

    def _build_forecast_chunks(self, db: Session) -> List[KnowledgeChunk]:
        rows = db.query(models.DemandForecast).order_by(models.DemandForecast.date.asc()).all()

        chunks: List[KnowledgeChunk] = []
        for row in rows:
            predicted_revenue = float(row.predicted_revenue or 0.0)
            predicted_orders = int(row.predicted_orders or 0)
            lower_bound = float(row.lower_bound_revenue or 0.0)
            upper_bound = float(row.upper_bound_revenue or 0.0)
            date_value = row.date.isoformat()
            chunks.append(
                KnowledgeChunk(
                    id=f"db:forecast:{date_value}",
                    source="database:forecast",
                    title=f"Forecast {date_value}",
                    text=(
                        f"Forecast for {date_value}: predicted revenue {predicted_revenue:.2f}, "
                        f"predicted orders {predicted_orders}, "
                        f"lower bound {lower_bound:.2f}, upper bound {upper_bound:.2f}."
                    ),
                    metadata={
                        "date": date_value,
                        "predicted_revenue": predicted_revenue,
                        "predicted_orders": predicted_orders,
                        "lower_bound_revenue": lower_bound,
                        "upper_bound_revenue": upper_bound,
                    },
                )
            )
        return chunks

    def _build_item_mix_chunks(self, db: Session) -> List[KnowledgeChunk]:
        category_expr = func.coalesce(models.OrderItem.category, "Other")
        rows = (
            db.query(
                models.OrderItem.item_name.label("item_name"),
                category_expr.label("category"),
                func.sum(models.OrderItem.quantity).label("total_quantity"),
                func.sum(models.OrderItem.total_price).label("total_revenue"),
                func.avg(models.OrderItem.price).label("avg_price"),
            )
            .group_by(models.OrderItem.item_name, category_expr)
            .order_by(func.sum(models.OrderItem.total_price).desc())
            .limit(20)
            .all()
        )

        chunks: List[KnowledgeChunk] = []
        for row in rows:
            total_quantity = int(row.total_quantity or 0)
            total_revenue = float(row.total_revenue or 0.0)
            avg_price = float(row.avg_price or 0.0)
            chunks.append(
                KnowledgeChunk(
                    id=f"db:item:{row.item_name}",
                    source="database:item_mix",
                    title=f"Top item {row.item_name}",
                    text=(
                        f"Item {row.item_name} from category {row.category}. "
                        f"Sold quantity {total_quantity}. "
                        f"Revenue {total_revenue:.2f}. "
                        f"Average price {avg_price:.2f}."
                    ),
                    metadata={
                        "item_name": row.item_name,
                        "category": row.category,
                        "total_quantity": total_quantity,
                        "total_revenue": total_revenue,
                        "avg_price": avg_price,
                    },
                )
            )
        return chunks

    def _build_category_chunks(self, db: Session) -> List[KnowledgeChunk]:
        category_expr = func.coalesce(models.OrderItem.category, "Other")
        rows = (
            db.query(
                category_expr.label("category"),
                func.sum(models.OrderItem.quantity).label("total_quantity"),
                func.sum(models.OrderItem.total_price).label("total_revenue"),
            )
            .group_by(category_expr)
            .order_by(func.sum(models.OrderItem.total_price).desc())
            .limit(10)
            .all()
        )

        chunks: List[KnowledgeChunk] = []
        for row in rows:
            total_quantity = int(row.total_quantity or 0)
            total_revenue = float(row.total_revenue or 0.0)
            chunks.append(
                KnowledgeChunk(
                    id=f"db:category:{row.category}",
                    source="database:category_mix",
                    title=f"Category {row.category}",
                    text=(
                        f"Category {row.category}: sold quantity {total_quantity}, "
                        f"revenue {total_revenue:.2f}."
                    ),
                    metadata={
                        "category": row.category,
                        "total_quantity": total_quantity,
                        "total_revenue": total_revenue,
                    },
                )
            )
        return chunks

    def _read_text_file(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            logger.warning("Failed to read RAG source %s: %s", path, exc)
            return ""

        cleaned = " ".join(content.split())
        return self._truncate(cleaned, 6000)

    def _truncate(self, value: str, limit: int) -> str:
        value = value.strip()
        if len(value) <= limit:
            return value
        return f"{value[: limit - 3].rstrip()}..."


rag_engine = RAGEngine()
