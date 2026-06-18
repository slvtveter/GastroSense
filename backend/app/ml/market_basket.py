import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models

# Pairs with fewer co-occurring orders than this are excluded from combo
# leaderboards (API and RAG alike) - with too few checks, lift/confidence is
# just sampling noise. Mirrors MIN_COMBO_SUPPORT in frontend/src/App.tsx.
MIN_COMBO_SUPPORT = 5

# The market basket self-join is the single heaviest per-request computation:
# it loads every order_item and builds a co-occurrence matrix in pandas. The
# dashboard refetches /associations on every page load, so without a cache the
# whole thing recomputes (and re-spikes memory) each time. Cache the result
# keyed by the order_item row count - cheap to check, and it changes whenever
# the data changes (reseed/upload), which is exactly when we must recompute.
_cache: dict = {"row_count": None, "result": None}


def compute_associations(db: Session, top_n_items: int = 15) -> dict:
    """Market Basket Analysis: for the top N items, compute confidence, lift and
    support for every pair. Shared by the /associations API endpoint and the RAG
    engine so the chat assistant reasons about combos using the exact same numbers
    the dashboard shows.

    - confidence (data): P(Item B | Item A) - probability of ordering B given A.
    - lift: P(A and B) / (P(A) * P(B)) - how many times more often A and B are
      bought together than random chance predicts. >1 = real synergy, <1 = bought
      together less than chance would predict (not a real combo).
    - support: raw count of orders containing both A and B.
    """
    row_count = db.query(func.count(models.OrderItem.id)).scalar() or 0
    if _cache["result"] is not None and _cache["row_count"] == row_count:
        return _cache["result"]

    def _finalize(result: dict) -> dict:
        _cache["row_count"] = row_count
        _cache["result"] = result
        return result

    items = db.query(models.OrderItem.order_id, models.OrderItem.item_name).all()
    if not items:
        return _finalize({"index": [], "columns": [], "data": [], "lift": [], "support": [], "total_orders": 0})

    df = pd.DataFrame(items, columns=["order_id", "item_name"])
    total_orders = df["order_id"].nunique()

    item_counts = df["item_name"].value_counts()
    top_items = item_counts.head(top_n_items).index.tolist()
    if len(top_items) < 2:
        return _finalize({"index": [], "columns": [], "data": [], "lift": [], "support": [], "total_orders": total_orders})

    df_unique = df.drop_duplicates()
    df_top = df_unique[df_unique["item_name"].isin(top_items)]

    merged = df_top.merge(df_top, on="order_id")

    support = pd.crosstab(merged["item_name_x"], merged["item_name_y"])
    support = support.reindex(index=top_items, columns=top_items, fill_value=0).astype(float)

    confidence = support.copy()
    for item in top_items:
        if item_counts[item] > 0:
            confidence.loc[item] = confidence.loc[item] / item_counts[item]
    confidence = confidence.round(3)

    lift = support.copy()
    for item_i in top_items:
        for item_j in top_items:
            denom = item_counts[item_i] * item_counts[item_j]
            lift.loc[item_i, item_j] = (support.loc[item_i, item_j] * total_orders / denom) if denom > 0 else 0.0
    lift = lift.round(2)

    return _finalize({
        "index": top_items,
        "columns": top_items,
        "data": confidence.values.tolist(),
        "lift": lift.values.tolist(),
        "support": support.values.tolist(),
        "total_orders": total_orders,
    })
