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
from app.ml.market_basket import MIN_COMBO_SUPPORT, compute_associations


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
        self._repo_root = self._find_repo_root()
        self._static_chunks = self._load_static_chunks()
        self._chunks: List[KnowledgeChunk] = []
        self._vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self._matrix = None
        self._last_refresh_at: datetime | None = None
        self._rebuild_index(self._static_chunks)

    def _find_repo_root(self) -> Path:
        """Walk up from this file looking for README.md or docs/, since the
        on-disk nesting depth differs between local dev (backend/app/ml/...)
        and the Docker image (app/ml/...) — a fixed parents[N] index breaks
        in one of the two environments.
        """
        here = Path(__file__).resolve()
        for candidate in here.parents:
            if (candidate / "README.md").exists() or (candidate / "docs").is_dir():
                return candidate
        # Fall back to the old fixed-depth guess if nothing matched.
        return here.parents[3]

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
            return "No matching context found."

        blocks: List[str] = []
        for idx, item in enumerate(results, start=1):
            blocks.append(
                f"[{idx}] {item['source']} | {item['title']} | relevance={item['score']:.3f}\n"
                # Rollup chunks (e.g. 30 days of history, 25 menu items) are
                # dense lists - 700 chars used to cut them off mid-list, the
                # same root cause as needing a high top_k. Now there are only
                # ~7 chunks total, so a generous per-chunk budget is cheap.
                f"{self._truncate(item['text'], 6000)}"
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

        # Only index docs that are genuinely useful context for an end user
        # asking the in-app assistant about their restaurant. The root
        # README explains what the product is, which is fair game for
        # "what is GastroSense" questions. Deliberately NOT indexing
        # frontend/README.md (generic Vite boilerplate) or docs/*.md
        # (internal outreach/deploy notes for the developer, not the
        # restaurant owner) - those used to get retrieved for unrelated
        # questions and the assistant would confidently answer with
        # sales-pitch copy instead of saying it found nothing relevant.
        root_readme = self._repo_root / "README.md"
        if root_readme.exists():
            static_files.append(root_readme)

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
        chunks.extend(self._build_cross_sales_chunks(db))

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
        """One rollup chunk with daily detail for the last 30 days plus a
        weekly summary covering the full available history. Daily-only
        rollups left questions like "revenue 2 months ago" with literally no
        matching data even when a full year was seeded - the rollup window
        just didn't reach that far back. Weekly granularity is coarser but
        gives every period in the dataset *some* answer instead of none."""
        daily_rows = db.execute(
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
        if not daily_rows:
            return []

        daily_rows = list(reversed(daily_rows))
        daily_lines = [
            f"{row[0]}: revenue {float(row[1] or 0.0):.2f}, orders {int(row[2] or 0)}"
            for row in daily_rows
        ]

        weekly_rows = db.execute(
            text(
                """
                SELECT MIN(DATE(timestamp)) AS week_start,
                       SUM(total_amount) AS revenue,
                       COUNT(*) AS orders_count
                FROM orders
                GROUP BY strftime('%Y-%W', timestamp)
                ORDER BY week_start ASC
                """
            )
        ).fetchall()
        weekly_lines = [
            f"Week of {row[0]}: revenue {float(row[1] or 0.0):.2f}, orders {int(row[2] or 0)}"
            for row in weekly_rows
        ]

        text_content = (
            f"Daily sales for the last {len(daily_rows)} days (oldest to newest):\n"
            + "\n".join(daily_lines)
            + f"\n\nWeekly revenue summary for the full available history ({len(weekly_rows)} weeks, "
            "use this for periods older than 30 days):\n"
            + "\n".join(weekly_lines)
        )

        return [
            KnowledgeChunk(
                id="db:history",
                source="database:history",
                title=f"Daily sales (last {len(daily_rows)} days + {len(weekly_rows)}-week summary)",
                text=text_content,
                metadata={"days": len(daily_rows), "weeks": len(weekly_rows)},
            )
        ]

    def _build_menu_chunks(self, db: Session) -> List[KnowledgeChunk]:
        """One rollup chunk for the whole menu engineering analysis."""
        rows = (
            db.query(models.MenuAnalysis)
            .order_by(models.MenuAnalysis.popularity_sales.desc(), models.MenuAnalysis.updated_at.desc())
            .limit(25)
            .all()
        )
        if not rows:
            return []

        lines = [
            f"{row.item_name} ({row.category or 'Other'}): popularity {int(row.popularity_sales or 0)}, "
            f"avg margin {float(row.avg_margin or 0.0):.2f}, total revenue {float(row.total_revenue or 0.0):.2f}, "
            f"cluster {row.cluster_label}"
            for row in rows
        ]
        text_content = f"Menu engineering analysis (BCG matrix) - top {len(rows)} items:\n" + "\n".join(lines)

        return [
            KnowledgeChunk(
                id="db:menu",
                source="database:menu_analysis",
                title=f"Menu analysis (top {len(rows)} items)",
                text=text_content,
                metadata={"items": len(rows)},
            )
        ]

    def _build_forecast_chunks(self, db: Session) -> List[KnowledgeChunk]:
        """One rollup chunk for the entire forecast horizon, instead of one
        chunk per day - this is what was causing 'summarize the forecast'
        questions to only see 5 of 7 days."""
        rows = db.query(models.DemandForecast).order_by(models.DemandForecast.date.asc()).all()
        if not rows:
            return []

        lines = [
            f"{row.date.isoformat()}: predicted revenue {float(row.predicted_revenue or 0.0):.2f}, "
            f"predicted orders {int(row.predicted_orders or 0)}"
            for row in rows
        ]
        text_content = f"Demand forecast for the next {len(rows)} days:\n" + "\n".join(lines)

        return [
            KnowledgeChunk(
                id="db:forecast",
                source="database:forecast",
                title=f"Demand forecast ({len(rows)} days)",
                text=text_content,
                metadata={"days": len(rows)},
            )
        ]

    def _build_item_mix_chunks(self, db: Session) -> List[KnowledgeChunk]:
        """One rollup chunk for the top items by revenue."""
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
        if not rows:
            return []

        lines = [
            f"{row.item_name} ({row.category}): qty {int(row.total_quantity or 0)}, "
            f"revenue {float(row.total_revenue or 0.0):.2f}, avg price {float(row.avg_price or 0.0):.2f}"
            for row in rows
        ]
        text_content = f"Top {len(rows)} items by revenue:\n" + "\n".join(lines)

        return [
            KnowledgeChunk(
                id="db:item_mix",
                source="database:item_mix",
                title=f"Top items by revenue ({len(rows)})",
                text=text_content,
                metadata={"items": len(rows)},
            )
        ]

    def _build_category_chunks(self, db: Session) -> List[KnowledgeChunk]:
        """One rollup chunk for the category breakdown."""
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
        if not rows:
            return []

        lines = [
            f"{row.category}: qty {int(row.total_quantity or 0)}, revenue {float(row.total_revenue or 0.0):.2f}"
            for row in rows
        ]
        text_content = f"Category breakdown ({len(rows)} categories):\n" + "\n".join(lines)

        return [
            KnowledgeChunk(
                id="db:category_mix",
                source="database:category_mix",
                title="Category breakdown",
                text=text_content,
                metadata={"categories": len(rows)},
            )
        ]

    def _build_cross_sales_chunks(self, db: Session) -> List[KnowledgeChunk]:
        """One chunk per item with its lift/support against every other item, so
        the assistant can explain *why* any specific pair is or isn't a good combo
        using the same statistics the Cross-Sales dashboard tab shows, instead of
        guessing from item names alone (e.g. "why aren't Breakfast Sandwich and
        Mocha a good combo together?"). Per-item chunks (rather than one big
        rollup) guarantee an arbitrary pair survives the per-chunk truncation,
        since a rollup of all ~100 pairs would cut off whichever ones don't make
        the top/bottom slice."""
        result = compute_associations(db)
        index = result["index"]
        if len(index) < 2:
            return []

        lift = result["lift"]
        support = result["support"]
        confidence = result["data"]

        # Kept as a single standalone chunk rather than repeated in every per-item
        # chunk below - repeating words like "promote"/"bundle" 15x previously
        # made unrelated questions (e.g. "which item should I promote?", a menu
        # engineering question) get hijacked by the cross-sales chunks in TF-IDF
        # retrieval, crowding out the actually relevant chunk.
        chunks: List[KnowledgeChunk] = [
            KnowledgeChunk(
                id="db:cross_sales_explainer",
                source="database:cross_sales",
                title="How combo lift scores work",
                text=(
                    "Explanation of lift scores used in cross-sales combo analysis: lift measures how many times "
                    "more often two menu items are bought together than random chance would predict. Lift above "
                    "1x means real synergy between the two items. Lift below 1x means they're bought together "
                    f"less often than chance alone would predict. Pairs with fewer than {MIN_COMBO_SUPPORT} "
                    "co-occurring orders are excluded as statistically unreliable."
                ),
                metadata={},
            )
        ]

        for i, item in enumerate(index):
            lines = []
            for j, other in enumerate(index):
                if i == j or support[i][j] < MIN_COMBO_SUPPORT:
                    continue
                lift_val = lift[i][j]
                lift_pct = round((lift_val - 1) * 100)
                tag = "synergy" if lift_val > 1 else "below random chance"
                lines.append(
                    f"{item} + {other}: lift {lift_val:.2f}x ({'+' if lift_pct >= 0 else ''}{lift_pct}% vs random), "
                    f"{int(support[i][j])} orders together, P({other}|{item})={confidence[i][j]:.2f} ({tag})."
                )
            if not lines:
                continue
            lines.sort(key=lambda line: "below random" in line)

            text_content = f"Combo lift scores for {item}:\n" + "\n".join(lines)
            chunks.append(
                KnowledgeChunk(
                    id=f"db:cross_sales:{item}",
                    source="database:cross_sales",
                    title=f"Cross-sales combos involving {item}",
                    text=text_content,
                    metadata={"item": item, "pairs": len(lines)},
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
