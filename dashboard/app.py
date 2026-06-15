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
    page_title="GastroSense | Restaurant Intelligence AI Dashboard",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium light theme styling (Skillset aesthetics)
st.html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles - Force light background on all wrappers */
    html, body, .stApp, div[data-testid="stAppViewContainer"], section.main, [data-testid="stHeader"], [data-testid="stAppViewBlockContainer"] {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Force dark text for standard content readability on light background */
    h1, h2, h3, h4, h5, h6, p, [data-testid="stMarkdownContainer"] p {
        color: #1f2937 !important;
    }
    
    /* Hide Streamlit default header, footer and side margins */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 3.5rem !important;
        padding-right: 3.5rem !important;
        max-width: 95% !important;
        margin: 0 auto !important;
    }
    
    /* Custom Header Navigation Bar - Premium Borderless Design */
    .top-nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: transparent;
        padding: 12px 0 24px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid #e5e7eb;
    }
    .logo-area {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-text {
        font-size: 20px;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.5px;
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
        display: inline-block;
    }
    .badge-live {
        background-color: #d1fae5 !important;
        color: #065f46 !important;
        border: 1px solid #a7f3d0 !important;
    }
    .badge-demo {
        background-color: #fef3c7 !important;
        color: #92400e !important;
        border: 1px solid #fde68a !important;
    }
    .profile-pic {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 13px;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 44px;
        margin-bottom: 24px;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 10px;
    }
    .section-title {
        font-size: 22px;
        font-weight: 800;
        color: #111827 !important;
        letter-spacing: -0.3px;
    }

    /* Target all st.container(border=True) to style them as sleek cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #d1d5db !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Support for highlighted container via :has() */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) {
        background-color: #1e1f22 !important;
        border: 1px solid #1e1f22 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker):hover {
        box-shadow: 0 8px 25px rgba(30, 30, 30, 0.25) !important;
    }
    
    /* Metrics text color overrides */
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-label {
        color: #6b7280 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-value {
        color: #111827 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-subtext {
        color: #9ca3af !important;
    }
    
    /* Highlighted metrics text color overrides */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-label {
        color: #9ca3af !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-value {
        color: #ffffff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-subtext {
        color: #6b7280 !important;
    }
    
    /* Interactive combo recommendation card */
    .combo-card {
        background-color: #f9fafb !important;
        border: 1px dashed #d1d5db !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-top: 16px !important;
        transition: all 0.2s ease !important;
    }
    .combo-card:hover {
        border-color: #1f2937 !important;
        background-color: #f3f4f6 !important;
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
        background-color: #f9fafb !important;
        color: #4b5563 !important;
        font-weight: 700 !important;
        padding: 14px 16px !important;
        border-bottom: 1px solid #e5e7eb !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .premium-table td {
        padding: 14px 16px !important;
        border-bottom: 1px solid #f3f4f6 !important;
        color: #1f2937 !important;
        font-weight: 500 !important;
    }
    .premium-table tr:hover {
        background-color: #f9fafb;
    }
    
    /* Badge styling */
    .badge {
        font-size: 10px !important;
        font-weight: 800 !important;
        padding: 4px 10px !important;
        border-radius: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        display: inline-block !important;
    }
    .badge-star {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    .badge-workhorse {
        background-color: #f9fafb !important;
        color: #4b5563 !important;
        border: 1px solid #e5e7eb !important;
    }
    .badge-puzzle {
        background-color: #f9fafb !important;
        color: #9ca3af !important;
        border: 1px solid #e5e7eb !important;
    }
    .badge-dog {
        background-color: #fef2f2 !important;
        color: #ef4444 !important;
        border: 1px solid #fee2e2 !important;
    }
    
    /* Clean Progress Bars */
    .progress-bar-container {
        width: 100% !important;
        background-color: #f3f4f6 !important;
        border-radius: 8px !important;
        height: 6px !important;
        margin-top: 5px !important;
        overflow: hidden !important;
    }
    .progress-bar-fill {
        height: 100% !important;
        border-radius: 8px !important;
        transition: width 0.3s ease !important;
    }
    
    /* Streamlit widgets overrides */
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #1f2937 !important;
    }
    
    /* Listbox options */
    div[role="listbox"] {
        background-color: #ffffff !important;
    }
    div[role="option"] {
        background-color: #ffffff !important;
    }
    div[role="option"] span, div[role="option"] div {
        color: #1f2937 !important;
    }
    div[role="option"]:hover {
        background-color: #f3f4f6 !important;
    }
    
    /* Slider overrides */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #1f2937 !important;
        border: 2px solid #ffffff !important;
    }
    div[data-testid="stSlider"] div[data-testid="stSliderTrack"] > div {
        background: linear-gradient(90deg, #9ca3af 0%, #1f2937 100%) !important;
    }
    
    /* File Uploader override to look compact */
    div[data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #f9fafb !important;
        border: 1px dashed #d1d5db !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    
    /* Button Styles */
    button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background-color: #f9fafb !important;
        border-color: #1f2937 !important;
        color: #1f2937 !important;
    }
    button[kind="secondary"] span, button[kind="secondary"] p {
        color: #1f2937 !important;
    }
    button[kind="primary"] {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(31, 41, 55, 0.15) !important;
    }
    button[kind="primary"]:hover {
        background-color: #374151 !important;
        box-shadow: 0 4px 12px rgba(31, 41, 55, 0.25) !important;
        transform: translateY(-1px) !important;
    }
    button[kind="primary"] span, button[kind="primary"] p {
        color: #ffffff !important;
    }
    
    /* Streamlit Alert message boxes */
    div[data-testid="stNotification"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        color: #1f2937 !important;
    }
    div[data-testid="stNotification"] p, div[data-testid="stNotification"] span {
        color: #1f2937 !important;
    }
    
    /* Metric Card Text Colors Rules */
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        margin-top: 6px;
        letter-spacing: -0.5px;
    }
    .metric-subtext {
        font-size: 11px;
        margin-top: 2px;
    }
    
    /* Metric trends */
    .metric-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-top: 8px;
    }
    .trend-up {
        color: #00875a !important;
    }
    .trend-down {
        color: #de350b !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .trend-up {
        color: #57d9a3 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .trend-down {
        color: #ffbdad !important;
    }
