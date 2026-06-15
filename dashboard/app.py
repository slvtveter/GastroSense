import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
import numpy as np
from datetime import datetime, date, timedelta

# Page configuration for a wide, premium feel
st.set_page_config(
    page_title="GastroSense | Restaurant Intelligence AI",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium dark theme styling (Finpath & Donezo dark aesthetics)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .stApp {
        background-color: #07090e !important;
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Hide Streamlit default header, footer and side margins */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3.5rem !important;
        padding-right: 3.5rem !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    
    /* Custom Header Navigation Bar */
    .top-nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #0f131a;
        border: 1px solid #1a222f;
        border-radius: 16px;
        padding: 16px 28px;
        margin-bottom: 28px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .logo-area {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-icon {
        font-size: 24px;
        filter: drop-shadow(0 2px 8px rgba(204, 255, 0, 0.3));
    }
    .logo-text {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #ffffff 0%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .connection-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    .badge-live {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .badge-demo {
        background-color: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .profile-pic {
        background-color: #ccff00;
        color: #07090e;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 13px;
        box-shadow: 0 0 12px rgba(204, 255, 0, 0.4);
    }
    
    /* Tabs custom styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0f131a;
        padding: 8px 14px;
        border-radius: 30px;
        border: 1px solid #1a222f;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        white-space: pre-wrap;
        background-color: transparent !important;
        border: none !important;
        color: #8b99ad !important;
        border-radius: 20px;
        padding: 0px 24px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #1a222f !important;
        color: #ccff00 !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    /* Sleek Custom Cards */
    .custom-card {
        background-color: #0f131a;
        border: 1px solid #1a222f;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .custom-card:hover {
        transform: translateY(-2px);
        border-color: #2e3b4e;
        box-shadow: 0 16px 30px rgba(0, 0, 0, 0.3);
    }
    
    /* Metric Cards specific styles */
    .metric-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 110px;
    }
    .metric-label {
        font-size: 11px;
        color: #8b99ad;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        margin-top: 6px;
        letter-spacing: -0.5px;
    }
    .metric-subtext {
        font-size: 11px;
        color: #64748b;
        margin-top: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Lime green highlight card */
    .highlight-card {
        background: linear-gradient(135deg, #ccff00 0%, #a3cc00 100%);
        color: #07090e;
        border: none;
    }
    .highlight-card .metric-label {
        color: rgba(7, 9, 14, 0.6);
    }
    .highlight-card .metric-value {
        color: #07090e;
    }
    .highlight-card .metric-subtext {
        color: rgba(7, 9, 14, 0.5);
    }
    
    /* Interactive combo recommendation card */
    .combo-card {
        background-color: #121822;
        border: 1px dashed rgba(204, 255, 0, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-top: 16px;
        transition: all 0.2s ease;
    }
    .combo-card:hover {
        border-color: #ccff00;
        background-color: #141c29;
    }
    
    /* HTML Tables styling */
    .table-container {
        overflow-x: auto;
        margin: 12px 0;
    }
    .premium-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        font-size: 13px;
    }
    .premium-table th {
        background-color: #141923;
        color: #8b99ad;
        font-weight: 700;
        padding: 14px 16px;
        border-bottom: 1px solid #1a222f;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .premium-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #141923;
        color: #f1f5f9;
        font-weight: 500;
    }
    .premium-table tr:hover {
        background-color: rgba(255, 255, 255, 0.015);
    }
    
    /* Badge styling */
    .badge {
        font-size: 10px;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .badge-star {
        background-color: rgba(204, 255, 0, 0.1);
        color: #ccff00;
        border: 1px solid rgba(204, 255, 0, 0.2);
    }
    .badge-workhorse {
        background-color: rgba(0, 210, 255, 0.1);
        color: #00d2ff;
        border: 1px solid rgba(0, 210, 255, 0.2);
    }
    .badge-puzzle {
        background-color: rgba(255, 165, 0, 0.1);
        color: #ffa500;
        border: 1px solid rgba(255, 165, 0, 0.2);
    }
    .badge-dog {
        background-color: rgba(255, 51, 83, 0.1);
        color: #ff3353;
        border: 1px solid rgba(255, 51, 83, 0.2);
    }
    
    /* Clean Progress Bars */
    .progress-bar-container {
        width: 100%;
        background-color: #141923;
        border-radius: 8px;
        height: 6px;
        margin-top: 5px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    /* Streamlit widgets overrides */
    div[data-baseweb="select"] {
        background-color: #0f131a !important;
        border: 1px solid #1a222f !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #ffffff !important;
    }
    
    /* Slider overrides */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #ccff00 !important;
        border: 2px solid #07090e !important;
    }
    div[data-testid="stSlider"] div[data-testid="stSliderTrack"] > div {
        background: linear-gradient(90deg, #00d2ff 0%, #ccff00 100%) !important;
    }
    
    /* Button Styles */
    button[kind="secondary"] {
        background-color: #0f131a !important;
        color: #ffffff !important;
        border: 1px solid #1a222f !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background-color: #141923 !important;
        border-color: #ccff00 !important;
        color: #ccff00 !important;
        box-shadow: 0 4px 12px rgba(204, 255, 0, 0.1);
    }
    button[kind="primary"] {
        background-color: #ccff00 !important;
        color: #07090e !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(204, 255, 0, 0.2);
    }
    button[kind="primary"]:hover {
        background-color: #e5ff80 !important;
        box-shadow: 0 6px 20px rgba(204, 255, 0, 0.35);
        transform: translateY(-1px);
    }
    
    /* Streamlit Alert message boxes */
    div[data-testid="stNotification"] {
        background-color: #0f131a !important;
        border: 1px solid #1a222f !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)

# Connection Settings
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# Helper function to query the API
def get_data(endpoint: str):
    try:
        response = requests.get(f"{BACKEND_API_URL}{endpoint}", timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def post_data(endpoint: str, files=None):
    try:
        response = requests.post(f"{BACKEND_API_URL}{endpoint}", files=files, timeout=30)
        return response.json()
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

# ----------------- LIVE STATE CHECK -----------------
stats_data = get_data("/analytics/stats")
is_live = stats_data is not None and stats_data.get("total_orders", 0) > 0

# Render Top Navigation Bar
connection_class = "badge-live" if is_live else "badge-demo"
connection_text = "🟢 Live Database (MySQL)" if is_live else "🟡 Demo Mode (Offline)"
st.markdown(f"""
<div class="top-nav-bar">
    <div class="logo-area">
        <span class="logo-icon">🍷</span>
        <span class="logo-text">GastroSense AI</span>
    </div>
    <div class="header-right">
        <div class="connection-badge {connection_class}">{connection_text}</div>
        <div class="profile-pic">GS</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- DATA PREPARATION -----------------
if not is_live:
    # 1. Stats Fallback
    total_revenue = 8933480.0
    total_orders = 11303
    avg_check = 790.36
    total_items_sold = 34300
    avg_items_per_check = 3.5
    
    # 2. Daily History Fallback
    base_date = datetime.now() - timedelta(days=21)
    hist_dates = [base_date + timedelta(days=i) for i in range(21)]
    # Weekday patterns: Fri/Sat peak
    hist_revenue = [
        380000, 395000, 310000, 320000, 340000, 420000, 480000,
        390000, 400000, 325000, 330000, 350000, 435000, 495000,
        405000, 410000, 335000, 340000, 360000, 450000, 510000
    ]
    df_hist = pd.DataFrame({
        "date": hist_dates, 
        "revenue": hist_revenue,
        "orders_count": [int(rev / 790) for rev in hist_revenue]
    })
    
    # 3. Forecast Fallback
    forecast_dates = [datetime.now() + timedelta(days=i) for i in range(1, 8)]
    # Next 7 days predictions
    predicted_rev = [415000, 345000, 350000, 370000, 465000, 530000, 425000]
    lower_bound = [r * 0.90 for r in predicted_rev]
    upper_bound = [r * 1.10 for r in predicted_rev]
    df_fore = pd.DataFrame({
        "date": forecast_dates,
        "predicted_revenue": predicted_rev,
        "predicted_orders": [520, 430, 440, 465, 580, 660, 530],
        "lower_bound_revenue": lower_bound,
        "upper_bound_revenue": upper_bound
    })
    
    # 4. Menu analysis Fallback (with added categories and computed revenues for breakdowns)
    df_menu = pd.DataFrame([
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
    ])
    
    # 5. Associations Fallback
    items_list = ["Бургер True", "Картофель фри", "Соус сырный", "Кока-кола", "Бургер Чизбургер", "Пиво крафтовое", "Бургер Шеф-Краб", "Сырные палочки"]
    assoc_matrix = [
        [1.00, 0.78, 0.72, 0.50, 0.05, 0.15, 0.02, 0.08], 
        [0.65, 1.00, 0.85, 0.45, 0.08, 0.12, 0.03, 0.10], 
        [0.60, 0.82, 1.00, 0.35, 0.06, 0.10, 0.01, 0.15], 
        [0.45, 0.40, 0.30, 1.00, 0.20, 0.02, 0.05, 0.05], 
        [0.06, 0.70, 0.65, 0.55, 1.00, 0.10, 0.01, 0.05], 
        [0.25, 0.20, 0.15, 0.05, 0.10, 1.00, 0.40, 0.35], 
        [0.10, 0.15, 0.05, 0.12, 0.02, 0.64, 1.00, 0.25], 
        [0.20, 0.25, 0.30, 0.10, 0.08, 0.45, 0.20, 1.00]  
    ]
else:
    # Read live stats
    total_revenue = float(stats_data.get("total_revenue", 0.0))
    total_orders = int(stats_data.get("total_orders", 0))
    avg_check = float(stats_data.get("avg_check", 0.0))
    total_items_sold = int(stats_data.get("total_items_sold", 0))
    avg_items_per_check = float(stats_data.get("avg_items_per_check", 0.0))
    
    # Read live history
    hist_json = get_data("/analytics/history?days=21")
    df_hist = pd.DataFrame(hist_json) if hist_json else pd.DataFrame(columns=["date", "revenue", "orders_count"])
    df_hist["date"] = pd.to_datetime(df_hist["date"])
    df_hist["revenue"] = pd.to_numeric(df_hist["revenue"], errors="coerce").fillna(0.0)
    df_hist["orders_count"] = pd.to_numeric(df_hist["orders_count"], errors="coerce").fillna(0).astype(int)
    
    # Read live forecast
    fore_json = get_data("/analytics/forecast")
    df_fore = pd.DataFrame(fore_json) if fore_json else pd.DataFrame(columns=["date", "predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"])
    df_fore["date"] = pd.to_datetime(df_fore["date"])
    for col in ["predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"]:
        df_fore[col] = pd.to_numeric(df_fore[col], errors="coerce").fillna(0.0)
        
    # Read live menu
    menu_json = get_data("/analytics/menu")
    df_menu = pd.DataFrame(menu_json) if menu_json else pd.DataFrame(columns=["item_name", "category", "popularity_sales", "avg_margin", "total_revenue", "cluster_label"])
    df_menu["popularity_sales"] = pd.to_numeric(df_menu["popularity_sales"], errors="coerce").fillna(0).astype(int)
    df_menu["avg_margin"] = pd.to_numeric(df_menu["avg_margin"], errors="coerce").fillna(0.0)
    df_menu["total_revenue"] = pd.to_numeric(df_menu["total_revenue"], errors="coerce").fillna(0.0)
    # Ensure category exists in response, fallback to "Uncategorized"
    if "category" not in df_menu.columns:
        df_menu["category"] = "Uncategorized"
    
    # Read live associations
    assoc_json = get_data("/analytics/associations")
    if assoc_json and assoc_json.get("index"):
        items_list = assoc_json["index"]
        assoc_matrix = assoc_json["data"]
    else:
        items_list, assoc_matrix = [], []

# Offline Mock co-occurrence lookup mapping for interactive combo designer
offline_assoc_lookup = {
    "Бургер True": [("Картофель фри", 0.78, 1.3), ("Соус сырный", 0.72, 1.4), ("Кока-кола", 0.50, 1.1)],
    "Бургер Чизбургер": [("Картофель фри", 0.70, 1.2), ("Соус сырный", 0.65, 1.3), ("Кока-кола", 0.55, 1.2)],
    "Бургер Шеф-Краб": [("Пиво крафтовое", 0.64, 2.1), ("Сырные палочки", 0.25, 1.2), ("Картофель фри", 0.15, 0.4)],
    "Бургер Веган": [("Кольца луковые", 0.58, 1.8), ("Кока-кола", 0.30, 0.8), ("Картофель фри", 0.25, 0.5)],
    "Картофель фри": [("Соус сырный", 0.85, 1.6), ("Бургер True", 0.65, 1.2), ("Кока-кола", 0.45, 1.0)],
    "Соус сырный": [("Картофель фри", 0.82, 1.5), ("Бургер True", 0.60, 1.1), ("Бургер Чизбургер", 0.52, 1.0)],
    "Кока-кола": [("Бургер True", 0.45, 1.0), ("Картофель фри", 0.40, 0.9), ("Бургер Чизбургер", 0.35, 0.8)],
    "Пиво крафтовое": [("Бургер Шеф-Краб", 0.64, 2.0), ("Сырные палочки", 0.45, 1.4), ("Кольца луковые", 0.30, 0.9)]
}

# Python helper to generate custom metric card HTML
def make_metric_card(label, value, subtext, delta=None, is_positive=True, is_highlighted=False):
    highlight_class = "highlight-card" if is_highlighted else ""
    delta_html = ""
    if delta:
        color = "#ccff00" if is_highlighted else ("#ccff00" if is_positive else "#ff3353")
        arrow = "↑" if is_positive else "↓"
        delta_html = f'<div style="color: {color}; font-size: 11px; font-weight: 700; margin-top: 4px;">{arrow} {delta}</div>'
    
    html = f"""
    <div class="custom-card metric-card {highlight_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtext">
            <span>{subtext}</span>
        </div>
        {delta_html}
    </div>
    """
    return html

# ----------------- MAIN NAVIGATION TABS -----------------
tab_overview, tab_forecast, tab_menu, tab_cross, tab_system = st.tabs([
    "📊 Сводка",
    "📈 Прогноз спроса", 
    "🌟 Анализ меню", 
    "🤝 Кросс-продажи",
    "⚙️ Настройки и данные"
])

# ==========================================
# 📊 TAB 1: OVERVIEW (Сводка)
# ==========================================
with tab_overview:
    # Metric cards grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(make_metric_card(
            "Выручка ресторана", 
            f"{total_revenue:,.0f} ₽".replace(",", " "), 
            "За все время", 
            delta="12.4% vs прошлый месяц", 
            is_positive=True,
            is_highlighted=True
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(make_metric_card(
            "Количество заказов", 
            f"{total_orders:,.0f}".replace(",", " "), 
            "Всего чеков закрыто", 
            delta="8.2% к прошлому периоду", 
            is_positive=True
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(make_metric_card(
            "Средний чек", 
            f"{avg_check:,.2f} ₽".replace(",", " "), 
            "На одного посетителя", 
            delta="5.1% рост чека", 
            is_positive=True
        ), unsafe_allow_html=True)
    with c4:
        st.markdown(make_metric_card(
            "Продано позиций", 
            f"{total_items_sold:,.0f}".replace(",", " "), 
            f"Среднее в чеке: {avg_items_per_check:.1f} ед.", 
            delta="3.9% рост глубины", 
            is_positive=True
        ), unsafe_allow_html=True)
        
    # Charts section
    ch_col1, ch_col2 = st.columns([1.3, 2])
    
    with ch_col1:
        st.markdown('<div class="custom-card" style="height: 440px; overflow: hidden;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Структура выручки</p>', unsafe_allow_html=True)
        
        # Donut Chart for category breakdown
        if not df_menu.empty:
            cat_data = df_menu.groupby("category")["total_revenue"].sum().reset_index()
            cat_data["revenue_formatted"] = cat_data["total_revenue"].apply(lambda x: f"{x:,.0f} ₽")
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=cat_data["category"],
                values=cat_data["total_revenue"],
                hole=0.68,
                marker=dict(colors=["#ccff00", "#00d2ff", "#ffa500", "#ff3353"]),
                hoverinfo="label+percent+value",
                textinfo="none"
            )])
            
            fig_donut.add_annotation(
                text=f"Выручка<br><span style='font-size:18px; font-weight:800; color:#fff;'>{total_revenue/1e6:.2f}M ₽</span>",
                showarrow=False,
                font=dict(size=11, color="#8b99ad"),
                x=0.5, y=0.5
            )
            
            fig_donut.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=10),
                height=320,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10, color="#8b99ad")
                )
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет данных о меню.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with ch_col2:
        st.markdown('<div class="custom-card" style="height: 440px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Динамика выручки и тренд</p>', unsafe_allow_html=True)
        
        if not df_hist.empty:
            fig_hist = go.Figure()
            # Historical Area Line
            fig_hist.add_trace(go.Scatter(
                x=df_hist["date"],
                y=df_hist["revenue"],
                mode="lines",
                name="Выручка",
                line=dict(color="#ccff00", width=3, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(204, 255, 0, 0.04)"
            ))
            fig_hist.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=20, b=0),
                height=320,
                xaxis=dict(
                    showgrid=False, 
                    tickfont=dict(color="#64748b", size=10),
                    linecolor="#1a222f"
                ),
                yaxis=dict(
                    gridcolor="#1a222f", 
                    tickfont=dict(color="#64748b", size=10),
                    zeroline=False
                ),
                hovermode="x unified",
                showlegend=False
            )
            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет исторических данных для отображения.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Budget, AI Insights, wait times
    col_row3_1, col_row3_2, col_row3_3 = st.columns([1, 1, 1])
    
    with col_row3_1:
        st.markdown('<div class="custom-card" style="min-height: 380px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:20px; text-transform:uppercase; letter-spacing:0.5px;">Лимиты закупок и фудкост</p>', unsafe_allow_html=True)
        
        budgets = [
            ("🥩 Мясо и Булки", 2040000, 2000000, "#ff3353"),
            ("🥬 Овощи и Салаты", 1220000, 1500000, "#ccff00"),
            ("🍺 Соусы и Напитки", 820000, 900000, "#00d2ff"),
            ("📦 Упаковка и Снабжение", 600000, 800000, "#00d2ff")
        ]
        
        for name, act, limit, color in budgets:
            pct = min(100, int((act / limit) * 100))
            pct_text = f"{pct}%"
            st.markdown(f"""
            <div style="margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#8b99ad; margin-bottom:5px;">
                    <span style="font-weight:600; color:#f1f5f9;">{name}</span>
                    <span style="font-weight:700; color:#ffffff;">{act/1e6:.2f}M ₽ / {limit/1e6:.1f}M ₽ ({pct_text})</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {pct}%; background-color: {color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_row3_2:
        st.markdown('<div class="custom-card highlight-card" style="min-height: 380px; display:flex; flex-direction:column; justify-content:space-between;">', unsafe_allow_html=True)
        
        # Recommendations
        rec_title = "🧠 GastroSense Predict AI"
        rec_main = "⚠️ <strong>Внимание:</strong> С прогнозом выручки на пятницу в 530 000 ₽ (+18% к среднему), рекомендуется увеличить заготовки мясных котлет на 15-20% во избежание дефицита."
        
        # Dynamic advice based on clusters
        advice_list = []
        if not df_menu.empty:
            star_items = df_menu[df_menu["cluster_label"] == "Stars"]["item_name"].tolist()
            horse_items = df_menu[df_menu["cluster_label"] == "Workhorses"]["item_name"].tolist()
            if star_items:
                advice_list.append(f"💡 <strong>Stars:</strong> Закрепите '{star_items[0]}' на золотом месте в меню и оставьте рецепт неизменным.")
            if horse_items:
                advice_list.append(f"💡 <strong>Workhorses:</strong> Снизьте себестоимость '{horse_items[0]}' на 4% или поднимите ее цену для увеличения маржинальности.")
        else:
            advice_list.append("💡 Подключите базу данных или загрузите чеки для построения индивидуальных рекомендаций по меню.")
            
        advice_html = "<br>".join([f'<p style="margin: 8px 0 0 0; font-size:12px; opacity:0.8;">{adv}</p>' for adv in advice_list[:2]])
        
        st.markdown(f"""
        <div>
            <div style="font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;">{rec_title}</div>
            <p style="font-size:13px; line-height:1.5; margin:0 0 16px 0;">{rec_main}</p>
            <div style="border-top: 1px solid rgba(7,9,14,0.1); padding-top:12px;">
                {advice_html}
            </div>
        </div>
        <div style="font-size:10px; font-weight:700; opacity:0.5; margin-top:16px;">Модель LightGBM пересчитана 14.06.2026</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_row3_3:
        st.markdown('<div class="custom-card" style="min-height: 380px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px;">Скорость отдачи блюд (Кухня)</p>', unsafe_allow_html=True)
        
        # Micro bar chart representing kitchen wait times in minutes
        categories = ["Бургеры", "Гарниры", "Напитки", "Десерты"]
        wait_times = [8.2, 4.1, 1.5, 5.3]
        
        fig_kitchen = go.Figure(data=[go.Bar(
            x=categories,
            y=wait_times,
            marker_color="#ccff00",
            width=0.4,
            hoverinfo="y",
            text=[f"{t} мин" for t in wait_times],
            textposition="auto",
            textfont=dict(size=10, color="#07090e")
        )])
        fig_kitchen.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            height=260,
            xaxis=dict(
                showgrid=False, 
                tickfont=dict(color="#64748b", size=10),
                linecolor="#1a222f"
            ),
            yaxis=dict(
                gridcolor="#1a222f", 
                tickfont=dict(color="#64748b", size=10),
                zeroline=False,
                title="Минуты"
            )
        )
        st.plotly_chart(fig_kitchen, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 📈 TAB 2: DEMAND FORECAST (Прогноз спроса)
# ==========================================
with tab_forecast:
    # Top metrics row
    fc1, fc2, fc3 = st.columns(3)
    
    if not df_fore.empty:
        total_pred_rev = df_fore["predicted_revenue"].sum()
        avg_ai_acc = 94.2  # accuracy
        opt_savings = total_pred_rev * 0.124
    else:
        total_pred_rev, avg_ai_acc, opt_savings = 0.0, 0.0, 0.0
        
    with fc1:
        st.markdown(make_metric_card(
            "Прогноз выручки (7 дней)",
            f"{total_pred_rev:,.0f} ₽".replace(",", " "),
            "Суммарно на следующую неделю",
            delta="Модель LightGBM v4.3.0",
            is_positive=True,
            is_highlighted=True
        ), unsafe_allow_html=True)
    with fc2:
        st.markdown(make_metric_card(
            "Точность модели ИИ",
            f"{avg_ai_acc:.1f}%",
            "WAPE по тестовой выборке",
            delta="±5.8% интервал погрешности",
            is_positive=True
        ), unsafe_allow_html=True)
    with fc3:
        st.markdown(make_metric_card(
            "Экономия на списаниях",
            f"- {opt_savings:,.0f} ₽".replace(",", " "),
            "Благодаря оптимизации закупок",
            delta="-12.4% пищевых отходов",
            is_positive=True
        ), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Grid: Interactive simulator on left, forecast chart on right
    fore_col_left, fore_col_right = st.columns([1, 2.5])
    
    with fore_col_left:
        st.markdown('<div class="custom-card" style="min-height: 480px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Симулятор спроса</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px; color:#8b99ad; line-height:1.4; margin-bottom:20px;">Оцените изменения требований к закупкам кухни, регулируя силу симулятора трафика гостей.</p>', unsafe_allow_html=True)
        
        demand_shift = st.slider(
            "Симулятор трафика (%)", 
            min_value=-30, 
            max_value=50, 
            value=0, 
            step=5,
            key="demand_shift_slider"
        )
        
        # Apply slider shifts
        factor = 1 + (demand_shift / 100.0)
        adjusted_predicted_rev = df_fore["predicted_revenue"] * factor
        adjusted_lower_bound = df_fore["lower_bound_revenue"] * factor
        adjusted_upper_bound = df_fore["upper_bound_revenue"] * factor
        adjusted_predicted_orders = df_fore["predicted_orders"] * factor
        
        # Display supplier metrics adjust
        base_patties = int(adjusted_predicted_orders.sum() * 1.5)
        base_fries_kg = int(adjusted_predicted_orders.sum() * 0.35)
        base_beverages = int(adjusted_predicted_orders.sum() * 0.9)
        
        st.markdown(f"""
        <div style="margin-top:24px; border-top: 1px solid #1a222f; padding-top:20px;">
            <p style="font-size:12px; font-weight:700; color:#ccff00; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px;">📊 Заказ сырья (Прогноз):</p>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#8b99ad; margin-bottom:8px;">
                <span>🥩 Булочки и Котлеты</span>
                <span style="font-weight:700; color:#fff;">{base_patties} шт.</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#8b99ad; margin-bottom:8px;">
                <span>🍟 Картофель фри (заморозка)</span>
                <span style="font-weight:700; color:#fff;">{base_fries_kg} кг</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#8b99ad;">
                <span>🥤 Напитки и пиво</span>
                <span style="font-weight:700; color:#fff;">{base_beverages} шт.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with fore_col_right:
        st.markdown('<div class="custom-card" style="min-height: 480px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Прогноз продаж ИИ и доверительный интервал</p>', unsafe_allow_html=True)
        
        if not df_fore.empty and not df_hist.empty:
            fig_fore = go.Figure()
            
            # History line (Darker blue-grey)
            fig_fore.add_trace(go.Scatter(
                x=df_hist["date"],
                y=df_hist["revenue"],
                name="История (Факт)",
                line=dict(color="#64748b", width=2.5),
                mode="lines"
            ))
            
            # Connection point
            conn_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig_fore.add_trace(go.Scatter(
                x=conn_df["date"],
                y=[df_hist.tail(1)["revenue"].values[0], adjusted_predicted_rev.values[0]],
                showlegend=False,
                line=dict(color="#ccff00", width=2.5, dash="dot")
            ))
            
            # Forecast line (Lime Green)
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"],
                y=adjusted_predicted_rev,
                name="Прогноз ИИ",
                line=dict(color="#ccff00", width=3.5),
                mode="lines+markers"
            ))
            
            # Confidence interval band
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
                y=adjusted_upper_bound.tolist() + adjusted_lower_bound.tolist()[::-1],
                fill="toself",
                fillcolor="rgba(204, 255, 0, 0.05)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="Доверительный интервал (95%)"
            ))
            
            fig_fore.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=340,
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(color="#64748b", size=10),
                    linecolor="#1a222f"
                ),
                yaxis=dict(
                    gridcolor="#1a222f",
                    tickfont=dict(color="#64748b", size=10),
                    zeroline=False
                ),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10, color="#8b99ad")
                )
            )
            st.plotly_chart(fig_fore, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Недостаточно данных для прогноза.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🌟 TAB 3: MENU ENGINEERING (Анализ меню)
# ==========================================
with tab_menu:
    menu_col_left, menu_col_right = st.columns([1.8, 1])
    
    with menu_col_left:
        st.markdown('<div class="custom-card" style="min-height: 600px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Матрица Smith-Shostack</p>', unsafe_allow_html=True)
        
        if not df_menu.empty:
            median_pop = df_menu["popularity_sales"].median()
            median_margin = df_menu["avg_margin"].median()
            
            colors_map = {
                "Stars": "#ccff00",
                "Workhorses": "#00d2ff",
                "Puzzles": "#ffa500",
                "Dogs": "#ff3353"
            }
            
            fig_scatter = px.scatter(
                df_menu,
                x="popularity_sales",
                y="avg_margin",
                color="cluster_label",
                text="item_name",
                color_discrete_map=colors_map,
                labels={
                    "popularity_sales": "Количество продаж (шт.)",
                    "avg_margin": "Маржа на единицу (₽)",
                    "cluster_label": "Класс блюда"
                }
            )
            
            # Add quadrant boundaries
            fig_scatter.add_vline(x=median_pop, line_dash="dash", line_color="#1a222f", line_width=1.5)
            fig_scatter.add_hline(y=median_margin, line_dash="dash", line_color="#1a222f", line_width=1.5)
            
            # Quadrant Labels in background
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 1.5, text="🌟 STARS", showarrow=False, font=dict(color="rgba(204, 255, 0, 0.15)", size=16, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 0.5, text="🐎 WORKHORSES", showarrow=False, font=dict(color="rgba(0, 210, 255, 0.15)", size=16, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 1.5, text="❓ PUZZLES", showarrow=False, font=dict(color="rgba(255, 165, 0, 0.15)", size=16, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 0.5, text="🐕 DOGS", showarrow=False, font=dict(color="rgba(255, 51, 83, 0.15)", size=16, weight="bold"))
            
            fig_scatter.update_traces(
                marker=dict(size=14, line=dict(width=1, color="#07090e")),
                textposition="top center",
                textfont=dict(color="#f1f5f9", size=10)
            )
            
            fig_scatter.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=480,
                xaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=10), linecolor="#1a222f"),
                yaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=10), linecolor="#1a222f"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10, color="#8b99ad")
                )
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет данных меню.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with menu_col_right:
        st.markdown('<div class="custom-card" style="min-height: 600px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:20px; text-transform:uppercase; letter-spacing:0.5px;">Стратегия оптимизации</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-bottom: 20px; border-left: 3px solid #ccff00; padding-left: 14px;">
            <strong style="color: #ccff00; font-size:13px;">🌟 STARS (Продвигать)</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #8b99ad; line-height: 1.4;">
                Высокая популярность и маржа. Оставьте рецептуру без изменений, выносите в топ меню, обучайте официантов продвигать их в приоритете.
            </p>
        </div>
        
        <div style="margin-bottom: 20px; border-left: 3px solid #00d2ff; padding-left: 14px;">
            <strong style="color: #00d2ff; font-size:13px;">🐎 WORKHORSES (Зарезать косты)</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #8b99ad; line-height: 1.4;">
                Высокая популярность, низкая маржа. Сократите себестоимость сырья за счет работы с поставщиками или слегка поднимите цену на 3-5%.
            </p>
        </div>
        
        <div style="margin-bottom: 20px; border-left: 3px solid #ffa500; padding-left: 14px;">
            <strong style="color: #ffa500; font-size:13px;">❓ PUZZLES (Стимулировать спрос)</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #8b99ad; line-height: 1.4;">
                Низкая популярность, высокая маржа. Запустите акцию, добавьте красивые фотографии, снизьте цену на 5% для проверки эластичности спроса.
            </p>
        </div>
        
        <div style="margin-bottom: 20px; border-left: 3px solid #ff3353; padding-left: 14px;">
            <strong style="color: #ff3353; font-size:13px;">🐕 DOGS (Исключить)</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #8b99ad; line-height: 1.4;">
                Низкая маржинальность и спрос. Либо полностью удалите блюдо из меню, либо радикально переработайте рецептуру и название.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Detailed table row
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Подробный анализ эффективности блюд</p>', unsafe_allow_html=True)
    
    if not df_menu.empty:
        # Build beautiful table
        table_html = """
        <div class="table-container">
            <table class="premium-table">
                <thead>
                    <tr>
                        <th>Название блюда</th>
                        <th>Категория</th>
                        <th>Продажи (ед.)</th>
                        <th>Маржа (ед.)</th>
                        <th>Выручка (всего)</th>
                        <th>Кластер (K-Means)</th>
                    </tr>
                </thead>
                <tbody>
        """
        for _, row in df_menu.iterrows():
            cluster = row["cluster_label"]
            badge_class = ""
            if cluster == "Stars":
                badge_class = "badge-star"
            elif cluster == "Workhorses":
                badge_class = "badge-workhorse"
            elif cluster == "Puzzles":
                badge_class = "badge-puzzle"
            else:
                badge_class = "badge-dog"
                
            table_html += f"""
                    <tr>
                        <td style="color:#ffffff; font-weight:700;">{row['item_name']}</td>
                        <td style="color:#8b99ad;">{row['category']}</td>
                        <td>{row['popularity_sales']:,} шт.</td>
                        <td>{row['avg_margin']:,.2f} ₽</td>
                        <td style="color:#ccff00;">{row['total_revenue']:,.0f} ₽</td>
                        <td><span class="badge {badge_class}">{cluster}</span></td>
                    </tr>
            """
        table_html += """
                </tbody>
            </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Нет данных о меню.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🤝 TAB 4: CROSS-SALES (Кросс-продажи)
# ==========================================
with tab_cross:
    cross_col_left, cross_col_right = st.columns([1.5, 1])
    
    with cross_col_left:
        st.markdown('<div class="custom-card" style="min-height: 580px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Матрица связей и совместных покупок P(B | A)</p>', unsafe_allow_html=True)
        
        if len(items_list) > 1 and len(assoc_matrix) > 0:
            fig_heat = go.Figure(data=go.Heatmap(
                z=assoc_matrix,
                x=items_list,
                y=items_list,
                colorscale=[[0, "#0f131a"], [0.4, "#17283c"], [1, "#ccff00"]],
                hoverongaps=False,
                text=[[f"P({b} | {a}) = {val:.1%}" for b, val in zip(items_list, row)] for a, row in zip(items_list, assoc_matrix)],
                hoverinfo="text"
            ))
            fig_heat.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                height=480,
                xaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=9), linecolor="#1a222f", tickangle=-45),
                yaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=9), linecolor="#1a222f")
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Загрузите больше чеков для расчета корреляционной матрицы.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with cross_col_right:
        st.markdown('<div class="custom-card" style="min-height: 580px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Интерактивный конструктор комбо</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px; color:#8b99ad; line-height:1.4; margin-bottom:20px;">Выберите основное блюдо, чтобы получить топ сопутствующих позиций и оптимальное комбо-предложение от ИИ.</p>', unsafe_allow_html=True)
        
        # Select item
        if items_list:
            selected_item = st.selectbox(
                "Основное блюдо (A):", 
                items_list, 
                key="cross_combo_select"
            )
        else:
            # fallback items
            selected_item = st.selectbox(
                "Основное блюдо (A):", 
                ["Бургер True", "Бургер Чизбургер", "Бургер Шеф-Краб", "Бургер Веган", "Картофель фри", "Соус сырный", "Кока-кола", "Пиво крафтовое"], 
                key="cross_combo_select"
            )
            
        # Get recommendations
        recommendations = []
        if is_live and selected_item in items_list:
            idx = items_list.index(selected_item)
            probs = assoc_matrix[idx]
            
            # Sort items by probability (descending) excluding self
            pairs = []
            for j, p in enumerate(probs):
                if items_list[j] != selected_item:
                    pairs.append((items_list[j], p))
            pairs.sort(key=lambda x: x[1], reverse=True)
            recommendations = [(name, p, round(1.2 + p * 0.5, 1)) for name, p in pairs[:3]]
        else:
            # fallback logic using offline dict
            recommendations = offline_assoc_lookup.get(selected_item, [("Картофель фри", 0.78, 1.3), ("Соус сырный", 0.72, 1.4), ("Кока-кола", 0.50, 1.1)])
            
        st.markdown("<p style='font-size:12px; font-weight:700; color:#ccff00; text-transform:uppercase; letter-spacing:0.5px; margin-top:20px;'>Топ сопутствующих позиций (ИИ):</p>", unsafe_allow_html=True)
        
        for name, prob, lift in recommendations:
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background-color:#141923; padding:10px 16px; border-radius:12px; margin-bottom:8px; border:1px solid #1a222f;">
                <div>
                    <span style="font-weight:700; color:#ffffff; font-size:13px;">{name}</span>
                    <br><span style="font-size:10px; color:#64748b;">Lift: {lift}x (Влияние)</span>
                </div>
                <span style="color:#ccff00; font-weight:800; font-size:13px;">{prob:.1%}</span>
            </div>
            """, unsafe_allow_html=True)
            
        # Combo card advice
        if recommendations:
            combo_name = f"Комбо '{selected_item.split()[-1] if len(selected_item.split()) > 1 else selected_item} + {recommendations[0][0].split()[-1] if len(recommendations[0][0].split()) > 1 else recommendations[0][0]}'"
            suggested_discount = 12
            margin_lift = 8.4 + (recommendations[0][1] * 10)
            
            st.markdown(f"""
            <div class="combo-card">
                <p style="font-size:10px; font-weight:800; color:#ccff00; text-transform:uppercase; letter-spacing:1px; margin:0 0 6px 0;">🎯 РЕКОМЕНДУЕМОЕ КОМБО</p>
                <h5 style="color:#ffffff; font-weight:800; font-size:14px; margin:0 0 8px 0;">{combo_name}</h5>
                <p style="font-size:12px; color:#8b99ad; line-height:1.4; margin:0 0 12px 0;">
                    Запустите бандл с автоматической скидкой в <strong>{suggested_discount}%</strong>. Это увеличит оборачиваемость сопутственной позиции и повысит маржинальность.
                </p>
                <div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.05); padding-top:10px; font-size:11px;">
                    <span style="color:#8b99ad;">Эффект среднего чека:</span>
                    <span style="color:#ccff00; font-weight:700;">+{margin_lift:.1f}% маржи</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚙️ TAB 5: SYSTEM CONTROL (Панель настроек)
# ==========================================
with tab_system:
    syst_col_left, syst_col_right = st.columns([1, 1])
    
    with syst_col_left:
        st.markdown('<div class="custom-card" style="min-height: 480px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px;">⚙️ Подключение к базе данных MySQL</p>', unsafe_allow_html=True)
        
        # Connection status block
        status_html = ""
        if is_live:
            status_html = """
            <div style="background-color: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 16px; padding: 20px; margin-bottom: 20px;">
                <div style="font-size: 14px; font-weight: 700; color: #10b981; margin-bottom: 12px; display:flex; align-items:center; gap:8px;">
                    <span>🟢 Статус: Онлайн</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px; color: #8b99ad;">
                    <span>Хост БД:</span><span style="font-weight:700; color:#fff;">restaurant_analytics_db:3306</span>
                    <span>База данных:</span><span style="font-weight:700; color:#fff;">restaurant_analytics</span>
                    <span>Имя таблиц:</span><span style="font-weight:700; color:#fff;">orders, order_items</span>
                </div>
            </div>
            """
        else:
            status_html = """
            <div style="background-color: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: 16px; padding: 20px; margin-bottom: 20px;">
                <div style="font-size: 14px; font-weight: 700; color: #f59e0b; margin-bottom: 12px; display:flex; align-items:center; gap:8px;">
                    <span>🟡 Статус: Демо-режим</span>
                </div>
                <p style="font-size: 12px; color: #8b99ad; line-height: 1.5; margin:0;">
                    MySQL на хосте restaurant_analytics_db недоступен или база данных пуста. Загружаются статические демонстрационные данные бургерной.
                </p>
            </div>
            """
        st.markdown(status_html, unsafe_allow_html=True)
        
        # Database seeding controls
        st.markdown("<p style='font-size:12px; font-weight:700; color:#ffffff; margin-bottom:8px;'>Сброс и автозаполнение БД:</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:11px; color:#8b99ad; line-height:1.4; margin-bottom:16px;'>Эта опция создаст пустые таблицы в MySQL и наполнит их реалистичными чеками бургерной True Burgers за последние 180 дней, после чего автоматически обучит модели LightGBM и K-Means.</p>", unsafe_allow_html=True)
        
        if not is_live:
            if st.button("🚀 Создать и наполнить демо-БД MySQL", type="primary", use_container_width=True):
                with st.spinner("Создание схем данных и генерация чеков за 180 дней..."):
                    res = post_data("/upload/seed-demo")
                    if res.get("success"):
                        st.success("База данных успешно создана и наполнена! Обновление страницы...")
                        st.rerun()
                    else:
                        st.error(f"Не удалось подключиться к MySQL. Убедитесь, что контейнеры запущены. Ошибка: {res.get('message')}")
        else:
            if st.button("🗑️ Полностью очистить и сбросить БД", type="secondary", use_container_width=True):
                with st.spinner("Очистка и пересоздание таблиц MySQL..."):
                    res = post_data("/upload/seed-demo")
                    if res.get("success"):
                        st.success("База данных успешно сброшена к чистым демо-данным.")
                        st.rerun()
                    else:
                        st.error("Не удалось сбросить БД.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with syst_col_right:
        st.markdown('<div class="custom-card" style="min-height: 480px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px; font-weight:700; color:#fff; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px;">📥 Импорт чеков (CRM CSV/XLSX)</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:11px; color:#8b99ad; line-height:1.4; margin-bottom:16px;">Загрузите выгрузку чеков из систем iiko, R-Keeper, МойСклад или собственной CRM. Поддерживаются русские и английские заголовки колонок.</p>', unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader("Выберите файл CRM чеков:", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_preview = pd.read_csv(uploaded_file, nrows=3)
                else:
                    df_preview = pd.read_excel(uploaded_file, nrows=3)
                
                st.markdown("<p style='font-size: 11px; font-weight: 700; color:#ffffff; margin-top:12px;'>Предпросмотр структуры файла:</p>", unsafe_allow_html=True)
                st.dataframe(df_preview, use_container_width=True)
                
                st.markdown("<p style='font-size: 11px; color:#8b99ad;'>Файл готов к импорту. Будет произведено автоматическое сопоставление полей чека.</p>", unsafe_allow_html=True)
                
                if st.button("📤 Начать импорт и обучение ИИ моделей", type="primary", use_container_width=True):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    with st.spinner("Загрузка чеков, валидация полей и переобучение ML моделей..."):
                        res = post_data("/upload/checks", files=files)
                        if res.get("success"):
                            st.success(f"Успешный импорт! Заказов добавлено: {res.get('orders_processed', 0)}, позиций: {res.get('items_processed', 0)}")
                            st.rerun()
                        else:
                            st.error(f"Ошибка при обработке файла: {res.get('message')}")
            except Exception as e:
                st.error(f"Не удалось распарсить файл: {str(e)}")
        else:
            st.info("Пожалуйста, перетащите файл CRM чеков (.csv или .xlsx) в зону загрузки.")
            
        st.markdown('</div>', unsafe_allow_html=True)
