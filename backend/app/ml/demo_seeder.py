import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app import models, crud

MENU_ITEMS = {
    "Burgers": [
        {"name": "Бургер True", "price": 450.0},
        {"name": "Бургер Чизбургер", "price": 380.0},
        {"name": "Бургер Шеф-Краб", "price": 590.0},
        {"name": "Бургер Веган", "price": 420.0}
    ],
    "Sides": [
        {"name": "Картофель фри", "price": 180.0},
        {"name": "Сырные палочки", "price": 240.0},
        {"name": "Кольца луковые", "price": 160.0}
    ],
    "Drinks": [
        {"name": "Кока-кола", "price": 120.0},
        {"name": "Морс домашний", "price": 100.0},
        {"name": "Пиво крафтовое", "price": 280.0}
    ],
    "Sauces": [
        {"name": "Кетчуп", "price": 50.0},
        {"name": "Соус сырный", "price": 50.0},
        {"name": "Соус BBQ", "price": 50.0}
    ]
}

def seed_demo_data(db: Session, days: int = 180) -> dict:
    """Clear existing receipts, generate 180 days of realistic sales data, and save it.
    Returns statistics about seeded data.
    """
    # 1. Clear existing database tables
    db.query(models.OrderItem).delete()
    db.query(models.Order).delete()
    db.query(models.MenuAnalysis).delete()
    db.query(models.DemandForecast).delete()
    db.commit()

    # Setup time horizon
    start_date = datetime.now() - timedelta(days=days)
    
    # Weekly seasonality factors (0: Monday, ..., 6: Sunday)
    weekday_multipliers = [0.75, 0.8, 0.85, 0.95, 1.45, 1.6, 1.25]
    
    orders_count = 0
    items_count = 0
    
    random.seed(42)
    np.random.seed(42)
    
    # Iterate through each day
    for d in range(days):
        current_date = start_date + timedelta(days=d)
        wday = current_date.weekday()
        
        # Calculate daily base order volume
        base_orders = 55
        multiplier = weekday_multipliers[wday]
        
        # Add monthly trend (slight peak in spring/summer)
        month_factor = 1.0 + 0.1 * np.sin((current_date.month - 1) * np.pi / 6)
        
        # Add random noise
        noise = np.random.normal(0, 5)
        
        daily_orders_qty = int(max(10, base_orders * multiplier * month_factor + noise))
        
        for o in range(daily_orders_qty):
            # CRM Order ID
            order_id_crm = f"TB-{current_date.strftime('%Y%m%d')}-{o+1:03d}"
            
            # Timestamp with random hour/minute (mostly lunch 12-14 and dinner 18-22)
            hour_choices = [12, 13, 14, 18, 19, 20, 21, 22]
            rand_hour = random.choice(hour_choices)
            rand_minute = random.randint(0, 59)
            order_time = current_date.replace(hour=rand_hour, minute=rand_minute, second=0)
            
            # Select items based on probabilities and affinities
            order_items = []
            
            # 1. Burger selection (90% probability)
            selected_burger = None
            if random.random() < 0.90:
                selected_burger = random.choice(MENU_ITEMS["Burgers"])
                qty = 1 if random.random() < 0.85 else (2 if random.random() < 0.95 else 3)
                order_items.append({
                    "name": selected_burger["name"],
                    "category": "Burgers",
                    "price": selected_burger["price"],
                    "qty": qty
                })
                
            # 2. Side selection (70% probability, strong affinities)
            if random.random() < 0.70:
                # If they bought a classic burger, they likely get French Fries
                if selected_burger and selected_burger["name"] in ["Бургер True", "Бургер Чизбургер"]:
                    side = MENU_ITEMS["Sides"][0]  # Картофель фри
                elif selected_burger and selected_burger["name"] == "Бургер Веган":
                    side = MENU_ITEMS["Sides"][2]  # Кольца луковые
                else:
                    side = random.choice(MENU_ITEMS["Sides"])
                    
                qty = 1 if random.random() < 0.90 else 2
                order_items.append({
                    "name": side["name"],
                    "category": "Sides",
                    "price": side["price"],
                    "qty": qty
                })
                
            # 3. Drink selection (80% probability)
            if random.random() < 0.80:
                if selected_burger and selected_burger["name"] == "Бургер Шеф-Краб":
                    drink = MENU_ITEMS["Drinks"][2]  # Пиво крафтовое (premium pair)
                elif selected_burger and selected_burger["name"] == "Бургер Веган":
                    drink = MENU_ITEMS["Drinks"][1]  # Морс домашний
                else:
                    drink = random.choice(MENU_ITEMS["Drinks"][:2])  # Cola or Mors
                    
                qty = 1 if random.random() < 0.80 else 2
                order_items.append({
                    "name": drink["name"],
                    "category": "Drinks",
                    "price": drink["price"],
                    "qty": qty
                })
                
            # 4. Sauce selection (65% probability, high correlation with fries)
            if random.random() < 0.65:
                # If they got French Fries, match with Cheese Sauce or Ketchup
                has_fries = any(item["name"] == "Картофель фри" for item in order_items)
                if has_fries:
                    sauce = MENU_ITEMS["Sauces"][1] if random.random() < 0.70 else MENU_ITEMS["Sauces"][0] # Cheese or Ketchup
                else:
                    sauce = random.choice(MENU_ITEMS["Sauces"])
                    
                qty = 1 if random.random() < 0.90 else 2
                order_items.append({
                    "name": sauce["name"],
                    "category": "Sauces",
                    "price": sauce["price"],
                    "qty": qty
                })

            # Calculate total amount
            total_amount = sum(item["price"] * item["qty"] for item in order_items)
            
            # Create Order ORM
            db_order = models.Order(
                order_id_crm=order_id_crm,
                timestamp=order_time,
                total_amount=Decimal(str(round(total_amount, 2))),
                payment_method=random.choice(["Card", "Card", "Card", "Cash"])  # 75% cards
            )
            db.add(db_order)
            db.flush()
            orders_count += 1
            
            # Create OrderItems ORMs
            for item in order_items:
                db_item = models.OrderItem(
                    order_id=db_order.id,
                    item_name=item["name"],
                    category=item["category"],
                    price=Decimal(str(item["price"])),
                    quantity=item["qty"],
                    total_price=Decimal(str(round(item["price"] * item["qty"], 2)))
                )
                db.add(db_item)
                items_count += 1
                
        # Commit in chunks of 10 days to save memory and show progress
        if d % 10 == 0:
            db.commit()
            
    db.commit()
    
    return {
        "success": True,
        "orders_seeded": orders_count,
        "items_seeded": items_count,
        "days_seeded": days
    }
