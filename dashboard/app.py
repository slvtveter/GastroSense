import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
from datetime import datetime, date, timedelta

# Page configuration for a wide, premium feel
st.set_page_config(
    page_title="GastroSense | Restaurant Intelligence",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom CSS Injection (Light Minimalist design resembling Donezo / Skillset)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
        color: #1e293b !important;
    }
    
    /* Hide default streamlit header/footer for white label look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove padding and default colors */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 95% !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #f1f5f9 !important;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.01) !important;
    }
    
    /* Hide default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Custom Sidebar Menu options styling */
    [data-testid="stSidebar"] [data-testid="stRadioButton"] > label {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] {
        gap: 6px;
        padding: 5px 0;
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label {
        background-color: #ffffff;
        border: 1px solid #f8fafc;
        border-radius: 12px;
        padding: 12px 16px !important;
        margin-bottom: 4px;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label:hover {
        background-color: #f8fafc;
        border-color: #cbd5e1;
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #0f5132 !important;
        border-color: #0f5132 !important;
        box-shadow: 0 4px 12px rgba(15, 81, 50, 0.15);
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label:has(input:checked) span {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* Hide the radio button circle indicator */
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label div[role="presentation"],
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label div[class*="st-"] {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadioButton"] div[role="radiogroup"] label input {
        display: none !important;
    }
    
    /* Sleek Cards */
    .card {
        background-color: #ffffff;
        border: 1px solid #f1f5f9;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.02), 0 4px 6px -4px rgba(0, 0, 0, 0.02);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 16px;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -6px rgba(0, 0, 0, 0.05);
    }
    
    .card-green {
        background: linear-gradient(135deg, #0f5132 0%, #177a4c 100%);
        color: #ffffff;
    }
    
    /* Styled Premium Buttons */
    div.stButton > button {
        border-radius: 30px !important;
        background-color: #0f5132 !important;
        color: #ffffff !important;
        border: 1px solid #0f5132 !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        width: 100%;
        box-shadow: 0 2px 4px rgba(15, 81, 50, 0.1);
    }
    div.stButton > button:hover {
        background-color: #177a4c !important;
        border-color: #177a4c !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(15, 81, 50, 0.2);
    }
    div.stButton > button:active {
        transform: translateY(0);
    }

    /* Style selectboxes */
    div[data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Progress bar design */
    .progress-bar-container {
        width: 100%;
        background-color: #f1f5f9;
        border-radius: 10px;
        height: 8px;
        margin-top: 6px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease-in-out;
    }

    /* Premium Custom Table Styles */
    .premium-table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 13px;
        text-align: left;
    }
    .premium-table th {
        background-color: #f8fafc;
        color: #64748b;
        font-weight: 700;
        padding: 12px 16px;
        border-bottom: 1px solid #f1f5f9;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .premium-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #f8fafc;
        color: #1e293b;
    }
    .premium-table tr:hover {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# Connection Settings
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# Helper function to query the API
def get_data(endpoint: str):
    try:
        response = requests.get(f"{BACKEND_API_URL}{endpoint}", timeout=2)
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
avg_ai_acc = 94.2 # Base forecast model accuracy (WAPE)

# ----------------- DATA PREPARATION -----------------
# Fallback data configuration
if not is_live:
    total_revenue = 8933480.0
    total_orders = 11303
    avg_check = 790.36
    total_items_sold = 34300
    avg_items_per_check = 3.0
    
    # 21-day History
    base_date = datetime.now() - timedelta(days=21)
    hist_dates = [base_date + timedelta(days=i) for i in range(21)]
    hist_revenue = [
        380000, 395000, 310000, 320000, 340000, 420000, 480000,
        390000, 400000, 325000, 330000, 350000, 435000, 495000,
        405000, 410000, 335000, 340000, 360000, 450000, 510000
    ]
    df_hist = pd.DataFrame({"date": hist_dates, "revenue": hist_revenue})
    
    # 7-day Forecast
    forecast_dates = [datetime.now() + timedelta(days=i) for i in range(1, 8)]
    predicted_rev = [415000, 345000, 350000, 370000, 465000, 530000, 425000]
    lower_bound = [r * 0.92 for r in predicted_rev]
    upper_bound = [r * 1.08 for r in predicted_rev]
    df_fore = pd.DataFrame({
        "date": forecast_dates,
        "predicted_revenue": predicted_rev,
        "predicted_orders": [520, 430, 440, 465, 580, 660, 530],
        "lower_bound_revenue": lower_bound,
        "upper_bound_revenue": upper_bound
    })
    
    # Menu Engineering (with simulated price/cost)
    df_menu = pd.DataFrame([
        {"item_name": "Бургер True", "popularity_sales": 2450, "avg_margin": 247.5, "price": 450.0, "cost": 202.5, "cluster_label": "Stars"},
        {"item_name": "Бургер Чизбургер", "popularity_sales": 2820, "avg_margin": 152.0, "price": 350.0, "cost": 198.0, "cluster_label": "Workhorses"},
        {"item_name": "Бургер Шеф-Краб", "popularity_sales": 420, "avg_margin": 306.8, "price": 750.0, "cost": 443.2, "cluster_label": "Puzzles"},
        {"item_name": "Бургер Веган", "popularity_sales": 250, "avg_margin": 147.0, "price": 400.0, "cost": 253.0, "cluster_label": "Dogs"},
        {"item_name": "Картофель фри", "popularity_sales": 3400, "avg_margin": 140.4, "price": 200.0, "cost": 59.6, "cluster_label": "Stars"},
        {"item_name": "Кока-кола", "popularity_sales": 3100, "avg_margin": 96.0, "price": 150.0, "cost": 54.0, "cluster_label": "Workhorses"},
        {"item_name": "Пиво крафтовое", "popularity_sales": 610, "avg_margin": 218.4, "price": 350.0, "cost": 131.6, "cluster_label": "Puzzles"},
        {"item_name": "Соус сырный", "popularity_sales": 2900, "avg_margin": 39.0, "price": 50.0, "cost": 11.0, "cluster_label": "Stars"},
        {"item_name": "Сырные палочки", "popularity_sales": 450, "avg_margin": 180.0, "price": 300.0, "cost": 120.0, "cluster_label": "Puzzles"},
        {"item_name": "Кольца луковые", "popularity_sales": 310, "avg_margin": 124.8, "price": 220.0, "cost": 95.2, "cluster_label": "Dogs"}
    ])
    
    # Associations Heatmap
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
    df_hist = pd.DataFrame(hist_json) if hist_json else pd.DataFrame(columns=["date", "revenue"])
    df_hist["date"] = pd.to_datetime(df_hist["date"])
    df_hist["revenue"] = pd.to_numeric(df_hist["revenue"], errors="coerce").fillna(0.0)
    
    # Read live forecast
    fore_json = get_data("/analytics/forecast")
    df_fore = pd.DataFrame(fore_json) if fore_json else pd.DataFrame(columns=["date", "predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"])
    df_fore["date"] = pd.to_datetime(df_fore["date"])
    for col in ["predicted_revenue", "predicted_orders", "lower_bound_revenue", "upper_bound_revenue"]:
        df_fore[col] = pd.to_numeric(df_fore[col], errors="coerce").fillna(0.0)
        
    # Read live menu
    menu_json = get_data("/analytics/menu")
    df_menu = pd.DataFrame(menu_json) if menu_json else pd.DataFrame(columns=["item_name", "popularity_sales", "avg_margin", "cluster_label"])
    df_menu["popularity_sales"] = pd.to_numeric(df_menu["popularity_sales"], errors="coerce").fillna(0).astype(int)
    df_menu["avg_margin"] = pd.to_numeric(df_menu["avg_margin"], errors="coerce").fillna(0.0)
    # Estimate prices/costs for simulation if not present
    if "price" not in df_menu.columns:
        df_menu["price"] = df_menu["avg_margin"] * 1.5
        df_menu["cost"] = df_menu["avg_margin"] * 0.5
    else:
        df_menu["price"] = pd.to_numeric(df_menu["price"], errors="coerce").fillna(0.0)
        df_menu["cost"] = pd.to_numeric(df_menu["cost"], errors="coerce").fillna(0.0)
    
    # Read live associations
    assoc_json = get_data("/analytics/associations")
    if assoc_json and assoc_json.get("index"):
        items_list = assoc_json["index"]
        assoc_matrix = assoc_json["data"]
    else:
        items_list, assoc_matrix = [], []

# Style utilities
def style_plotly_fig(fig):
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1e293b"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color="#64748b",
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            zeroline=False,
            color="#64748b",
            tickfont=dict(size=10)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color="#64748b")
        )
    )
    return fig

# Custom HTML table helper
def html_table(headers, rows):
    header_html = "".join([f"<th>{h}</th>" for h in headers])
    rows_html = ""
    for r in rows:
        cells_html = "".join([f"<td>{c}</td>" for c in r])
        rows_html += f"<tr>{cells_html}</tr>"
        
    return f"""
    <table class="premium-table">
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """

# Custom component renderers
def metric_card(label, value, trend_text, trend_direction="up", is_green=False):
    card_class = "card card-green" if is_green else "card"
    label_color = "#a3cfbb" if is_green else "#64748b"
    value_color = "#ffffff" if is_green else "#0f5132"
    badge_bg = "rgba(255, 255, 255, 0.15)" if is_green else ("#e6f4ea" if trend_direction == "up" else "#fce8e6")
    badge_color = "#ffffff" if is_green else ("#137333" if trend_direction == "up" else "#c5221f")
    
    html = f"""
    <div class="{card_class}">
        <div style="font-size: 11px; font-weight: 700; color: {label_color}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">{label}</div>
        <div style="font-size: 30px; font-weight: 800; color: {value_color}; line-height: 1.1; margin-bottom: 12px;">{value}</div>
        <span style="display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 30px; font-size: 11px; font-weight: 600; background-color: {badge_bg}; color: {badge_color};">
            {trend_text}
        </span>
    </div>
    """
    return html

def circular_progress(percentage, title, subtitle):
    radius = 50
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference - (percentage / 100) * circumference
    
    html = f"""
    <div class="card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; min-height: 290px; text-align: center;">
        <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px;">{title}</div>
        <div style="position: relative; width: 130px; height: 130px; margin-bottom: 16px;">
            <svg width="130" height="130" viewBox="0 0 130 130" style="transform: rotate(-90deg);">
                <circle cx="65" cy="65" r="{radius}" fill="transparent" stroke="#e2e8f0" stroke-width="12"></circle>
                <circle cx="65" cy="65" r="{radius}" fill="transparent" stroke="#0f5132" stroke-width="12"
                        stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}" stroke-linecap="round"
                        style="transition: stroke-dashoffset 1s ease-in-out;"></circle>
            </svg>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <span style="font-size: 26px; font-weight: 800; color: #1e293b;">{percentage}%</span>
                <span style="font-size: 10px; font-weight: 600; color: #64748b; margin-top: -2px;">Снижение</span>
            </div>
        </div>
        <div style="font-size: 12px; font-weight: 500; color: #64748b; padding: 0 10px;">{subtitle}</div>
    </div>
    """
    return html

def shift_tracker():
    html = f"""
    <div class="card card-green" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; min-height: 290px; background: linear-gradient(135deg, #09301d 0%, #0f5132 100%);">
        <div>
            <div style="font-size: 11px; font-weight: 700; color: #a3cfbb; text-transform: uppercase; letter-spacing: 0.08em;">Анализ в реальном времени</div>
            <div style="font-size: 16px; font-weight: 700; color: #ffffff; margin-top: 4px;">Смена открыта: Касса #1</div>
        </div>
        <div style="margin: 20px 0;">
            <div style="font-size: 11px; color: #a3cfbb;">Время текущей смены:</div>
            <div style="font-size: 32px; font-weight: 800; color: #ffffff; font-family: monospace; letter-spacing: 0.05em; line-height: 1;">08:14:22</div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <span style="display: inline-flex; align-items: center; justify-content: center; width: 8px; height: 8px; border-radius: 50%; background-color: #2ec4b6; box-shadow: 0 0 8px #2ec4b6;"></span>
            <span style="font-size: 12px; font-weight: 500; color: #a3cfbb;">ИИ мониторинг активен</span>
        </div>
    </div>
    """
    return html

def top_header(title="GastroSense Dashboard"):
    html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background-color: #ffffff; border-radius: 16px; border: 1px solid #f1f5f9; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01);">
        <div>
            <h2 style="font-size: 20px; font-weight: 800; color: #1e293b; margin: 0; line-height: 1.1;">{title}</h2>
            <p style="font-size: 12px; color: #64748b; margin: 4px 0 0 0;">True Burgers • Интеллектуальный дашборд аналитики</p>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="position: relative; cursor: pointer; font-size: 18px;">
                🔔
                <span style="position: absolute; top: -2px; right: -2px; width: 8px; height: 8px; background-color: #ef4444; border-radius: 50%; border: 1.5px solid #ffffff;"></span>
            </div>
            <div style="position: relative; cursor: pointer; font-size: 18px;">
                💬
                <span style="position: absolute; top: -2px; right: -2px; width: 8px; height: 8px; background-color: #3b82f6; border-radius: 50%; border: 1.5px solid #ffffff;"></span>
            </div>
            <div style="height: 24px; width: 1px; background-color: #cbd5e1;"></div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80" alt="Avatar" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover;" />
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 13px; font-weight: 700; color: #1e293b; line-height: 1.2;">Михаил Т.</span>
                    <span style="font-size: 11px; font-weight: 500; color: #64748b;">Владелец бизнеса</span>
                </div>
            </div>
        </div>
    </div>
    """
    return html

def top_menu_list(df_menu):
    if df_menu.empty:
        return "<div class='card'>Нет данных о меню</div>"
    
    top_5 = df_menu.sort_values(by="popularity_sales", ascending=False).head(5)
    
    colors_map = {
        "Stars": {"color": "#0f5132", "bg": "#e6f4ea", "label": "Звезда"},
        "Workhorses": {"color": "#3b82f6", "bg": "#eff6ff", "label": "Лошадка"},
        "Puzzles": {"color": "#f59e0b", "bg": "#fffbeb", "label": "Загадка"},
        "Dogs": {"color": "#ef4444", "bg": "#fef2f2", "label": "Собака"}
    }
    
    list_items = ""
    for _, row in top_5.iterrows():
        c_label = row["cluster_label"]
        info = colors_map.get(c_label, {"color": "#64748b", "bg": "#f1f5f9", "label": "Н/Д"})
        
        list_items += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background-color: #f8fafc; font-size: 14px;">🍔</span>
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 13px; font-weight: 600; color: #1e293b;">{row['item_name']}</span>
                    <span style="font-size: 11px; color: #64748b;">{row['popularity_sales']} шт. продано</span>
                </div>
            </div>
            <span style="padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; background-color: {info['bg']}; color: {info['color']};">
                {info['label']}
            </span>
        </div>
        """
        
    html = f"""
    <div class="card" style="min-height: 290px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0px;">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 14px; font-weight: 700; color: #1e293b;">Популярные позиции</span>
                <span style="font-size: 11px; font-weight: 600; color: #0f5132; cursor: pointer;">Все →</span>
            </div>
            <div style="display: flex; flex-direction: column;">
                {list_items}
            </div>
        </div>
    </div>
    """
    return html

def ai_alerts_list():
    alerts = [
        {"icon": "🥩", "color": "#0f5132", "bg": "#e6f4ea", "text": "Снижение цены на говядину (-8%)", "desc": "Идеальное время для закупки стейков для Бургера True."},
        {"icon": "📈", "color": "#3b82f6", "bg": "#eff6ff", "text": "Пиковый спрос в пятницу", "desc": "Ожидается +25% заказов. Подготовьте дополнительную смену."},
        {"icon": "⚠️", "color": "#f59e0b", "bg": "#fffbeb", "text": "Бургер Веган теряет популярность", "desc": "Спрос упал на 15%. Рекомендуем обновить соус или фото в меню."}
    ]
    
    list_items = ""
    for a in alerts:
        list_items += f"""
        <div style="display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 12px; background-color: #f8fafc; border: 1px solid #f1f5f9; margin-bottom: 10px;">
            <span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 10px; background-color: {a['bg']}; font-size: 16px; flex-shrink: 0;">{a['icon']}</span>
            <div style="display: flex; flex-direction: column;">
                <span style="font-size: 12px; font-weight: 700; color: #1e293b;">{a['text']}</span>
                <span style="font-size: 11px; color: #64748b; line-height: 1.3; margin-top: 2px;">{a['desc']}</span>
            </div>
        </div>
        """
        
    html = f"""
    <div class="card" style="height: 100%; min-height: 380px; margin-bottom: 0px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <span style="font-size: 14px; font-weight: 700; color: #1e293b;">🧠 Уведомления ИИ</span>
            <span style="padding: 2px 6px; border-radius: 10px; font-size: 10px; font-weight: 700; background-color: #f1f5f9; color: #64748b;">3 активных</span>
        </div>
        <div style="display: flex; flex-direction: column;">
            {list_items}
        </div>
    </div>
    """
    return html

def combo_recommendations_list():
    combos = [
        {"title": "Комбо Классика", "items": "Бургер True + Фри + Соус", "uplift": "+12.4% чек", "color": "#0f5132", "bg": "#e6f4ea"},
        {"title": "Сет Крафт & Краб", "items": "Бургер Шеф-Краб + Пиво Крафт", "uplift": "+8.2% маржа", "color": "#3b82f6", "bg": "#eff6ff"},
        {"title": "Здоровый выбор", "items": "Бургер Веган + Кольца + Морс", "uplift": "+15.0% оборот", "color": "#f59e0b", "bg": "#fffbeb"}
    ]
    
    list_items = ""
    for c in combos:
        list_items += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; border-radius: 12px; border: 1px solid #f1f5f9; background-color: #ffffff; margin-bottom: 8px;">
            <div style="display: flex; flex-direction: column;">
                <span style="font-size: 13px; font-weight: 700; color: #1e293b;">{c['title']}</span>
                <span style="font-size: 11px; color: #64748b; margin-top: 2px;">Состав: {c['items']}</span>
            </div>
            <span style="padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; color: {c['color']}; background-color: {c['bg']}; text-align: right; flex-shrink: 0;">
                {c['uplift']}
            </span>
        </div>
        """
        
    html = f"""
    <div class="card" style="min-height: 290px; display: flex; flex-direction: column; justify-content: space-between; background-color: #f8fafc; margin-bottom: 0px;">
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 14px; font-weight: 700; color: #1e293b;">⚡ Рекомендуемые комбо</span>
                <span style="font-size: 11px; font-weight: 600; color: #0f5132; cursor: pointer;">Все связи →</span>
            </div>
            <div style="display: flex; flex-direction: column;">
                {list_items}
            </div>
        </div>
    </div>
    """
    return html

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<h2 style='text-align: center; color: #0f5132; margin-bottom: 0px; font-weight: 800; font-size: 24px;'>🍷 GastroSense</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #64748b; font-size: 11px; margin-top:0px; font-weight: 600; letter-spacing: 0.05em;'>ИНТЕЛЛЕКТУАЛЬНЫЙ АНАЛИЗ РЕСТОРАНА</p>", unsafe_allow_html=True)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Connection Indicator card in sidebar
if is_live:
    conn_status = """
    <div style="background-color: #e6f4ea; border: 1px solid #c4ebd0; border-radius: 12px; padding: 12px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 8px; height: 8px; background-color: #137333; border-radius: 50%;"></span>
            <span style="font-size: 12px; font-weight: 700; color: #137333; text-transform: uppercase;">MySQL Подключена</span>
        </div>
        <p style="font-size: 11px; color: #64748b; margin: 4px 0 0 0; line-height: 1.3;">Аналитика на основе реальных чеков из вашей CRM.</p>
    </div>
    """
else:
    conn_status = """
    <div style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 12px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 8px; height: 8px; background-color: #d97706; border-radius: 50%;"></span>
            <span style="font-size: 12px; font-weight: 700; color: #b45309; text-transform: uppercase;">Демо-Режим (Offline)</span>
        </div>
        <p style="font-size: 11px; color: #64748b; margin: 4px 0 0 0; line-height: 1.3;">Бэкенд оффлайн. Отображаются встроенные демонстрационные данные.</p>
    </div>
    """
st.sidebar.markdown(conn_status, unsafe_allow_html=True)

st.sidebar.markdown("<p style='font-size: 10px; font-weight: 700; color: #94a3b8; letter-spacing: 0.1em; margin-bottom: 8px;'>МЕНЮ</p>", unsafe_allow_html=True)
nav_choice = st.sidebar.radio(
    "Навигация",
    ["📊 Обзор (Overview)", "📈 Прогноз спроса", "🌟 Анализ Меню", "🤝 Кросс-продажи", "⚙️ Импорт & БД"],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)

# Sidebar Card Promo matching Donezo
sidebar_promo = """
<div style="background: linear-gradient(135deg, #09301d 0%, #0f5132 100%); border-radius: 16px; padding: 16px; color: #ffffff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(15, 81, 50, 0.15);">
    <div style="font-size: 13px; font-weight: 700; color: #a3cfbb;">Управление закупками</div>
    <div style="font-size: 15px; font-weight: 800; margin-top: 4px; line-height: 1.2;">Запустить автозакуп с ИИ прогнозом?</div>
    <p style="font-size: 11px; color: #a3cfbb; margin: 8px 0 12px 0; line-height: 1.4;">Интегрируйте поставщиков для автоматического формирования заказов на склад.</p>
    <a href="#" style="display: block; background-color: #ffffff; color: #0f5132; text-align: center; padding: 8px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-decoration: none; transition: transform 0.2s;">Подключить API</a>
</div>
"""
st.sidebar.markdown(sidebar_promo, unsafe_allow_html=True)
st.sidebar.markdown("<p style='color: #94a3b8; font-size: 10px; text-align: center;'>GastroSense Pro &copy; 2026</p>", unsafe_allow_html=True)


# ----------------- MAIN PAGES RENDERING -----------------

# PAGE 1: OVERVIEW (📊 Обзор)
if nav_choice == "📊 Обзор (Overview)":
    st.markdown(top_header("Сводный аналитический дашборд"), unsafe_allow_html=True)
    
    # Rows of Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("Оборот (30 дней)", f"{total_revenue:,.0f} ₽".replace(",", " "), "↑ 12.4% к прош. мес.", "up", is_green=True), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Чеков за период", f"{total_orders:,}".replace(",", " "), "↑ 5.8% к прош. мес.", "up"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Средний чек", f"{avg_check:,.2f} ₽".replace(",", " "), "↑ 3.2% к прош. мес.", "up"), unsafe_allow_html=True)
    with col4:
        # Tomorrow forecast revenue fallback or calculated
        tomorrow_rev = df_fore.iloc[0]["predicted_revenue"] if not df_fore.empty else 415000.0
        st.markdown(metric_card("Прогноз на завтра", f"{tomorrow_rev:,.0f} ₽".replace(",", " "), "Точность прогноза 94.2%", "up"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2: Graph + Alerts
    col_graph, col_alerts = st.columns([13, 7])
    with col_graph:
        st.markdown('<div class="card" style="min-height: 430px; padding: 24px; display: flex; flex-direction: column;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">Динамика выручки и прогноз спроса (7 дней)</div>', unsafe_allow_html=True)
        
        if not df_fore.empty and not df_hist.empty:
            fig = go.Figure()
            # History line
            fig.add_trace(go.Scatter(
                x=df_hist["date"], y=df_hist["revenue"],
                name="История (Факт)",
                line=dict(color="#64748b", width=3, shape="spline"),
                mode="lines"
            ))
            # Connecting link
            conn_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig.add_trace(go.Scatter(
                x=conn_df["date"], y=conn_df["revenue"] if "revenue" in conn_df else conn_df["predicted_revenue"],
                showlegend=False,
                line=dict(color="#0f5132", width=3, dash="dot", shape="spline")
            ))
            # Forecast Line
            fig.add_trace(go.Scatter(
                x=df_fore["date"], y=df_fore["predicted_revenue"],
                name="Прогноз спроса ИИ",
                line=dict(color="#0f5132", width=3, shape="spline"),
                marker=dict(size=6, color="#0f5132", symbol="circle"),
                mode="lines+markers"
            ))
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
                y=df_fore["upper_bound_revenue"].tolist() + df_fore["lower_bound_revenue"].tolist()[::-1],
                fill="toself",
                fillcolor="rgba(15, 81, 50, 0.05)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="Доверительный интервал (95%)"
            ))
            style_plotly_fig(fig)
            fig.update_layout(height=310, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для графика.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_alerts:
        st.markdown(ai_alerts_list(), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 3: Lists & Gauges
    col_menu, col_combos, col_status = st.columns(3)
    with col_menu:
        st.markdown(top_menu_list(df_menu), unsafe_allow_html=True)
    with col_combos:
        st.markdown(combo_recommendations_list(), unsafe_allow_html=True)
    with col_status:
        # Show a sub-column to render progress and shift side-by-side or stacked
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.markdown(circular_progress(41, "Списание сырья", "Экономия запускщика за счет точности ИИ"), unsafe_allow_html=True)
        with sub_col2:
            st.markdown(shift_tracker(), unsafe_allow_html=True)


# PAGE 2: DEMAND FORECAST (📈 Прогноз спроса)
elif nav_choice == "📈 Прогноз спроса":
    st.markdown(top_header("Машинное прогнозирование спроса"), unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    total_pred_rev = df_fore["predicted_revenue"].sum() if not df_fore.empty else 0.0
    with col1:
        st.markdown(metric_card("Суммарный прогноз (7 дней)", f"{total_pred_rev:,.0f} ₽".replace(",", " "), "Период: следующие 7 дней", "up", is_green=True), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Ожидаемое число заказов", f"{df_fore['predicted_orders'].sum() if not df_fore.empty else 0:,.0f} зак.".replace(",", " "), "В среднем: ~70-90 чеков в день", "up"), unsafe_allow_html=True)
    with col3:
        opt_savings = total_pred_rev * 0.124 if not df_fore.empty else 0.0
        st.markdown(metric_card("Снижение издержек склада", f"- {opt_savings:,.0f} ₽".replace(",", " "), "За счет точной закупки сырья", "down"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main graph card
    st.markdown('<div class="card" style="padding: 24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">Интерактивный график 7-дневного прогнозирования (LightGBM)</div>', unsafe_allow_html=True)
    
    if not df_fore.empty:
        fig = go.Figure()
        # History
        if not df_hist.empty:
            fig.add_trace(go.Scatter(
                x=df_hist["date"], y=df_hist["revenue"],
                name="Факт (История)",
                line=dict(color="#94a3b8", width=2, shape="spline"),
                mode="lines"
            ))
            # Connecting dash link
            conn_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig.add_trace(go.Scatter(
                x=conn_df["date"], y=conn_df["revenue"] if "revenue" in conn_df else conn_df["predicted_revenue"],
                showlegend=False,
                line=dict(color="#0f5132", width=2, dash="dot", shape="spline")
            ))
        # Forecast
        fig.add_trace(go.Scatter(
            x=df_fore["date"], y=df_fore["predicted_revenue"],
            name="Прогноз выручки ИИ",
            line=dict(color="#0f5132", width=3, shape="spline"),
            marker=dict(size=8, color="#0f5132"),
            mode="lines+markers"
        ))
        # Confidence Band
        fig.add_trace(go.Scatter(
            x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
            y=df_fore["upper_bound_revenue"].tolist() + df_fore["lower_bound_revenue"].tolist()[::-1],
            fill="toself",
            fillcolor="rgba(15, 81, 50, 0.05)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="95% Доверительный диапазон"
        ))
        style_plotly_fig(fig)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Данные недоступны.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detailed Data table + Day of week statistics
    col_table, col_weekdays = st.columns([11, 9])
    
    with col_table:
        st.markdown('<div class="card" style="min-height: 400px; display: flex; flex-direction: column; justify-content: space-between;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">Таблица прогнозируемых показателей</div>', unsafe_allow_html=True)
        
        if not df_fore.empty:
            headers = ["Дата", "Прогноз выручки", "Заказов (прогноз)", "Нижний порог", "Верхний порог"]
            rows = []
            for _, r in df_fore.iterrows():
                date_str = r["date"].strftime("%d.%m.%Y (%a)") if isinstance(r["date"], (date, datetime)) else str(r["date"])
                rows.append([
                    date_str,
                    f"{r['predicted_revenue']:,.0f} ₽".replace(",", " "),
                    f"{r['predicted_orders']:.0f} шт.",
                    f"{r['lower_bound_revenue']:,.0f} ₽".replace(",", " "),
                    f"{r['upper_bound_revenue']:,.0f} ₽".replace(",", " ")
                ])
            st.markdown(html_table(headers, rows), unsafe_allow_html=True)
        else:
            st.info("Нет данных прогноза.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_weekdays:
        st.markdown('<div class="card" style="min-height: 400px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">Распределение спроса по дням недели (Среднее)</div>', unsafe_allow_html=True)
        
        # Calculate day of week average from history if available
        if not df_hist.empty:
            df_h = df_hist.copy()
            df_h["weekday"] = df_h["date"].dt.day_name()
            # Sort weekdays
            w_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            w_ru = {"Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср", "Thursday": "Чт", "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"}
            
            df_w = df_h.groupby("weekday")["revenue"].mean().reindex(w_order).reset_index()
            df_w["weekday_ru"] = df_w["weekday"].map(w_ru)
            
            fig_w = px.bar(
                df_w, x="weekday_ru", y="revenue",
                color_discrete_sequence=["#0f5132"],
                labels={"weekday_ru": "День недели", "revenue": "Средняя выручка (₽)"}
            )
            style_plotly_fig(fig_w)
            fig_w.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
            fig_w.update_traces(marker=dict(cornerradius=8))  # Rounded top bars
            st.plotly_chart(fig_w, use_container_width=True)
        else:
            st.info("Нет данных о днях недели.")
        st.markdown('</div>', unsafe_allow_html=True)


# PAGE 3: MENU ENGINEERING (🌟 Анализ Меню)
elif nav_choice == "🌟 Анализ Меню":
    st.markdown(top_header("Smith-Shostack Анализ & Квантование Меню"), unsafe_allow_html=True)
    
    # Metrics count for clusters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        stars_cnt = len(df_menu[df_menu["cluster_label"] == "Stars"]) if not df_menu.empty else 0
        st.markdown(metric_card("🌟 Звезды (Stars)", f"{stars_cnt} блюд", "Высокий спрос & маржа", "up"), unsafe_allow_html=True)
    with col2:
        horses_cnt = len(df_menu[df_menu["cluster_label"] == "Workhorses"]) if not df_menu.empty else 0
        st.markdown(metric_card("🐎 Рабочие лошадки", f"{horses_cnt} блюд", "Высокий спрос, малая маржа", "up"), unsafe_allow_html=True)
    with col3:
        puzzles_cnt = len(df_menu[df_menu["cluster_label"] == "Puzzles"]) if not df_menu.empty else 0
        st.markdown(metric_card("❓ Загадки (Puzzles)", f"{puzzles_cnt} блюд", "Малый спрос, высокая маржа", "up"), unsafe_allow_html=True)
    with col4:
        dogs_cnt = len(df_menu[df_menu["cluster_label"] == "Dogs"]) if not df_menu.empty else 0
        st.markdown(metric_card("🐕 Собаки (Dogs)", f"{dogs_cnt} блюд", "Низкий спрос & маржа", "down"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chart row + Simulator
    col_scatter, col_sim = st.columns([12, 8])
    
    with col_scatter:
        st.markdown('<div class="card" style="min-height: 520px; display: flex; flex-direction: column; justify-content: space-between;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">Карта классификации блюд меню (K-Means Clustering)</div>', unsafe_allow_html=True)
        
        if not df_menu.empty:
            median_pop = df_menu["popularity_sales"].median()
            median_margin = df_menu["avg_margin"].median()
            
            colors_map = {
                "Stars": "#0f5132",
                "Workhorses": "#3b82f6",
                "Puzzles": "#f59e0b",
                "Dogs": "#ef4444"
            }
            
            fig = px.scatter(
                df_menu, x="popularity_sales", y="avg_margin",
                color="cluster_label", text="item_name",
                color_discrete_map=colors_map,
                labels={"popularity_sales": "Продажи за период (шт)", "avg_margin": "Средняя маржа (₽)"}
            )
            fig.add_vline(x=median_pop, line_dash="dash", line_color="#cbd5e1")
            fig.add_hline(y=median_margin, line_dash="dash", line_color="#cbd5e1")
            
            fig.update_traces(
                marker=dict(size=14, line=dict(width=1, color="#ffffff")),
                textposition="top center",
                textfont=dict(color="#1e293b", size=10)
            )
            style_plotly_fig(fig)
            fig.update_layout(height=410, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для отображения.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_sim:
        st.markdown('<div class="card" style="min-height: 520px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">📈 ИИ-Симулятор ценообразования</div>', unsafe_allow_html=True)
        st.write("Выберите позицию из меню, чтобы спрогнозировать изменение маржинальности и спроса при изменении цены:")
        
        if not df_menu.empty:
            items_list_select = df_menu["item_name"].tolist()
            selected_item = st.selectbox("Позиция меню для симуляции", items_list_select)
            
            # Find record
            item_row = df_menu[df_menu["item_name"] == selected_item].iloc[0]
            curr_price = float(item_row["price"])
            curr_cost = float(item_row["cost"])
            curr_sales = int(item_row["popularity_sales"])
            curr_margin = float(item_row["avg_margin"])
            curr_cluster = item_row["cluster_label"]
            
            markup_change = st.slider("Изменение цены (%)", -30, 50, 0, step=5)
            
            # Simple price elasticity simulation (elasticity for fast food burgers ~ -1.5)
            elasticity = -1.5
            new_price = curr_price * (1 + markup_change / 100)
            new_margin = new_price - curr_cost
            sales_change_pct = (markup_change * elasticity)
            new_sales = max(10, int(curr_sales * (1 + sales_change_pct / 100)))
            
            curr_total_profit = curr_margin * curr_sales
            new_total_profit = new_margin * new_sales
            profit_diff = new_total_profit - curr_total_profit
            profit_diff_pct = (profit_diff / curr_total_profit * 100) if curr_total_profit > 0 else 0.0
            
            # Display comparison cards
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; margin: 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #1e293b;">{selected_item}</span>
                    <span style="font-size: 11px; font-weight: 700; color: #64748b;">Текущий класс: {curr_cluster}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Текущая цена</div>
                        <div style="font-size: 16px; font-weight: 700; color: #1e293b;">{curr_price:,.0f} ₽</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Новая цена</div>
                        <div style="font-size: 16px; font-weight: 700; color: #0f5132;">{new_price:,.0f} ₽</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Объем продаж (мес)</div>
                        <div style="font-size: 16px; font-weight: 700; color: #1e293b;">{curr_sales} шт.</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Ожидаемый объем</div>
                        <div style="font-size: 16px; font-weight: 700; color: #0f5132;">{new_sales} шт. ({sales_change_pct:+.1f}%)</div>
                    </div>
                </div>
                <div style="border-top: 1px dashed #cbd5e1; padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Прогноз изменения прибыли</div>
                        <div style="font-size: 20px; font-weight: 800; color: {'#0f5132' if profit_diff >= 0 else '#ef4444'};">
                            {profit_diff:+,.0f} ₽ ({profit_diff_pct:+.1f}%)
                        </div>
                    </div>
                    <span style="font-size: 28px;">{'📈' if profit_diff >= 0 else '📉'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Recommendation text based on outcome
            if profit_diff > 0:
                st.success(f"💡 ИИ одобряет: повышение цены увеличит совокупную маржинальную прибыль, несмотря на падение спроса на {abs(sales_change_pct):.1f}%.")
            else:
                st.error(f"⚠️ ИИ предупреждает: падение спроса из-за эластичности перекроет выгоду от повышенной цены. Прибыль снизится.")
        else:
            st.info("Нет данных о меню.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Detailed HTML table of all menu items
    st.markdown('<div class="card" style="padding: 24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">Полный список блюд с классификацией ИИ</div>', unsafe_allow_html=True)
    
    if not df_menu.empty:
        headers = ["Название позиции", "Продажи (шт)", "Цена", "Себестоимость (Фуд кост)", "Единичная маржа", "Класс эффективности"]
        rows = []
        
        colors_map = {
            "Stars": {"color": "#0f5132", "bg": "#e6f4ea", "label": "Звезда"},
            "Workhorses": {"color": "#3b82f6", "bg": "#eff6ff", "label": "Лошадка"},
            "Puzzles": {"color": "#f59e0b", "bg": "#fffbeb", "label": "Загадка"},
            "Dogs": {"color": "#ef4444", "bg": "#fef2f2", "label": "Собака"}
        }
        
        for _, r in df_menu.iterrows():
            c_info = colors_map.get(r["cluster_label"], {"color": "#64748b", "bg": "#f1f5f9", "label": "Н/Д"})
            badge_html = f'<span style="padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; background-color: {c_info["bg"]}; color: {c_info["color"]};">{c_info["label"]}</span>'
            
            rows.append([
                r["item_name"],
                f"{r['popularity_sales']:,}".replace(",", " "),
                f"{r['price']:,.1f} ₽".replace(",", " "),
                f"{r['cost']:,.1f} ₽".replace(",", " "),
                f"{r['avg_margin']:,.1f} ₽".replace(",", " "),
                badge_html
            ])
        st.markdown(html_table(headers, rows), unsafe_allow_html=True)
    else:
        st.info("Нет данных о меню.")
    st.markdown('</div>', unsafe_allow_html=True)


# PAGE 4: CROSS-SALES (🤝 Кросс-продажи)
elif nav_choice == "🤝 Кросс-продажи":
    st.markdown(top_header("Анализ рыночной корзины & Кросс-продажи"), unsafe_allow_html=True)
    
    col_heatmap, col_details = st.columns([11, 9])
    
    with col_heatmap:
        st.markdown('<div class="card" style="min-height: 520px; display: flex; flex-direction: column; justify-content: space-between;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px;">Вероятности совместных покупок P(B | A)</div>', unsafe_allow_html=True)
        
        if len(items_list) > 1 and len(assoc_matrix) > 0:
            fig = go.Figure(data=go.Heatmap(
                z=assoc_matrix, x=items_list, y=items_list,
                colorscale=[[0, "#f8fafc"], [0.4, "#e0f2fe"], [1, "#0f5132"]],
                hoverongaps=False,
                text=[[f"P({b} | {a}) = {val:.1%}" for b, val in zip(items_list, row)] for a, row in zip(items_list, assoc_matrix)],
                hoverinfo="text"
            ))
            style_plotly_fig(fig)
            fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(tickangle=-45))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных для построения тепловой карты.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_details:
        st.markdown('<div class="card" style="min-height: 520px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🔍 Интерактивный поиск сопутствующих товаров</div>', unsafe_allow_html=True)
        st.write("Выберите базовое блюдо (А), чтобы увидеть, с какой вероятностью покупают сопутствующие позиции (B) в одном чеке:")
        
        if len(items_list) > 1:
            base_item = st.selectbox("Базовое блюдо (A)", items_list)
            
            # Find index of selected item
            idx = items_list.index(base_item)
            probs = assoc_matrix[idx]
            
            # Map items and their probabilities
            pairs = []
            for i, p in enumerate(probs):
                if items_list[i] != base_item: # omit self co-occurrence
                    pairs.append((items_list[i], p))
                    
            # Sort by probability
            pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:5]
            
            # Draw beautiful visual bars
            bars_html = ""
            for item, p in pairs:
                p_pct = p * 100
                bars_html += f"""
                <div style="margin-bottom: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: #1e293b;">
                        <span>{item}</span>
                        <span style="color: #0f5132; font-weight: 700;">{p_pct:.1f}% чеков</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: {p_pct}%; background-color: #0f5132;"></div>
                    </div>
                </div>
                """
            st.markdown(f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin: 16px 0;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
                    Сопутствующие товары для: {base_item}
                </div>
                {bars_html}
            </div>
            """, unsafe_allow_html=True)
            
            # Business interpretation
            top_bundle = pairs[0][0]
            st.info(f"💡 Идея для маркетинга: Внедрите комбо-набор [{base_item} + {top_bundle}] или настройте кассовые подсказки, предлагая {top_bundle} при покупке {base_item}.")
        else:
            st.info("Недостаточно данных для поиска ассоциаций.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Combo Creator Section
    st.markdown('<div class="card" style="padding: 24px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🚀 Конструктор умных комбо-наборов</div>', unsafe_allow_html=True)
    
    col_inputs, col_preview = st.columns([10, 10])
    
    with col_inputs:
        combo_name = st.text_input("Название комбо-набора", "Комбо Голодный Шеф")
        
        # Populate selector if menu is loaded
        if not df_menu.empty:
            menu_options = df_menu["item_name"].tolist()
            c_item1 = st.selectbox("Первое блюдо", menu_options, index=0)
            c_item2 = st.selectbox("Второе блюдо", menu_options, index=1 if len(menu_options) > 1 else 0)
            c_item3 = st.selectbox("Напиток/Соус", menu_options, index=5 if len(menu_options) > 5 else 0)
            
            # Get original prices
            p1 = float(df_menu[df_menu["item_name"] == c_item1].iloc[0]["price"])
            p2 = float(df_menu[df_menu["item_name"] == c_item2].iloc[0]["price"])
            p3 = float(df_menu[df_menu["item_name"] == c_item3].iloc[0]["price"])
            
            p_total_sum = p1 + p2 + p3
            
            # Input discount
            combo_discount_pct = st.slider("Скидка на комбо (%)", 0, 30, 10, step=5)
            combo_price = p_total_sum * (1 - combo_discount_pct / 100)
            
    with col_preview:
        if not df_menu.empty:
            # Simple simulation: Estimate probability of joint purchase
            prob12, prob23 = 0.1, 0.1
            if len(items_list) > 0:
                try:
                    if c_item1 in items_list and c_item2 in items_list:
                        prob12 = assoc_matrix[items_list.index(c_item1)][items_list.index(c_item2)]
                    if c_item2 in items_list and c_item3 in items_list:
                        prob23 = assoc_matrix[items_list.index(c_item2)][items_list.index(c_item3)]
                except Exception:
                    pass
            
            # Estimate joint bundle conversion probability
            joint_prob = max(prob12, prob23) * 1.25 # Discount factor raises conversion
            estimated_uplift = combo_price * joint_prob * 12 # hypothetical 12 transactions per day
            
            st.markdown(f"""
            <div style="background-color: #0f5132; color: #ffffff; border-radius: 14px; padding: 20px; height: 100%;">
                <div style="font-size: 11px; font-weight: 700; color: #a3cfbb; text-transform: uppercase;">Карточка комбо-акции</div>
                <h3 style="margin: 8px 0 0 0; color: #ffffff; font-weight: 800;">{combo_name}</h3>
                <div style="font-size: 12px; color: #a3cfbb; margin-top: 4px;">{c_item1} + {c_item2} + {c_item3}</div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0;">
                    <div>
                        <div style="font-size: 10px; color: #a3cfbb; text-transform: uppercase;">Сумма по отдельности</div>
                        <div style="font-size: 18px; font-weight: 700; text-decoration: line-through; color: #cbd5e1;">{p_total_sum:,.0f} ₽</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #a3cfbb; text-transform: uppercase;">Стоимость комбо ({combo_discount_pct}% скидка)</div>
                        <div style="font-size: 18px; font-weight: 800; color: #2ec4b6;">{combo_price:,.0f} ₽</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #a3cfbb; text-transform: uppercase;">Вероятность покупки</div>
                        <div style="font-size: 18px; font-weight: 700; color: #ffffff;">{joint_prob:.1%}</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; color: #a3cfbb; text-transform: uppercase;">Прогноз прироста выручки</div>
                        <div style="font-size: 18px; font-weight: 700; color: #ffffff;">+{estimated_uplift:,.0f} ₽ / мес.</div>
                    </div>
                </div>
                
                <div style="font-size: 11px; color: #a3cfbb; line-height: 1.4; border-top: 1px dashed rgba(255,255,255,0.2); padding-top: 10px;">
                    Высокая связность между {c_item1} и {c_item2} гарантирует, что клиенты будут охотно выбирать комбо-набор. Рекомендуется транслировать комбо на кассовом дисплее и в меню.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 Зарегистрировать акцию в POS-системе", use_container_width=True):
                st.balloons()
                st.success("Успешно отправлено в POS-систему (Имитация)!")
        else:
            st.info("Нет данных о меню.")
    st.markdown('</div>', unsafe_allow_html=True)


# PAGE 5: IMPORT & DB CONFIG (⚙️ Импорт & БД)
elif nav_choice == "⚙️ Импорт & БД":
    st.markdown(top_header("Управление данными & Интеграции"), unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('<div class="card" style="min-height: 480px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">📥 Загрузить файлы чеков (iiko / r-keeper / Excel / CSV)</div>', unsafe_allow_html=True)
        st.write("Вы можете загрузить сырой файл экспорта чеков из любой ресторанной CRM. Наш ИИ автоматически распознает заголовки колонок:")
        
        uploaded_file = st.file_uploader("Выберите файл в формате CSV или Excel", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            # Read first few lines to show preview
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_preview = pd.read_csv(uploaded_file, nrows=5)
                else:
                    df_preview = pd.read_excel(uploaded_file, nrows=5)
                
                st.markdown("<p style='font-size: 12px; font-weight: 700; color:#1e293b; margin-top:12px;'>Предпросмотр данных:</p>", unsafe_allow_html=True)
                st.dataframe(df_preview, use_container_width=True)
                
                st.success("Файл успешно прочитан. Нажмите обработать, чтобы импортировать данные чеков в MySQL и пересчитать ML-модели.")
                
                if st.button("📤 Обработать и загрузить чеки"):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    with st.spinner("Загрузка, парсинг чеков, нормализация БД и обучение LightGBM / K-Means..."):
                        res = post_data("/upload/checks", files=files)
                        if res.get("success"):
                            st.success(f"Успешно импортировано! Обработано заказов: {res.get('orders_processed', 0)}, позиций: {res.get('items_processed', 0)}")
                            st.rerun()
                        else:
                            st.error(f"Ошибка при обработке: {res.get('message')}")
            except Exception as e:
                st.error(f"Не удалось прочитать файл: {str(e)}")
        else:
            st.info("Пожалуйста, загрузите файл чеков в поле выше.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown('<div class="card" style="min-height: 480px; display:flex; flex-direction:column; justify-content:space-between;">', unsafe_allow_html=True)
        
        # Connection status block
        status_html = ""
        if is_live:
            status_html = """
            <div>
                <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🟢 База данных: MySQL Активна</div>
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                        <span style="color:#64748b;">Адрес сервера:</span><span style="font-weight:700; color:#1e293b;">restaurant_analytics_db:3306</span>
                        <span style="color:#64748b;">База данных:</span><span style="font-weight:700; color:#1e293b;">restaurant_analytics</span>
                        <span style="color:#64748b;">Таблица заказов:</span><span style="font-weight:700; color:#1e293b;">orders (активна)</span>
                        <span style="color:#64748b;">Таблица блюд:</span><span style="font-weight:700; color:#1e293b;">order_items (активна)</span>
                    </div>
                </div>
                <p style="font-size: 12px; color: #64748b; line-height: 1.4;">Все операции считываются в режиме реального времени. ML-прогнозы (LightGBM) перерассчитываются при каждом импорте данных.</p>
            </div>
            """
        else:
            status_html = """
            <div>
                <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🟡 База данных: Демо-Режим (MySQL Недоступна)</div>
                <div style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; margin-bottom: 16px; color:#b45309;">
                    <p style="font-size: 12px; margin: 0; line-height: 1.4;">Система работает на высокодетализированных статических демонстрационных данных бургер-бара True Burgers. Для перехода в онлайн-режим необходимо запустить контейнеры с базой данных.</p>
                </div>
                <p style="font-size: 12px; color: #64748b;">Для развертывания демонстрационной базы данных в 1 клик, пожалуйста, нажмите кнопку ниже. Это автоматически создаст таблицы в MySQL и наполнит их реалистичными чеками за последние 180 дней.</p>
            </div>
            """
            
        st.markdown(status_html, unsafe_allow_html=True)
        
        # Demo database seeding controls
        if not is_live:
            st.markdown("<p style='font-size: 12px; font-weight: 700; color:#1e293b;'>Развернуть Демо-БД в MySQL:</p>", unsafe_allow_html=True)
            if st.button("🚀 Создать и наполнить БД (1 клик)"):
                with st.spinner("Создание таблиц MySQL и наполнение чеками за 180 дней..."):
                    res = post_data("/upload/seed-demo")
                    if res.get("success"):
                        st.success("Успешно создано и наполнено! Пожалуйста, обновите страницу.")
                        st.rerun()
                    else:
                        st.error(f"Не удалось подключиться к MySQL. Убедитесь, что docker-compose запущен. Ошибка: {res.get('message')}")
        else:
            st.markdown("<p style='font-size: 12px; font-weight: 700; color:#1e293b;'>Очистить или сбросить БД:</p>", unsafe_allow_html=True)
            if st.button("🗑️ Сбросить и наполнить заново"):
                with st.spinner("Пересоздание таблиц MySQL..."):
                    res = post_data("/upload/seed-demo")
                    if res.get("success"):
                        st.success("БД успешно сброшена и наполнена чистыми демо-данными за 180 дней.")
                        st.rerun()
                    else:
                        st.error("Ошибка при сбросе БД.")
                        
        st.markdown('</div>', unsafe_allow_html=True)
