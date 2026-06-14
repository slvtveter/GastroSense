import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from app.models import OrderItem
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

def run_menu_engineering(db: Session) -> List[Dict[str, Any]]:
    """Query order items, aggregate metrics, run K-Means, and assign quadrants."""
    # 1. Fetch order items from database
    items = db.query(OrderItem).all()
    if not items:
        return []
    
    # Convert to DataFrame
    data = []
    for item in items:
        data.append({
            "item_name": item.item_name,
            "category": item.category or "Other",
            "price": float(item.price),
            "quantity": item.quantity,
            "total_price": float(item.total_price)
        })
    df = pd.DataFrame(data)
    
    # 2. Aggregate per item
    agg_df = df.groupby(["item_name", "category"]).agg(
        popularity_sales=("quantity", "sum"),
        avg_price=("price", "mean"),
        total_revenue=("total_price", "sum")
    ).reset_index()
    
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
        # If menu is too small, fallback to simple median splitting without K-Means
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