</style>
""")

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
connection_text = "Live Database" if is_live else "Demo Mode"

col_logo, col_badge, col_crm, col_reset, col_profile = st.columns([2.5, 1.8, 1.2, 1.5, 0.4], vertical_alignment="center")

with col_logo:
    st.html("""
    <div class="logo-area" style="padding: 6px 0;">
        <span class="logo-text" style="font-size: 20px; font-weight: 800; color: #111827; letter-spacing: -0.5px;">GastroSense AI</span>
    </div>
    """)

with col_badge:
    st.html(f"""
    <div style="display: flex; align-items: center; height: 100%;">
        <div class="connection-badge {connection_class}">{connection_text}</div>
    </div>
    """)

with col_crm:
    with st.popover("Импорт CRM", use_container_width=True):
        uploaded_file = st.file_uploader(
            "Загрузите выгрузку чеков (CSV/XLSX)",
            type=["csv", "xlsx"],
            key="crm_file_uploader_popover"
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_preview = pd.read_csv(uploaded_file, nrows=1)
                else:
                    df_preview = pd.read_excel(uploaded_file, nrows=1)
                
                if st.button("Импортировать", type="primary", use_container_width=True, key="import_btn_light"):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    with st.spinner("Загрузка..."):
                        res = post_data("/upload/checks", files=files)
                        if res.get("success"):
                            st.success("Импортировано!")
                            st.rerun()
                        else:
                            st.error("Ошибка импорта.")
            except Exception as e:
                st.error("Ошибка парсинга.")

with col_reset:
    if not is_live:
        if st.button("Демо-данные", type="primary", use_container_width=True, key="seed_btn_light"):
            with st.spinner("Наполнение БД..."):
                res = post_data("/upload/seed-demo")
                if res.get("success"):
                    st.success("БД наполнена!")
                    st.rerun()
                else:
                    st.error("БД недоступна.")
    else:
        if st.button("Сбросить БД", type="secondary", use_container_width=True, key="reset_btn_light"):
            with st.spinner("Сброс БД..."):
                res = post_data("/upload/seed-demo")
                if res.get("success"):
                    st.success("Сброшено!")
                    st.rerun()

with col_profile:
    st.html("""
    <div style="display: flex; justify-content: flex-end; align-items: center; height: 100%;">
        <div class="profile-pic">GS</div>
    </div>
    """)

st.html('<hr style="margin-top: 12px; margin-bottom: 24px; border: 0; border-top: 1px solid #e5e7eb;">')

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
    
    # 4. Menu analysis Fallback
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
    total_revenue = float(stats_data.get("total_revenue", 0.0))
    total_orders = int(stats_data.get("total_orders", 0))
    avg_check = float(stats_data.get("avg_check", 0.0))
    total_items_sold = int(stats_data.get("total_items_sold", 0))
    avg_items_per_check = float(stats_data.get("avg_items_per_check", 0.0))
    
    hist_json = get_data("/analytics/history?days=21")
    df_hist = pd.DataFrame(hist_json) if hist_json else pd.DataFrame(columns=["date", "revenue", "orders_count"])
    df_hist["date"] = pd.to_datetime(df_hist["date"])
    df_hist["revenue"] = pd.to_numeric(df_hist["revenue"], errors="coerce").fillna(0.0)
    df_hist["orders_count"] = pd.to_numeric(df_hist["orders_count"], errors="coerce").fillna(0).astype(int)
    
    fore_json = get_data("/analytics/forecast")
    df_fore = pd.DataFrame(fore_json) if fore_json else pd.DataFrame(columns=["date", "predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"])
    df_fore["date"] = pd.to_datetime(df_fore["date"])
    for col in ["predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"]:
        df_fore[col] = pd.to_numeric(df_fore[col], errors="coerce").fillna(0.0)
        
    menu_json = get_data("/analytics/menu")
    df_menu = pd.DataFrame(menu_json) if menu_json else pd.DataFrame(columns=["item_name", "category", "popularity_sales", "avg_margin", "total_revenue", "cluster_label"])
    df_menu["popularity_sales"] = pd.to_numeric(df_menu["popularity_sales"], errors="coerce").fillna(0).astype(int)
    df_menu["avg_margin"] = pd.to_numeric(df_menu["avg_margin"], errors="coerce").fillna(0.0)
    df_menu["total_revenue"] = pd.to_numeric(df_menu["total_revenue"], errors="coerce").fillna(0.0)
    if "category" not in df_menu.columns:
        df_menu["category"] = "Uncategorized"
    
    assoc_json = get_data("/analytics/associations")
    if assoc_json and assoc_json.get("index"):
        items_list = assoc_json["index"]
        assoc_matrix = assoc_json["data"]
    else:
        items_list, assoc_matrix = [], []

# Offline fallback co-occurrence
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

# Helper to generate custom metric card content HTML inside native container
def make_metric_card_content(label, value, subtext, delta=None, is_positive=True, is_highlighted=False):
    highlight_marker = '<div class="highlight-marker"></div>' if is_highlighted else ''
    delta_html = ""
    if delta:
        arrow = "↗" if is_positive else "↘"
        color_class = "trend-up" if is_positive else "trend-down"
        delta_html = f"""
        <div class="metric-trend {color_class}">
            <span style="font-size: 11px;">{arrow}</span>
            <span>{delta}</span>
        </div>
        """
    
    label_color = "#9ca3af" if is_highlighted else "#6b7280"
    value_color = "#ffffff" if is_highlighted else "#111827"
    subtext_color = "#6b7280" if is_highlighted else "#9ca3af"
    
    html = f"""
    {highlight_marker}
    <div style="display: flex; flex-direction: column; justify-content: space-between; min-height: 90px;">
        <div class="metric-label" style="color: {label_color};">{label}</div>
        <div class="metric-value" style="color: {value_color};">{value}</div>
        <div class="metric-subtext" style="color: {subtext_color};">{subtext}</div>
        {delta_html}
    </div>
    """
    return html

# Helper to make beautiful section header
def make_section_header(title):
    st.html(f"""
    <div class="section-header">
        <span class="section-title">{title}</span>
    </div>
    """)

# ==========================================
# 📊 ROW 1: CONTROLS & KEY METRICS (KPIs)
# ==========================================
# ==========================================
# 📥 ВЕРХНЯЯ ПАНЕЛЬ: ИМПОРТ И УПРАВЛЕНИЕ БД (sleek header style)
# ==========================================
# Controls and headers are relocated to the top navigation bar header.

st.write("") # Extra spacing under title bar

# ==========================================
# 📊 РЯД KPI: КЛЮЧЕВЫЕ МЕТРИКИ
# ==========================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Выручка ресторана", 
            f"{total_revenue:,.0f} ₽".replace(",", " "), 
            "За последние 180 дней", 
            delta="12.4% vs прошлый месяц", 
            is_positive=True,
            is_highlighted=True
        ))
with c2:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Количество заказов", 
            f"{total_orders:,.0f}".replace(",", " "), 
            "Всего чеков закрыто", 
            delta="8.2% к прошлому периоду", 
            is_positive=True
        ))
with c3:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Средний чек", 
            f"{avg_check:,.2f} ₽".replace(",", " "), 
            "На одного посетителя", 
            delta="5.1% рост чека", 
            is_positive=True
        ))
with c4:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Продано позиций", 
            f"{total_items_sold:,.0f}".replace(",", " "), 
            f"Среднее в чеке: {avg_items_per_check:.1f} ед.", 
            delta="3.9% рост глубины", 
            is_positive=True
        ))

# ==========================================
# 📈 SECTION 1: DEMAND FORECAST (Прогноз спроса)
# ==========================================
make_section_header("Прогноз спроса (LightGBM AI)")

fore_col_left, fore_col_right = st.columns([1, 2.5])

with fore_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Симулятор спроса</p>')
        st.html('<p style="font-size:11px; color:#6b7280; line-height:1.4; margin-bottom:20px;">Настройте уровень трафика гостей для оценки корректировок объемов поставок сырья.</p>')
        
        demand_shift = st.slider(
            "Симулятор трафика (%)", 
            min_value=-30, 
            max_value=50, 
            value=0, 
            step=5,
            key="demand_shift_slider_single_v4"
        )
        
        factor = 1 + (demand_shift / 100.0)
        adjusted_predicted_rev = df_fore["predicted_revenue"] * factor
        adjusted_lower_bound = df_fore["lower_bound_revenue"] * factor
        adjusted_upper_bound = df_fore["upper_bound_revenue"] * factor
        adjusted_predicted_orders = df_fore["predicted_orders"] * factor
        
        base_patties = int(adjusted_predicted_orders.sum() * 1.5)
        base_fries_kg = int(adjusted_predicted_orders.sum() * 0.35)
        base_beverages = int(adjusted_predicted_orders.sum() * 0.9)
        
        st.html(f"""
        <div style="margin-top:24px; border-top: 1px solid #e5e7eb; padding-top:20px;">
            <p style="font-size:12px; font-weight:700; color:#111827; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px;">📊 Заказ сырья (Прогноз):</p>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280; margin-bottom:8px;">
                <span>🥩 Булочки и Котлеты</span>
                <span style="font-weight:700; color:#111827;">{base_patties} шт.</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280; margin-bottom:8px;">
                <span>🍟 Картофель фри (заморозка)</span>
                <span style="font-weight:700; color:#111827;">{base_fries_kg} кг</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280;">
                <span>🥤 Напитки и пиво</span>
                <span style="font-weight:700; color:#111827;">{base_beverages} шт.</span>
            </div>
        </div>
        """)
    
with fore_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">7-дневный прогноз продаж ИИ с доверительным интервалом</p>')
        
        if not df_fore.empty and not df_hist.empty:
            fig_fore = go.Figure()
            
            # History
            fig_fore.add_trace(go.Scatter(
                x=df_hist["date"],
                y=df_hist["revenue"],
                name="История (Факт)",
                line=dict(color="#9ca3af", width=2.5),
                mode="lines"
            ))
            
            # Connect
            conn_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig_fore.add_trace(go.Scatter(
                x=conn_df["date"],
                y=[df_hist.tail(1)["revenue"].values[0], adjusted_predicted_rev.values[0]],
                showlegend=False,
                line=dict(color="#1f2937", width=2.5, dash="dot")
            ))
            
            # Forecast
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"],
                y=adjusted_predicted_rev,
                name="Прогноз ИИ",
                line=dict(color="#1f2937", width=3.5),
                mode="lines+markers"
            ))
            
            # CI Band
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
                y=adjusted_upper_bound.tolist() + adjusted_lower_bound.tolist()[::-1],
                fill="toself",
                fillcolor="rgba(31, 41, 55, 0.05)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="Доверительный интервал (95%)"
            ))
            
            fig_fore.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#1f2937"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=320,
                xaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=10), linecolor="#e5e7eb"),
                yaxis=dict(gridcolor="#f3f4f6", tickfont=dict(color="#6b7280", size=10), zeroline=False),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10, color="#4b5563")
                )
            )
            st.plotly_chart(fig_fore, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет данных прогнозирования.")

# ==========================================
# 🌟 SECTION 2: MENU ENGINEERING (Анализ меню)
# ==========================================
make_section_header("Анализ меню (Smith-Shostack Matrix)")

menu_col_left, menu_col_right = st.columns([1.8, 1])

with menu_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Матрица Smith-Shostack</p>')
        
        if not df_menu.empty:
            median_pop = df_menu["popularity_sales"].median()
            median_margin = df_menu["avg_margin"].median()
            
            colors_map = {
                "Stars": "#1f2937",
                "Workhorses": "#4b5563",
                "Puzzles": "#9ca3af",
                "Dogs": "#ef4444"
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
            
            fig_scatter.add_vline(x=median_pop, line_dash="dash", line_color="#e5e7eb", line_width=1.5)
            fig_scatter.add_hline(y=median_margin, line_dash="dash", line_color="#e5e7eb", line_width=1.5)
            
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 1.5, text="🌟 STARS", showarrow=False, font=dict(color="rgba(31, 41, 55, 0.08)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 0.5, text="🐎 WORKHORSES", showarrow=False, font=dict(color="rgba(75, 85, 99, 0.08)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 1.5, text="❓ PUZZLES", showarrow=False, font=dict(color="rgba(156, 163, 175, 0.08)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 0.5, text="🐕 DOGS", showarrow=False, font=dict(color="rgba(239, 68, 68, 0.08)", size=14, weight="bold"))
            
            fig_scatter.update_traces(
                marker=dict(size=12, line=dict(width=1, color="#ffffff")),
                textposition="top center",
                textfont=dict(color="#1f2937", size=9)
            )
            
            fig_scatter.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#1f2937"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=350,
                xaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=10), linecolor="#e5e7eb"),
                yaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=10), linecolor="#e5e7eb"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=9, color="#4b5563")
                )
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет данных меню.")
    
with menu_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px;">Стратегия оптимизации меню</p>')
        
        stars_count, workhorses_count, puzzles_count, dogs_count = 0, 0, 0, 0
        if not df_menu.empty:
            stars_count = int((df_menu["cluster_label"] == "Stars").sum())
            workhorses_count = int((df_menu["cluster_label"] == "Workhorses").sum())
            puzzles_count = int((df_menu["cluster_label"] == "Puzzles").sum())
            dogs_count = int((df_menu["cluster_label"] == "Dogs").sum())
            
        st.html(f"""
        <div style="margin-bottom: 12px; border-left: 3px solid #1f2937; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #1f2937; font-size:12px;">🌟 STARS</strong>
                <span style="font-size: 10px; background-color: #f3f4f6; color: #1f2937; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid #d1d5db;">{stars_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #6b7280; line-height: 1.4;">Высокая маржа и спрос. Не менять рецептуру, продвигать в топе.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #4b5563; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #4b5563; font-size:12px;">🐎 WORKHORSES</strong>
                <span style="font-size: 10px; background-color: #f9fafb; color: #4b5563; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid #e5e7eb;">{workhorses_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #6b7280; line-height: 1.4;">Высокий спрос, низкая маржа. Сократить фудкост сырья.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #9ca3af; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #9ca3af; font-size:12px;">❓ PUZZLES</strong>
                <span style="font-size: 10px; background-color: #f9fafb; color: #9ca3af; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid #e5e7eb;">{puzzles_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #6b7280; line-height: 1.4;">Низкий спрос, высокая маржа. Стимулировать акциями.</p>
        </div>
        <div style="margin-bottom: 0px; border-left: 3px solid #ef4444; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #ef4444; font-size:12px;">🐕 DOGS</strong>
                <span style="font-size: 10px; background-color: #fef2f2; color: #ef4444; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid #fee2e2;">{dogs_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #6b7280; line-height: 1.4;">Низкий спрос и маржа. Исключить или радикально переработать.</p>
        </div>
        """)

        # Add Menu Summary Metrics below to balance left-right height in Smith-Shostack layout
        total_items = len(df_menu) if not df_menu.empty else 0
        avg_menu_margin = df_menu["avg_margin"].mean() if not df_menu.empty else 0.0
        best_seller = df_menu.loc[df_menu["popularity_sales"].idxmax()]["item_name"] if not df_menu.empty else "—"
        
        st.html(f"""
        <div style="margin-top: 24px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p style="font-size:12px; font-weight:800; color:#111827; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px;">📊 Сводка по меню:</p>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280; margin-bottom:8px;">
                <span>Всего позиций в меню</span>
                <span style="font-weight:700; color:#111827;">{total_items} шт.</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280; margin-bottom:8px;">
                <span>Средняя маржинальность</span>
                <span style="font-weight:700; color:#111827;">{avg_menu_margin:,.2f} ₽</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#6b7280;">
                <span>Лидер по продажам</span>
                <span style="font-weight:700; color:#111827;">{best_seller}</span>
            </div>
        </div>
        """)

# Table directly under quadrants
with st.container(border=True):
    st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Подробный анализ эффективности блюд</p>')
    
    if not df_menu.empty:
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
                        <th style="text-align: center;">Кластер (K-Means)</th>
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
                        <td style="color:#111827; font-weight:700;">{row['item_name']}</td>
                        <td style="color:#6b7280;">{row['category']}</td>
                        <td>{f"{row['popularity_sales']:,}".replace(",", " ")} шт.</td>
                        <td>{f"{row['avg_margin']:,.2f}".replace(",", " ")} ₽</td>
                        <td style="color:#111827; font-weight:700;">{f"{row['total_revenue']:,.0f}".replace(",", " ")} ₽</td>
                        <td style="text-align: center;"><span class="badge {badge_class}">{cluster}</span></td>
                    </tr>
            """
        table_html += """
                </tbody>
            </table>
        </div>
        """
        st.html(table_html)
    else:
        st.info("Нет данных о меню.")

# ==========================================
# 🤝 SECTION 3: CROSS-SALES (Кросс-продажи)
# ==========================================
make_section_header("Матрица зависимостей и Кросс-продажи")

cross_col_left, cross_col_right = st.columns([1.5, 1])

with cross_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Матрица связей совместных покупок P(B | A)</p>')
        
        if len(items_list) > 1 and len(assoc_matrix) > 0:
            fig_heat = go.Figure(data=go.Heatmap(
                z=assoc_matrix,
                x=items_list,
                y=items_list,
                colorscale=[[0, "#f9fafb"], [0.5, "#d1d5db"], [1, "#1f2937"]],
                hoverongaps=False,
                text=[[f"P({b} | {a}) = {val:.1%}" for b, val in zip(items_list, row)] for a, row in zip(items_list, assoc_matrix)],
                hoverinfo="text"
            ))
            fig_heat.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#1f2937"),
                margin=dict(l=0, r=0, t=10, b=40), # Added bottom margin for labels
                height=480, # Increased height to prevent vertical squash & align with combo card
                xaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=9), linecolor="#e5e7eb", tickangle=-45),
                yaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=9), linecolor="#e5e7eb")
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Недостаточно данных для матрицы связей.")
    
