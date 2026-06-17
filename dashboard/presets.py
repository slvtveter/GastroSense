PRESET_DATASETS = {
    "Бургерная 'True Burgers'": {
        "stats": {
            "total_revenue": 8933480.0,
            "total_orders": 11303,
            "avg_check": 790.36,
            "total_items_sold": 34300,
            "avg_items_per_check": 3.5
        },
        "hist_revenue": [380000, 395000, 310000, 320000, 340000, 420000, 480000,
                         390000, 400000, 325000, 330000, 350000, 435000, 495000,
                         405000, 410000, 335000, 340000, 360000, 450000, 510000],
        "pred_revenue": [415000, 345000, 350000, 370000, 465000, 530000, 425000],
        "pred_orders": [520, 430, 440, 465, 580, 660, 530],
        "menu": [
            {"item_name": "Бургер True", "popularity_sales": 2972, "avg_margin": 247.50, "category": "Burgers", "total_revenue": 1337400.0, "cluster_label": "Stars"},
            {"item_name": "Бургер Чизбургер", "popularity_sales": 3280, "avg_margin": 152.00, "category": "Burgers", "total_revenue": 820000.0, "cluster_label": "Workhorses"},
            {"item_name": "Картофель фри", "popularity_sales": 4410, "avg_margin": 140.40, "category": "Sides", "total_revenue": 882000.0, "cluster_label": "Stars"},
            {"item_name": "Соус сырный", "popularity_sales": 3950, "avg_margin": 39.00, "category": "Sides", "total_revenue": 197500.0, "cluster_label": "Stars"},
            {"item_name": "Кока-кола", "popularity_sales": 3100, "avg_margin": 96.00, "category": "Drinks", "total_revenue": 465000.0, "cluster_label": "Workhorses"},
            {"item_name": "Бургер Шеф-Краб", "popularity_sales": 820, "avg_margin": 306.80, "category": "Burgers", "total_revenue": 492000.0, "cluster_label": "Puzzles"},
            {"item_name": "Пиво крафтовое", "popularity_sales": 1150, "avg_margin": 218.40, "category": "Drinks", "total_revenue": 402500.0, "cluster_label": "Puzzles"},
            {"item_name": "Сырные палочки", "popularity_sales": 1210, "avg_margin": 180.00, "category": "Sides", "total_revenue": 302500.0, "cluster_label": "Puzzles"},
            {"item_name": "Бургер Веган", "popularity_sales": 420, "avg_margin": 147.00, "category": "Burgers", "total_revenue": 105000.0, "cluster_label": "Dogs"},
            {"item_name": "Кольца луковые", "popularity_sales": 580, "avg_margin": 124.80, "category": "Sides", "total_revenue": 116000.0, "cluster_label": "Dogs"}
        ],
        "items_list": ["Бургер True", "Картофель фри", "Соус сырный", "Кока-кола", "Бургер Чизбургер", "Пиво крафтовое", "Бургер Шеф-Краб", "Сырные палочки"],
        "assoc_matrix": [
            [1.00, 0.78, 0.72, 0.50, 0.05, 0.15, 0.02, 0.08], 
            [0.65, 1.00, 0.85, 0.45, 0.08, 0.12, 0.03, 0.10], 
            [0.60, 0.82, 1.00, 0.35, 0.06, 0.10, 0.01, 0.15], 
            [0.45, 0.40, 0.30, 1.00, 0.20, 0.02, 0.05, 0.05], 
            [0.06, 0.70, 0.65, 0.55, 1.00, 0.10, 0.01, 0.05], 
            [0.25, 0.20, 0.15, 0.05, 0.10, 1.00, 0.40, 0.35], 
            [0.10, 0.15, 0.05, 0.12, 0.02, 0.64, 1.00, 0.25], 
            [0.20, 0.25, 0.30, 0.10, 0.08, 0.45, 0.20, 1.00]
        ],
        "assoc_lookup": {
            "Бургер True": [("Картофель фри", 0.78, 1.3), ("Соус сырный", 0.72, 1.4), ("Кока-кола", 0.50, 1.1)],
            "Бургер Чизбургер": [("Картофель фри", 0.70, 1.2), ("Соус сырный", 0.65, 1.3), ("Кока-кола", 0.55, 1.2)],
            "Бургер Шеф-Краб": [("Пиво крафтовое", 0.64, 2.1), ("Сырные палочки", 0.25, 1.2), ("Картофель фри", 0.15, 0.4)],
            "Бургер Веган": [("Кольца луковые", 0.58, 1.8), ("Кока-кола", 0.30, 0.8), ("Картофель фри", 0.25, 0.5)],
            "Картофель фри": [("Соус сырный", 0.85, 1.6), ("Бургер True", 0.65, 1.2), ("Кока-кола", 0.45, 1.0)],
            "Соус сырный": [("Картофель фри", 0.82, 1.5), ("Бургер True", 0.60, 1.1), ("Бургер Чизбургер", 0.52, 1.0)],
            "Кока-кола": [("Бургер True", 0.45, 1.0), ("Картофель фри", 0.40, 0.9), ("Бургер Чизбургер", 0.35, 0.8)],
            "Пиво крафтовое": [("Бургер Шеф-Краб", 0.64, 2.0), ("Сырные палочки", 0.45, 1.4), ("Кольца луковые", 0.30, 0.9)]
        },
        "simulator": {
            "title1": "🥩 Булочки и Котлеты", "mul1": 1.5, "unit1": "шт.",
            "title2": "🍟 Картофель фри (заморозка)", "mul2": 0.35, "unit2": "кг",
            "title3": "🥤 Напитки и пиво", "mul3": 0.9, "unit3": "шт."
        },
        "kpi_deltas": {
            "revenue": {"text": "+14.2% vs прошлый месяц", "positive": True},
            "orders": {"text": "+11.3% к прошлому периоду", "positive": True},
            "avg_check": {"text": "+3.6% к среднему чеку", "positive": True},
            "items_depth": {"text": "+2.4% глубины чека", "positive": True},
        }
    },
    "Кофейня-пекарня 'Coffee & Bakery'": {
        "stats": {
            "total_revenue": 3419500.0,
            "total_orders": 9770,
            "avg_check": 350.00,
            "total_items_sold": 21500,
            "avg_items_per_check": 2.2
        },
        "hist_revenue": [152000, 155000, 160000, 158000, 162000, 145000, 140000,
                         154000, 156000, 162000, 160000, 164000, 147000, 142000,
                         157000, 159000, 165000, 163000, 168000, 150000, 145000],
        "pred_revenue": [161000, 163000, 167000, 165000, 170000, 152000, 146000],
        "pred_orders": [460, 465, 477, 471, 485, 434, 417],
        "menu": [
            {"item_name": "Капуччино 0.3", "popularity_sales": 3400, "avg_margin": 180.00, "category": "Coffee", "total_revenue": 748000.0, "cluster_label": "Stars"},
            {"item_name": "Латте Макиато", "popularity_sales": 2800, "avg_margin": 195.00, "category": "Coffee", "total_revenue": 672000.0, "cluster_label": "Stars"},
            {"item_name": "Эспрессо", "popularity_sales": 1950, "avg_margin": 110.00, "category": "Coffee", "total_revenue": 312000.0, "cluster_label": "Workhorses"},
            {"item_name": "Круассан классик", "popularity_sales": 2500, "avg_margin": 130.00, "category": "Bakery", "total_revenue": 475000.0, "cluster_label": "Stars"},
            {"item_name": "Миндальный круассан", "popularity_sales": 780, "avg_margin": 220.00, "category": "Bakery", "total_revenue": 218400.0, "cluster_label": "Puzzles"},
            {"item_name": "Авокадо тост", "popularity_sales": 450, "avg_margin": 290.00, "category": "Food", "total_revenue": 193500.0, "cluster_label": "Puzzles"},
            {"item_name": "Фильтр-кофе", "popularity_sales": 2100, "avg_margin": 125.00, "category": "Coffee", "total_revenue": 336000.0, "cluster_label": "Workhorses"},
            {"item_name": "Матча латте", "popularity_sales": 620, "avg_margin": 210.00, "category": "Coffee", "total_revenue": 167400.0, "cluster_label": "Puzzles"},
            {"item_name": "Овсяное печенье", "popularity_sales": 480, "avg_margin": 95.00, "category": "Bakery", "total_revenue": 45600.0, "cluster_label": "Dogs"},
            {"item_name": "Веганский брауни", "popularity_sales": 390, "avg_margin": 115.00, "category": "Bakery", "total_revenue": 44850.0, "cluster_label": "Dogs"}
        ],
        "items_list": ["Капуччино 0.3", "Латте Макиато", "Эспрессо", "Круассан классик", "Миндальный круассан", "Авокадо тост", "Фильтр-кофе", "Матча латте"],
        "assoc_matrix": [
            [1.00, 0.30, 0.10, 0.75, 0.40, 0.15, 0.05, 0.20],
            [0.25, 1.00, 0.05, 0.70, 0.45, 0.20, 0.02, 0.15],
            [0.12, 0.08, 1.00, 0.50, 0.25, 0.05, 0.30, 0.05],
            [0.80, 0.75, 0.45, 1.00, 0.10, 0.10, 0.15, 0.10],
            [0.35, 0.40, 0.20, 0.08, 1.00, 0.05, 0.10, 0.25],
            [0.10, 0.15, 0.05, 0.08, 0.04, 1.00, 0.65, 0.05],
            [0.05, 0.02, 0.40, 0.12, 0.08, 0.70, 1.00, 0.05],
            [0.18, 0.12, 0.04, 0.08, 0.22, 0.05, 0.02, 1.00]
        ],
        "assoc_lookup": {
            "Капуччино 0.3": [("Круассан классик", 0.75, 1.4), ("Миндальный круассан", 0.40, 1.2), ("Латте Макиато", 0.30, 0.8)],
            "Латте Макиато": [("Круассан классик", 0.70, 1.3), ("Миндальный круассан", 0.45, 1.3), ("Авокадо тост", 0.20, 0.9)],
            "Эспрессо": [("Круассан классик", 0.50, 1.1), ("Фильтр-кофе", 0.30, 0.9), ("Миндальный круассан", 0.25, 0.8)],
            "Круассан классик": [("Капуччино 0.3", 0.80, 1.5), ("Латте Макиато", 0.75, 1.4), ("Эспрессо", 0.45, 1.1)],
            "Миндальный круассан": [("Латте Макиато", 0.40, 1.3), ("Капуччино 0.3", 0.35, 1.2), ("Матча латте", 0.25, 1.0)],
            "Авокадо тост": [("Фильтр-кофе", 0.65, 1.6), ("Латте Макиато", 0.15, 0.8), ("Капуччино 0.3", 0.10, 0.7)],
            "Фильтр-кофе": [("Авокадо тост", 0.70, 1.7), ("Эспрессо", 0.40, 1.1), ("Круассан классик", 0.12, 0.6)],
            "Матча латте": [("Миндальный круассан", 0.22, 1.1), ("Капуччино 0.3", 0.18, 0.9), ("Латте Макиато", 0.12, 0.8)]
        },
        "simulator": {
            "title1": "☕ Кофейное зерно", "mul1": 0.04, "unit1": "кг",
            "title2": "🥐 Круассаны и выпечка", "mul2": 0.65, "unit2": "шт.",
            "title3": "🥛 Молоко коровье & альт.", "mul3": 0.3, "unit3": "л"
        },
        "kpi_deltas": {
            "revenue": {"text": "+6.8% vs прошлый месяц", "positive": True},
            "orders": {"text": "+4.1% к прошлому периоду", "positive": True},
            "avg_check": {"text": "-1.4% к среднему чеку", "positive": False},
            "items_depth": {"text": "+0.9% глубины чека", "positive": True},
        }
    },
    "Пиццерия 'Pizzeria Italiana'": {
        "stats": {
            "total_revenue": 11210000.0,
            "total_orders": 11800,
            "avg_check": 950.00,
            "total_items_sold": 29500,
            "avg_items_per_check": 2.5
        },
        "hist_revenue": [450000, 480000, 390000, 410000, 430000, 580000, 640000,
                         460000, 490000, 400000, 420000, 440000, 600000, 660000,
                         480000, 510000, 420000, 440000, 460000, 630000, 690000],
        "pred_revenue": [490000, 430000, 450000, 470000, 620000, 710000, 520000],
        "pred_orders": [515, 452, 473, 494, 652, 747, 547],
        "menu": [
            {"item_name": "Пицца Маргарита", "popularity_sales": 3120, "avg_margin": 310.00, "category": "Pizza", "total_revenue": 967200.0, "cluster_label": "Stars"},
            {"item_name": "Пицца Пепперони", "popularity_sales": 3890, "avg_margin": 340.00, "category": "Pizza", "total_revenue": 1322600.0, "cluster_label": "Stars"},
            {"item_name": "Пицца 4 Сыра", "popularity_sales": 1240, "avg_margin": 390.00, "category": "Pizza", "total_revenue": 483600.0, "cluster_label": "Puzzles"},
            {"item_name": "Пицца Карбонара", "popularity_sales": 2450, "avg_margin": 350.00, "category": "Pizza", "total_revenue": 857500.0, "cluster_label": "Stars"},
            {"item_name": "Салат Цезарь", "popularity_sales": 1850, "avg_margin": 210.00, "category": "Salad", "total_revenue": 388500.0, "cluster_label": "Workhorses"},
            {"item_name": "Чесночный хлеб", "popularity_sales": 2200, "avg_margin": 120.00, "category": "Sides", "total_revenue": 264000.0, "cluster_label": "Workhorses"},
            {"item_name": "Тирамису", "popularity_sales": 950, "avg_margin": 260.00, "category": "Dessert", "total_revenue": 247000.0, "cluster_label": "Puzzles"},
            {"item_name": "Кока-Кола", "popularity_sales": 4100, "avg_margin": 110.00, "category": "Drinks", "total_revenue": 451000.0, "cluster_label": "Workhorses"},
            {"item_name": "Пицца Кальцоне", "popularity_sales": 510, "avg_margin": 240.00, "category": "Pizza", "total_revenue": 122400.0, "cluster_label": "Dogs"},
            {"item_name": "Паста Болоньезе", "popularity_sales": 430, "avg_margin": 270.00, "category": "Pasta", "total_revenue": 116100.0, "cluster_label": "Dogs"}
        ],
        "items_list": ["Пицца Маргарита", "Пицца Пепперони", "Пицца 4 Сыра", "Пицца Карбонара", "Салат Цезарь", "Чесночный хлеб", "Тирамису", "Кока-Кола"],
        "assoc_matrix": [
            [1.00, 0.15, 0.05, 0.10, 0.40, 0.55, 0.20, 0.75],
            [0.12, 1.00, 0.08, 0.08, 0.45, 0.50, 0.25, 0.85],
            [0.05, 0.08, 1.00, 0.04, 0.30, 0.35, 0.35, 0.40],
            [0.10, 0.08, 0.04, 1.00, 0.35, 0.45, 0.18, 0.80],
            [0.32, 0.38, 0.22, 0.28, 1.00, 0.15, 0.10, 0.50],
            [0.58, 0.52, 0.32, 0.48, 0.15, 1.00, 0.05, 0.60],
            [0.15, 0.20, 0.25, 0.12, 0.08, 0.05, 1.00, 0.30],
            [0.72, 0.82, 0.38, 0.78, 0.48, 0.58, 0.28, 1.00]
        ],
        "assoc_lookup": {
            "Пицца Маргарита": [("Кока-Кола", 0.75, 1.3), ("Чесночный хлеб", 0.55, 1.2), ("Салат Цезарь", 0.40, 1.0)],
            "Пицца Пепперони": [("Кока-Кола", 0.85, 1.4), ("Чесночный хлеб", 0.50, 1.1), ("Салат Цезарь", 0.45, 1.1)],
            "Пицца 4 Сыра": [("Кока-Кола", 0.40, 1.1), ("Тирамису", 0.35, 1.2), ("Чесночный хлеб", 0.35, 0.9)],
            "Пицца Карбонара": [("Кока-Кола", 0.80, 1.3), ("Чесночный хлеб", 0.45, 1.1), ("Салат Цезарь", 0.35, 0.9)],
            "Салат Цезарь": [("Кока-Кола", 0.50, 1.2), ("Пицца Пепперони", 0.38, 1.1), ("Пицца Карбонара", 0.28, 0.9)],
            "Чесночный хлеб": [("Кока-Кола", 0.60, 1.3), ("Пицца Маргарита", 0.58, 1.2), ("Пицца Пепперони", 0.52, 1.1)],
            "Тирамису": [("Кока-Кола", 0.30, 1.0), ("Пицца 4 Сыра", 0.25, 1.1), ("Пицца Пепперони", 0.20, 0.8)],
            "Кока-Кола": [("Пицца Пепперони", 0.82, 1.4), ("Пицца Карбонара", 0.78, 1.3), ("Пицца Маргарита", 0.72, 1.2)]
        },
        "simulator": {
            "title1": "🍕 Мука и Основы пиццы", "mul1": 1.1, "unit1": "шт.",
            "title2": "🧀 Сыр Моцарелла", "mul2": 0.25, "unit2": "кг",
            "title3": "🥤 Соки и газировки", "mul3": 0.8, "unit3": "шт."
        },
        "kpi_deltas": {
            "revenue": {"text": "+18.7% vs прошлый месяц", "positive": True},
            "orders": {"text": "+15.6% к прошлому периоду", "positive": True},
            "avg_check": {"text": "-2.8% к среднему чеку", "positive": False},
            "items_depth": {"text": "-0.7% глубины чека", "positive": False},
        }
    },
    "Веганское кафе 'Green & Healthy'": {
        "stats": {
            "total_revenue": 4500000.0,
            "total_orders": 6920,
            "avg_check": 650.00,
            "total_items_sold": 14500,
            "avg_items_per_check": 2.1
        },
        "hist_revenue": [200000, 205000, 195000, 190000, 210000, 220000, 230000,
                         202000, 207000, 197000, 192000, 212000, 222000, 232000,
                         205000, 210000, 200000, 195000, 215000, 225000, 235000],
        "pred_revenue": [208000, 203000, 198000, 218000, 228000, 238000, 205000],
        "pred_orders": [320, 312, 304, 335, 350, 366, 315],
        "menu": [
            {"item_name": "Асаи Боул", "popularity_sales": 1820, "avg_margin": 240.00, "category": "Bowls", "total_revenue": 436800.0, "cluster_label": "Stars"},
            {"item_name": "Зеленый Смузи", "popularity_sales": 2400, "avg_margin": 190.00, "category": "Drinks", "total_revenue": 456000.0, "cluster_label": "Stars"},
            {"item_name": "Тофу Скрембл", "popularity_sales": 680, "avg_margin": 280.00, "category": "Breakfast", "total_revenue": 190400.0, "cluster_label": "Puzzles"},
            {"item_name": "Хумус Ролл", "popularity_sales": 1950, "avg_margin": 180.00, "category": "Wraps", "total_revenue": 351000.0, "cluster_label": "Workhorses"},
            {"item_name": "Тарелка Фалафеля", "popularity_sales": 1650, "avg_margin": 220.00, "category": "Plates", "total_revenue": 363000.0, "cluster_label": "Stars"},
            {"item_name": "Чиа Пудинг", "popularity_sales": 920, "avg_margin": 170.00, "category": "Dessert", "total_revenue": 156400.0, "cluster_label": "Puzzles"},
            {"item_name": "Комбуча", "popularity_sales": 1800, "avg_margin": 130.00, "category": "Drinks", "total_revenue": 234000.0, "cluster_label": "Workhorses"},
            {"item_name": "Имбирный Шот", "popularity_sales": 2100, "avg_margin": 90.00, "category": "Drinks", "total_revenue": 189000.0, "cluster_label": "Workhorses"},
            {"item_name": "Сыроедческий торт", "popularity_sales": 580, "avg_margin": 250.00, "category": "Dessert", "total_revenue": 145000.0, "cluster_label": "Puzzles"},
            {"item_name": "Овсянка Б/Г", "popularity_sales": 410, "avg_margin": 110.00, "category": "Breakfast", "total_revenue": 45100.0, "cluster_label": "Dogs"}
        ],
        "items_list": ["Асаи Боул", "Зеленый Смузи", "Тофу Скрембл", "Хумус Ролл", "Тарелка Фалафеля", "Чиа Пудинг", "Комбуча", "Имбирный Шот"],
        "assoc_matrix": [
            [1.00, 0.65, 0.20, 0.35, 0.15, 0.45, 0.10, 0.30],
            [0.60, 1.00, 0.15, 0.40, 0.20, 0.50, 0.30, 0.45],
            [0.18, 0.12, 1.00, 0.10, 0.25, 0.08, 0.05, 0.15],
            [0.30, 0.35, 0.08, 1.00, 0.50, 0.10, 0.55, 0.20],
            [0.12, 0.18, 0.22, 0.45, 1.00, 0.05, 0.40, 0.15],
            [0.40, 0.45, 0.08, 0.08, 0.04, 1.00, 0.15, 0.10],
            [0.08, 0.28, 0.04, 0.50, 0.38, 0.12, 1.00, 0.25],
            [0.28, 0.42, 0.12, 0.18, 0.12, 0.08, 0.22, 1.00]
        ],
        "assoc_lookup": {
            "Асаи Боул": [("Зеленый Смузи", 0.65, 1.3), ("Чиа Пудинг", 0.45, 1.2), ("Хумус Ролл", 0.35, 0.9)],
            "Зеленый Смузи": [("Асаи Боул", 0.60, 1.3), ("Чиа Пудинг", 0.50, 1.2), ("Имбирный Шот", 0.45, 1.1)],
            "Тофу Скрембл": [("Тарелка Фалафеля", 0.25, 1.0), ("Асаи Боул", 0.20, 0.9), ("Имбирный Шот", 0.15, 0.8)],
            "Хумус Ролл": [("Комбуча", 0.55, 1.4), ("Тарелка Фалафеля", 0.50, 1.2), ("Зеленый Смузи", 0.35, 0.9)],
            "Тарелка Фалафеля": [("Хумус Ролл", 0.45, 1.2), ("Комбуча", 0.40, 1.1), ("Зеленый Смузи", 0.18, 0.7)],
            "Чиа Пудинг": [("Зеленый Смузи", 0.45, 1.2), ("Асаи Боул", 0.40, 1.1), ("Комбуча", 0.15, 0.8)],
            "Комбуча": [("Хумус Ролл", 0.50, 1.3), ("Тарелка Фалафеля", 0.38, 1.1), ("Зеленый Смузи", 0.28, 0.8)],
            "Имбирный Шот": [("Зеленый Смузи", 0.42, 1.2), ("Асаи Боул", 0.28, 1.0), ("Комбуча", 0.22, 0.9)]
        },
        "simulator": {
            "title1": "🥑 Свежие авокадо & зелень", "mul1": 0.5, "unit1": "кг",
            "title2": "🍓 Ягоды и семена чиа", "mul2": 0.15, "unit2": "кг",
            "title3": "🌱 Миндальное/овсяное молоко", "mul3": 0.4, "unit3": "л"
        },
        "kpi_deltas": {
            "revenue": {"text": "+5.3% vs прошлый месяц", "positive": True},
            "orders": {"text": "+3.2% к прошлому периоду", "positive": True},
            "avg_check": {"text": "+1.8% к среднему чеку", "positive": True},
            "items_depth": {"text": "+0.5% глубины чека", "positive": True},
        }
    },
    "Крафтовый бар 'Craft Beer Bar'": {
        "stats": {
            "total_revenue": 6792000.0,
            "total_orders": 5660,
            "avg_check": 1200.00,
            "total_items_sold": 17500,
            "avg_items_per_check": 3.1
        },
        "hist_revenue": [100000, 110000, 120000, 280000, 780000, 840000, 250000,
                         105000, 115000, 125000, 290000, 800000, 860000, 260000,
                         110000, 120000, 130000, 300000, 820000, 890000, 270000],
        "pred_revenue": [115000, 125000, 135000, 310000, 850000, 920000, 280000],
        "pred_orders": [96, 104, 112, 258, 708, 766, 233],
        "menu": [
            {"item_name": "IPA Крафт", "popularity_sales": 2650, "avg_margin": 280.00, "category": "Drinks", "total_revenue": 742000.0, "cluster_label": "Stars"},
            {"item_name": "Стаут Шоколадный", "popularity_sales": 840, "avg_margin": 310.00, "category": "Drinks", "total_revenue": 260400.0, "cluster_label": "Puzzles"},
            {"item_name": "APA Pale Ale", "popularity_sales": 2100, "avg_margin": 260.00, "category": "Drinks", "total_revenue": 546000.0, "cluster_label": "Stars"},
            {"item_name": "Лагер Классика", "popularity_sales": 3100, "avg_margin": 180.00, "category": "Drinks", "total_revenue": 558000.0, "cluster_label": "Workhorses"},
            {"item_name": "Сидр Сладкий", "popularity_sales": 1720, "avg_margin": 240.00, "category": "Drinks", "total_revenue": 412800.0, "cluster_label": "Stars"},
            {"item_name": "Начос с сыром", "popularity_sales": 1920, "avg_margin": 190.00, "category": "Snacks", "total_revenue": 364800.0, "cluster_label": "Workhorses"},
            {"item_name": "Гренки чесночные", "popularity_sales": 3400, "avg_margin": 110.00, "category": "Snacks", "total_revenue": 374000.0, "cluster_label": "Workhorses"},
            {"item_name": "Куриные крылышки", "popularity_sales": 920, "avg_margin": 290.00, "category": "Snacks", "total_revenue": 266800.0, "cluster_label": "Puzzles"},
            {"item_name": "French Fries", "popularity_sales": 2400, "avg_margin": 150.00, "category": "Snacks", "total_revenue": 360000.0, "cluster_label": "Workhorses"},
            {"item_name": "Пиво безалкогольное", "popularity_sales": 350, "avg_margin": 160.00, "category": "Drinks", "total_revenue": 56000.0, "cluster_label": "Dogs"}
        ],
        "items_list": ["IPA Крафт", "Стаут Шоколадный", "APA Pale Ale", "Лагер Классика", "Сидр Сладкий", "Начос с сыром", "Гренки чесночные", "Куриные крылышки"],
        "assoc_matrix": [
            [1.00, 0.15, 0.45, 0.10, 0.20, 0.55, 0.70, 0.40],
            [0.12, 1.00, 0.18, 0.08, 0.10, 0.35, 0.42, 0.30],
            [0.42, 0.16, 1.00, 0.12, 0.15, 0.48, 0.65, 0.38],
            [0.10, 0.08, 0.12, 1.00, 0.05, 0.62, 0.75, 0.45],
            [0.18, 0.10, 0.14, 0.04, 1.00, 0.38, 0.42, 0.28],
            [0.52, 0.32, 0.44, 0.58, 0.35, 1.00, 0.25, 0.50],
            [0.68, 0.40, 0.62, 0.72, 0.40, 0.25, 1.00, 0.35],
            [0.38, 0.28, 0.35, 0.42, 0.25, 0.48, 0.32, 1.00]
        ],
        "assoc_lookup": {
            "IPA Крафт": [("Гренки чесночные", 0.70, 1.4), ("Начос с сыром", 0.55, 1.3), ("APA Pale Ale", 0.45, 1.1)],
            "Стаут Шоколадный": [("Гренки чесночные", 0.42, 1.2), ("Начос с сыром", 0.35, 1.1), ("Куриные крылышки", 0.30, 1.0)],
            "APA Pale Ale": [("Гренки чесночные", 0.65, 1.4), ("Начос с сыром", 0.48, 1.2), ("IPA Крафт", 0.42, 1.1)],
            "Лагер Классика": [("Гренки чесночные", 0.75, 1.5), ("Начос с сыром", 0.62, 1.4), ("Куриные крылышки", 0.45, 1.1)],
            "Сидр Сладкий": [("Гренки чесночные", 0.42, 1.1), ("Начос с сыром", 0.38, 1.1), ("Куриные крылышки", 0.28, 0.9)],
            "Начос с сыром": [("Лагер Классика", 0.58, 1.4), ("IPA Крафт", 0.52, 1.3), ("Куриные крылышки", 0.50, 1.2)],
            "Гренки чесночные": [("Лагер Классика", 0.72, 1.5), ("IPA Крафт", 0.68, 1.4), ("APA Pale Ale", 0.62, 1.3)],
            "Куриные крылышки": [("Начос с сыром", 0.48, 1.2), ("Лагер Классика", 0.42, 1.1), ("IPA Крафт", 0.38, 1.0)]
        },
        "simulator": {
            "title1": "🍺 Кеги пивные & сидр", "mul1": 1.2, "unit1": "л",
            "title2": "🥨 Пивные закуски & начос", "mul2": 0.95, "unit2": "шт.",
            "title3": "🍟 Картофель фри (заморозка)", "mul3": 0.4, "unit3": "кг"
        },
        "kpi_deltas": {
            "revenue": {"text": "+22.4% vs прошлый месяц", "positive": True},
            "orders": {"text": "+19.1% к прошлому периоду", "positive": True},
            "avg_check": {"text": "-4.6% к среднему чеку", "positive": False},
            "items_depth": {"text": "+6.2% глубины чека", "positive": True},
        }
    }
}
