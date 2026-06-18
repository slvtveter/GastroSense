import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, insert
from sqlalchemy.orm import Session
from app import models, crud
from app.logger import logger

# Preset definitions mapped to restaurant types
PRESETS_CONFIG = {
    "Casual Coffee Shop": {
        "items": [
            ("Cappuccino", "Coffee", 4.50), ("Latte", "Coffee", 4.75), ("Espresso", "Coffee", 3.00),
            ("Americano", "Coffee", 3.50), ("Mocha", "Coffee", 5.00), ("Iced Coffee", "Cold Drinks", 4.00),
            ("Croissant", "Pastry", 3.75), ("Blueberry Muffin", "Pastry", 3.50), ("Avocado Toast", "Food", 8.50),
            ("Breakfast Sandwich", "Food", 9.00), ("Oatmeal", "Food", 6.00), ("Green Tea", "Tea", 3.50)
        ],
        "daily_orders": (80, 200),
        "items_per_order": (1, 3),
        "peak_hours": [8, 9, 10, 11, 14, 15]
    },
    "Fine Dining Restaurant": {
        "items": [
            ("Truffle Risotto", "Mains", 38.00), ("Wagyu Steak", "Mains", 85.00), ("Lobster Bisque", "Starters", 24.00),
            ("Oysters Rockefeller", "Starters", 28.00), ("Duck a l'Orange", "Mains", 45.00), ("Foie Gras", "Starters", 32.00),
            ("Caviar (Half Dozen)", "Starters", 45.00), ("Chocolate Souffle", "Desserts", 16.00), ("Crème Brûlée", "Desserts", 18.00),
            ("Vintage Pinot Noir", "Wine", 120.00), ("Chardonnay", "Wine", 95.00), ("Champagne", "Wine", 150.00)
        ],
        "daily_orders": (15, 40),
        "items_per_order": (2, 6),
        "peak_hours": [18, 19, 20, 21, 22]
    },
    "Fast Food Chain": {
        "items": [
            ("Classic Burger", "Burgers", 6.50), ("Cheeseburger", "Burgers", 7.50), ("Double Bacon Burger", "Burgers", 9.50),
            ("Crispy Chicken Sandwich", "Sandwiches", 7.00), ("Spicy Chicken Nuggets", "Snacks", 5.00), ("French Fries (S)", "Sides", 2.50),
            ("French Fries (L)", "Sides", 4.00), ("Onion Rings", "Sides", 3.50), ("Cola", "Drinks", 2.00),
            ("Milkshake", "Drinks", 4.50), ("Soft Serve Ice Cream", "Desserts", 3.00), ("Apple Pie", "Desserts", 2.50)
        ],
        "daily_orders": (150, 400),
        "items_per_order": (2, 5),
        "peak_hours": [12, 13, 18, 19, 20]
    },
    "Vegan Cafe": {
        "items": [
            ("Quinoa Bowl", "Breakfast", 9.50), ("Acai Smoothie", "Bowls", 11.00), ("Beyond Burger", "Mains", 14.50),
            ("Jackfruit Tacos", "Mains", 13.00), ("Kale Salad", "Salads", 12.00), ("Mushroom Risotto (V)", "Mains", 16.00),
            ("Sweet Potato Fries", "Sides", 6.00), ("Matcha Latte", "Drinks", 5.50), ("Kombucha", "Drinks", 4.50),
            ("Vegan Brownie", "Desserts", 4.50), ("Chia Pudding", "Desserts", 5.00), ("Detox Juice", "Drinks", 7.00)
        ],
        "daily_orders": (40, 100),
        "items_per_order": (1, 4),
        "peak_hours": [11, 12, 13, 14]
    },
    "Food Truck": {
        "items": [
            ("Street Taco (Beef)", "Tacos", 3.50), ("Street Taco (Chicken)", "Tacos", 3.00), ("Street Taco (Pork)", "Tacos", 3.50),
            ("Loaded Nachos", "Snacks", 8.50), ("Burrito Supreme", "Burritos", 10.00), ("Quesadilla", "Burritos", 9.00),
            ("Churros", "Desserts", 4.50), ("Horchata", "Drinks", 3.00), ("Jarritos", "Drinks", 3.00),
            ("Mexican Coke", "Drinks", 3.50), ("Chips & Salsa", "Snacks", 4.00), ("Guacamole Side", "Sides", 2.50)
        ],
        "daily_orders": (60, 150),
        "items_per_order": (1, 3),
        "peak_hours": [11, 12, 13, 21, 22, 23]
    }
}