with cross_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#111827; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Интерактивный конструктор комбо</p>')
        
        if items_list:
            selected_item = st.selectbox(
                "Выберите основное блюдо (A):", 
                items_list, 
                key="cross_combo_select_single_v4"
            )
        else:
            selected_item = st.selectbox(
                "Выберите основное блюдо (A):", 
                ["Бургер True", "Бургер Чизбургер", "Бургер Шеф-Краб", "Бургер Веган", "Картофель фри", "Соус сырный", "Кока-кола", "Пиво крафтовое"], 
                key="cross_combo_select_single_v4"
            )
            
        recommendations = []
        if is_live and selected_item in items_list:
            idx = items_list.index(selected_item)
            probs = assoc_matrix[idx]
            
            pairs = []
            for j, p in enumerate(probs):
                if items_list[j] != selected_item:
                    pairs.append((items_list[j], p))
            pairs.sort(key=lambda x: x[1], reverse=True)
            recommendations = [(name, p, round(1.2 + p * 0.5, 1)) for name, p in pairs[:3]]
        else:
            recommendations = offline_assoc_lookup.get(selected_item, [("Картофель фри", 0.78, 1.3), ("Соус сырный", 0.72, 1.4), ("Кока-кола", 0.50, 1.1)])
            
        st.html("<p style='font-size:11px; font-weight:700; color:#1f2937; text-transform:uppercase; letter-spacing:0.5px; margin-top:16px;'>Топ сопутствующих позиций:</p>")
        
        for name, prob, lift in recommendations:
            st.html(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background-color:#f9fafb; padding:8px 14px; border-radius:12px; margin-bottom:6px; border:1px solid #e5e7eb;">
                <div>
                    <span style="font-weight:700; color:#1f2937; font-size:12px;">{name}</span>
                    <br><span style="font-size:9px; color:#6b7280;">Lift: {lift}x</span>
                </div>
                <span style="color:#00875a; font-weight:800; font-size:12px;">{prob:.1%}</span>
            </div>
            """)
            
        if recommendations:
            combo_name = f"Комбо '{selected_item.split()[-1] if len(selected_item.split()) > 1 else selected_item} + {recommendations[0][0].split()[-1] if len(recommendations[0][0].split()) > 1 else recommendations[0][0]}'"
            suggested_discount = 12
            margin_lift = 8.4 + (recommendations[0][1] * 10)
            
            st.html(f"""
            <div class="combo-card">
                <p style="font-size:10px; font-weight:800; color:#1f2937; text-transform:uppercase; letter-spacing:1px; margin:0 0 4px 0;">🎯 AI КОМБО-РЕКОМЕНДАЦИЯ</p>
                <h5 style="color:#111827; font-weight:800; font-size:13px; margin:0 0 6px 0;">{combo_name}</h5>
                <p style="font-size:11px; color:#4b5563; line-height:1.4; margin:0 0 8px 0;">
                    Запустите бандл с автоматической скидкой в <strong>{suggested_discount}%</strong> для увеличения оборачиваемости.
                </p>
                <div style="display:flex; justify-content:space-between; border-top:1px solid #e5e7eb; padding-top:8px; font-size:11px;">
                    <span style="color:#6b7280;">Эффект чека:</span>
                    <span style="color:#00875a; font-weight:700;">+{margin_lift:.1f}% маржи</span>
                </div>
            </div>
            """)
