import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.models import OrderItem
from app.logger import logger, log_execution_time
from typing import List, Dict, Any

def get_food_cost_margin_factor(item_name: str, category: str) -> float:
    """Return a realistic margin factor based on item category and name.
    Drinks typically have very high margins (80-85%).
    Burgers/steaks have moderate margins due to meat costs (50-60%).
    Pizzas/pastas have good margins (65-75%).
    Sides and desserts have high margins (70-80%).
    """
    name_lower = item_name.lower()
    cat_lower = (category or "").lower()
    
    if "drink" in cat_lower or "coke" in name_lower or "beer" in name_lower or "coffee" in name_lower or "tea" in name_lower or "juice" in name_lower:
        return 0.80  # 80% margin
    elif "burger" in cat_lower or "burger" in name_lower or "steak" in name_lower or "beef" in name_lower:
        return 0.55  # 55% margin
    elif "pizza" in cat_lower or "pizza" in name_lower or "pasta" in name_lower:
        return 0.68  # 68% margin
    elif "dessert" in cat_lower or "cake" in name_lower or "ice cream" in name_lower:
        return 0.72  # 72% margin
    elif "fry" in name_lower or "fries" in name_lower or "potato" in name_lower or "sauce" in name_lower:
        return 0.78  # 78% margin
    
    return 0.65  # Default 65% margin

@log_execution_time("Menu Engineering K-Means")
def run_menu_engineering(db: Session) -> List[Dict[str, Any]]:
    """Aggregate per-item metrics in SQL, run K-Means, and assign quadrants."""
    # 1. Aggregate directly in the database with GROUP BY, instead of loading
    # every order_item row (hundreds of thousands for a year of data) into
    # Python and grouping with pandas. The DB returns ~one row per menu item,
    # which is the whole point of the aggregation - materialising all the raw
    # rows first was a major memory spike that could OOM a 512 MB instance.
    category_label = case((OrderItem.category.is_(None), "Other"),
                          (OrderItem.category == "", "Other"),
                          else_=OrderItem.category)
    rows = (
        db.query(
            OrderItem.item_name.label("item_name"),
            category_label.label("category"),
            func.sum(OrderItem.quantity).label("popularity_sales"),
            func.avg(OrderItem.price).label("avg_price"),
            func.sum(OrderItem.total_price).label("total_revenue"),
        )
        .group_by(OrderItem.item_name, category_label)
        .all()
    )
    if not rows:
        logger.warning("No items found in database for Menu Engineering.")
        return []

    logger.info(f"Aggregated {len(rows)} unique menu items in SQL. Running clustering...")

    agg_df = pd.DataFrame(
        [
            {
                "item_name": r.item_name,
                "category": r.category or "Other",
                "popularity_sales": float(r.popularity_sales or 0.0),
                "avg_price": float(r.avg_price or 0.0),
                "total_revenue": float(r.total_revenue or 0.0),
            }
            for r in rows
        ]
    )
    
    # Calculate estimated margin per item
    agg_df["avg_margin_factor"] = agg_df.apply(
        lambda row: get_food_cost_margin_factor(row["item_name"], row["category"]), axis=1
    )
    agg_df["avg_margin"] = agg_df["avg_price"] * agg_df["avg_margin_factor"]
    
    # 3. K-Means Clustering on Popularity & Margin
    features = agg_df[["popularity_sales", "avg_margin"]].copy()
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Run K-Means with 4 clusters
    n_clusters = min(4, len(agg_df))
    if n_clusters < 4:
        logger.info(f"Unique menu items ({len(agg_df)}) < 4. Falling back to median split classification.")
        median_pop = agg_df["popularity_sales"].median()
        median_margin = agg_df["avg_margin"].median()
        
        results = []
        for _, row in agg_df.iterrows():
            pop = row["popularity_sales"]
            marg = row["avg_margin"]
            if pop >= median_pop and marg >= median_margin:
                label = "Stars"
            elif pop >= median_pop and marg < median_margin:
                label = "Workhorses"
            elif pop < median_pop and marg >= median_margin:
                label = "Puzzles"
            else:
                label = "Dogs"
            
            results.append({
                "item_name": row["item_name"],
                "category": row["category"],
                "popularity_sales": int(row["popularity_sales"]),
                "avg_margin": float(row["avg_margin"]),
                "total_revenue": float(row["total_revenue"]),
                "cluster_label": label
            })
        return results
    
    logger.info(f"Running K-Means clustering (K=4) on {len(agg_df)} unique menu items...")
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    agg_df["cluster"] = kmeans.fit_predict(scaled_features)
    
    # 4. Map K-Means clusters to business labels (Stars, Workhorses, Puzzles, Dogs)
    # Calculate cluster centroids
    centroids = kmeans.cluster_centers_
    
    # Map centroids back to the original scale to evaluate business metrics
    centroids_orig = scaler.inverse_transform(centroids)
    
    # Determine the median popularity and margin across all items
    median_pop = agg_df["popularity_sales"].median()
    median_margin = agg_df["avg_margin"].median()
    
    # Calculate scores for each centroid to identify which is which
    # A simple ranking heuristic:
    # Stars: high popularity, high margin
    # Workhorses: high popularity, low margin
    # Puzzles: low popularity, high margin
    # Dogs: low popularity, low margin
    
    cluster_mapping = {}
    remaining_clusters = list(range(4))
    
    # Sort centroids by distance from the ideal point (max popularity, max margin)
    # and worst point (min popularity, min margin)
    pop_vals = centroids_orig[:, 0]
    margin_vals = centroids_orig[:, 1]
    
    # Rank them
    # Star candidate: highest combined rank of popularity and margin
    star_score = (pop_vals - median_pop) / median_pop + (margin_vals - median_margin) / median_margin
    star_cluster = np.argmax(star_score)
    cluster_mapping[star_cluster] = "Stars"
    remaining_clusters.remove(star_cluster)
    
    # Dog candidate: lowest score
    dog_score = (pop_vals - median_pop) / median_pop + (margin_vals - median_margin) / median_margin
    # Exclude the star cluster from calculation
    for c in list(cluster_mapping.keys()):
        dog_score[c] = np.inf  # Make it high so we don't pick it
    dog_cluster = np.argmin(dog_score)
    cluster_mapping[dog_cluster] = "Dogs"
    remaining_clusters.remove(dog_cluster)
    
    # Puzzles: high margin, lower popularity
    # Workhorses: high popularity, lower margin
    c1, c2 = remaining_clusters[0], remaining_clusters[1]
    if pop_vals[c1] > pop_vals[c2]:
        cluster_mapping[c1] = "Workhorses"
        cluster_mapping[c2] = "Puzzles"
    else:
        cluster_mapping[c1] = "Puzzles"
        cluster_mapping[c2] = "Workhorses"
        
    # Apply mapping
    agg_df["cluster_label"] = agg_df["cluster"].map(cluster_mapping)
    
    # Log cluster sizes for observability
    sizes = agg_df["cluster_label"].value_counts().to_dict()
    logger.info(f"K-Means clustering completed. Quadrant distribution: {sizes}")

    
    # Convert to list of dicts for CRUD insertion
    results = []
    for _, row in agg_df.iterrows():
        results.append({
            "item_name": row["item_name"],
            "category": row["category"],
            "popularity_sales": int(row["popularity_sales"]),
            "avg_margin": float(row["avg_margin"]),
            "total_revenue": float(row["total_revenue"]),
            "cluster_label": row["cluster_label"]
        })
    return results
