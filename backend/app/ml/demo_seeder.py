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

    # Pre-allocate order IDs ourselves instead of flushing once per order to
    # get an autoincrement ID back - that round-trip per row is what made
    # seeding a full year take 30-40+ seconds. Building plain dicts and doing
    # two bulk INSERTs at the end is an order of magnitude faster.
    next_order_id = (db.query(func.max(models.Order.id)).scalar() or 0) + 1
    order_rows: list[dict] = []
    item_rows: list[dict] = []

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

            selected_items = random.choices(MENU, weights=weights, k=num_items)

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

    if order_rows:
        db.execute(insert(models.Order), order_rows)
        db.execute(insert(models.OrderItem), item_rows)
    db.commit()

    orders_created = len(order_rows)
    items_created = len(item_rows)
    logger.info(f"Demo seeding complete. Orders: {orders_created}, Items: {items_created}")

    return {
        "orders_seeded": orders_created,
        "items_seeded": items_created,
        "days_seeded": days
    }