# Deliberate item affinities so the cross-sales lift analysis shows a realistic
# mix of real synergy (lift > 1) and anti-synergy (lift < 1), instead of every
# pair just reflecting whatever independent random sampling happens to produce
# (which skews uniformly below 1, since picking with replacement makes exact
# duplicate-free pairings slightly less likely than true chance). Multiplier
# adjusts a candidate item's selection weight when its paired item is already
# in the same order; pairs not listed here are left to fall out naturally.
AFFINITY_CONFIG = {
    "Casual Coffee Shop": [
        ("Croissant", "Cappuccino", 6.0),
        ("Blueberry Muffin", "Latte", 5.0),
        ("Avocado Toast", "Green Tea", 4.5),
        ("Breakfast Sandwich", "Mocha", 0.12),
        ("Oatmeal", "Espresso", 0.15),
    ],
    "Fine Dining Restaurant": [
        ("Wagyu Steak", "Vintage Pinot Noir", 6.0),
        ("Oysters Rockefeller", "Champagne", 5.5),
        ("Truffle Risotto", "Chardonnay", 4.5),
        ("Crème Brûlée", "Champagne", 0.12),
        ("Foie Gras", "Chardonnay", 0.15),
    ],
    "Fast Food Chain": [
        ("Classic Burger", "French Fries (L)", 6.0),
        ("Double Bacon Burger", "Milkshake", 5.0),
        ("Crispy Chicken Sandwich", "Cola", 4.5),
        ("Apple Pie", "Onion Rings", 0.12),
        ("Soft Serve Ice Cream", "French Fries (S)", 0.15),
    ],
    "Vegan Cafe": [
        ("Beyond Burger", "Sweet Potato Fries", 6.0),
        ("Quinoa Bowl", "Acai Smoothie", 5.0),
        ("Kale Salad", "Detox Juice", 4.5),
        ("Vegan Brownie", "Kombucha", 0.12),
        ("Mushroom Risotto (V)", "Matcha Latte", 0.15),
    ],
    "Food Truck": [
        ("Street Taco (Beef)", "Horchata", 6.0),
        ("Burrito Supreme", "Mexican Coke", 5.0),
        ("Loaded Nachos", "Guacamole Side", 4.5),
        ("Churros", "Jarritos", 0.12),
        ("Quesadilla", "Chips & Salsa", 0.15),
    ],
}


def clean_database(db: Session):
    """Deletes all existing records to ensure a fresh demo state."""
    db.query(models.OrderItem).delete()
    db.query(models.Order).delete()
    db.query(models.MenuAnalysis).delete()
    db.query(models.DemandForecast).delete()
    db.commit()

def seed_demo_data(
    db: Session,
    days: int = 180,
    preset_name: str = "Casual Coffee Shop",
    end_date: datetime | None = None,
    clean_first: bool = True,
) -> dict:
    """
    Generates realistic synthetic restaurant data based on a preset, covering
    `days` days ending at `end_date` (defaults to now).

    `clean_first=False` appends to the existing data instead of wiping it -
    used to seed a long history in the background after a fast initial seed
    already gave the user something to look at.
    """
    end_date = end_date or datetime.now()
    start_date = end_date - timedelta(days=days)
    logger.info(
        f"Seeding demo data for preset '{preset_name}' from {start_date.date()} to {end_date.date()} "
        f"(clean_first={clean_first})"
    )

    if clean_first:
        clean_database(db)

    # Safely get preset or fallback to Casual Coffee Shop
    config = PRESETS_CONFIG.get(preset_name, PRESETS_CONFIG["Casual Coffee Shop"])
    MENU = config["items"]

    # Weights for menu items to simulate popularity (Pareto principle)
    weights = [random.uniform(0.1, 1.0) for _ in MENU]
    weights.sort(reverse=True)

    # name -> [(partner_index, weight_multiplier), ...], both directions
    item_index_by_name = {name: i for i, (name, _, _) in enumerate(MENU)}
    affinity_map: dict[str, list[tuple[int, float]]] = {}
    for a, b, mult in AFFINITY_CONFIG.get(preset_name, []):
        affinity_map.setdefault(a, []).append((item_index_by_name[b], mult))
        affinity_map.setdefault(b, []).append((item_index_by_name[a], mult))

    # Pre-allocate order IDs ourselves instead of flushing once per order to
    # get an autoincrement ID back - that round-trip per row is what made
    # seeding a full year take 30-40+ seconds. Building plain dicts and doing
    # two bulk INSERTs at the end is an order of magnitude faster.
    next_order_id = (db.query(func.max(models.Order.id)).scalar() or 0) + 1
    order_rows: list[dict] = []
    item_rows: list[dict] = []

    # Flush to the DB every FLUSH_EVERY_DAYS instead of buffering a whole year
    # of rows in Python lists - on a 512 MB host, holding ~450k item dicts in
    # memory at once is enough to OOM the process by itself. Periodic flushing
    # keeps peak memory bounded to roughly one chunk regardless of total days.
    FLUSH_EVERY_DAYS = 30
    days_since_flush = 0
    total_orders = 0
    total_items = 0

    def flush() -> None:
        nonlocal days_since_flush, total_orders, total_items
        if order_rows:
            db.execute(insert(models.Order), order_rows)
            db.execute(insert(models.OrderItem), item_rows)
            db.commit()
            total_orders += len(order_rows)
            total_items += len(item_rows)
            order_rows.clear()
            item_rows.clear()
        days_since_flush = 0

    current_date = start_date
    while current_date <= end_date:
        # Weekend multiplier
        is_weekend = current_date.weekday() >= 5
        multiplier = random.uniform(1.2, 1.8) if is_weekend else random.uniform(0.8, 1.2)

        min_ord, max_ord = config["daily_orders"]
        daily_orders = int(random.randint(min_ord, max_ord) * multiplier)

        for _ in range(daily_orders):
            # Peak hours logic
            hour = random.choice(config["peak_hours"]) if random.random() > 0.3 else random.randint(8, 22)
            minute = random.randint(0, 59)
            order_time = current_date.replace(hour=hour, minute=minute)

            min_items, max_items = config["items_per_order"]
            num_items = random.randint(min_items, max_items)

            # Pick items one at a time (instead of one independent batch draw)
            # so already-chosen items can bias the weight of their affinity
            # partners - this is what makes some pairs lift > 1 and others < 1.
            selected_items = []
            chosen_names: list[str] = []
            for _ in range(num_items):
                adj_weights = weights
                if chosen_names:
                    adj_weights = list(weights)
                    for chosen_name in chosen_names:
                        for partner_idx, mult in affinity_map.get(chosen_name, []):
                            adj_weights[partner_idx] *= mult
                pick = random.choices(MENU, weights=adj_weights, k=1)[0]
                selected_items.append(pick)
                chosen_names.append(pick[0])

            order_id = next_order_id
            next_order_id += 1
            order_total = 0.0

            for item in selected_items:
                name, category, price = item
                actual_price = price * random.choice([1.0, 1.0, 1.0, 0.9, 1.1])
                qty = random.randint(1, 2)

                total_item_price = actual_price * qty
                order_total += total_item_price

                item_rows.append({
                    "order_id": order_id,
                    "item_name": name,
                    "category": category,
                    "price": Decimal(str(round(actual_price, 2))),
                    "quantity": qty,
                    "total_price": Decimal(str(round(total_item_price, 2))),
                })

            order_rows.append({
                "id": order_id,
                "order_id_crm": f"DEMO-{preset_name[:3].upper()}-{order_time.strftime('%Y%m%d')}-{order_id}-{random.randint(100,999)}",
                "timestamp": order_time,
                "total_amount": Decimal(str(round(order_total, 2))),
                "payment_method": random.choice(["Card", "Card", "Card", "Cash"]),
            })

        current_date += timedelta(days=1)
        days_since_flush += 1
        if days_since_flush >= FLUSH_EVERY_DAYS:
            flush()

    # Flush whatever is left in the final partial chunk.
    flush()

    logger.info(f"Demo seeding complete. Orders: {total_orders}, Items: {total_items}")

    return {
        "orders_seeded": total_orders,
        "items_seeded": total_items,
        "days_seeded": days
    }

