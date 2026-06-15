import sys
from pathlib import Path

# Гарантируем импорт локальных модулей при запуске из корня репо или PyCharm
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
import numpy as np
from datetime import datetime, date, timedelta

from portfolio_config import CONTACT_NAME, CONTACT_TELEGRAM, CONTACT_EMAIL
from portfolio_ui import render_hero_banner, render_services_block
from pdf_report import generate_report_pdf

# Page configuration for a wide, premium feel
st.set_page_config(
    page_title="GastroSense | Аналитика для кофеен — портфолио",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium dark theme styling
st.html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles - Force dark background on all wrappers */
    html, body, .stApp, div[data-testid="stAppViewContainer"], section.main, [data-testid="stHeader"], [data-testid="stAppViewBlockContainer"] {
        background-color: #0b0f19 !important;
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Global Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Base paragraph and markdown styling - no important to let inline styles override */
    p, [data-testid="stMarkdownContainer"] p {
        color: #cbd5e1;
        font-size: 14px;
        line-height: 1.6;
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
    
    /* Custom Header Navigation Bar */
    .top-nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: transparent;
        padding: 12px 0 24px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid #1e293b;
    }
    .logo-area {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-text {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    /* Vertically center elements inside the header columns */
    div[data-testid="stHorizontalBlock"]:has(.header-column-marker) div[data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    /* Equal height columns layout to align charts and cards horizontally */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        align-items: stretch !important;
    }
    div[data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stColumn"] > div {
        flex-grow: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 8px;
    }
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.3px;
    }

    /* Target all st.container(border=True) to style them as sleek cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161b26 !important;
        border: 1px solid #2d3748 !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        
        /* Force container to stretch and justify its child contents */
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }
    
    /* Support for highlighted container via :has() */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) {
        background: linear-gradient(135deg, #1e1b4b 0%, #111827 100%) !important;
        border: 1px solid #4f46e5 !important;
    }
    
    /* Metrics text color overrides */
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-label {
        color: #94a3b8 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-value {
        color: #ffffff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] .metric-subtext {
        color: #64748b !important;
    }
    
    /* Highlighted metrics text color overrides */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-label {
        color: #c7d2fe !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-value {
        color: #ffffff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .metric-subtext {
        color: #818cf8 !important;
    }
    
    /* Interactive combo recommendation card */
    .combo-card {
        background-color: rgba(99, 102, 241, 0.05) !important;
        border: 1px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-top: 16px !important;
        transition: all 0.2s ease !important;
    }
    .combo-card:hover {
        border-color: #6366f1 !important;
        background-color: rgba(99, 102, 241, 0.1) !important;
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
        background-color: #1e293b !important;
        color: #94a3b8 !important;
        font-weight: 700 !important;
        padding: 14px 16px !important;
        border-bottom: 1px solid #2d3748 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    .premium-table td {
        padding: 14px 16px !important;
        border-bottom: 1px solid #1e293b !important;
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    .premium-table tr:hover {
        background-color: #1e293b;
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
        background-color: rgba(99, 102, 241, 0.15) !important;
        color: #818cf8 !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }
    .badge-workhorse {
        background-color: rgba(59, 130, 246, 0.15) !important;
        color: #60a5fa !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
    }
    .badge-puzzle {
        background-color: rgba(148, 163, 184, 0.15) !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
    }
    .badge-dog {
        background-color: rgba(239, 68, 68, 0.15) !important;
        color: #f87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }
    
    /* Clean Progress Bars */
    .progress-bar-container {
        width: 100% !important;
        background-color: #1e293b !important;
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
        background-color: #161b26 !important;
        border: 1px solid #222b3c !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #f1f5f9 !important;
    }
    
    /* Popover body styling */
    div[data-testid="stPopoverBody"] {
        background-color: #161b26 !important;
        border: 1px solid #222b3c !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4) !important;
        color: #f1f5f9 !important;
    }
    
    /* Popover Button override */
    button[data-testid="stPopoverButton"] {
        background-color: #161b26 !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    button[data-testid="stPopoverButton"]:hover {
        border-color: #3b82f6 !important;
        background-color: #1e293b !important;
    }
    
    /* Dropdown Listbox options */
    ul[data-baseweb="menu"] {
        background-color: #161b26 !important;
        border: 1px solid #222b3c !important;
    }
    li[role="option"] {
        background-color: #161b26 !important;
        color: #f1f5f9 !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    /* Slider overrides */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #3b82f6 !important;
        border: 2px solid #ffffff !important;
    }
    div[data-testid="stSlider"] div[data-testid="stSliderTrack"] > div {
        background: linear-gradient(90deg, #1e293b 0%, #3b82f6 100%) !important;
    }
    
    /* File Uploader override to look compact */
    div[data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #161b26 !important;
        border: 1px dashed #334155 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    div[data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p {
        color: #94a3b8 !important;
    }
    
    /* Button Styles */
    button[kind="secondary"] {
        background-color: #161b26 !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background-color: #1e293b !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    button[kind="secondary"] span, button[kind="secondary"] p {
        color: #f1f5f9 !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 18px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    button[kind="primary"] span, button[kind="primary"] p {
        color: #ffffff !important;
    }
    
    /* Streamlit Alert message boxes */
    div[data-testid="stNotification"] {
        background-color: #161b26 !important;
        border: 1px solid #222b3c !important;
        border-radius: 12px !important;
    }
    div[data-testid="stNotification"] p, div[data-testid="stNotification"] span {
        color: #f1f5f9 !important;
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
        color: #34d399 !important;
    }
    .trend-down {
        color: #f87171 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .trend-up {
        color: #34d399 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) .trend-down {
        color: #f87171 !important;
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

# ----------------- PRESET DATASETS FOR SIMULATION -----------------
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
        }
    }
}
stats_data = get_data("/analytics/stats")
is_live = stats_data is not None and stats_data.get("total_orders", 0) > 0

# Render Top Navigation Bar
col_logo, col_crm, col_reset = st.columns([7, 1.5, 1.5])

with col_logo:
    st.html("""
    <div class="logo-area" style="padding: 6px 0;">
        <div class="header-column-marker"></div>
        <span class="logo-text" style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">☕ GastroSense <span style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Analytics</span></span>
    </div>
    """)

with col_crm:
    with st.popover("Пример импорта", use_container_width=True):
        st.html("<p style='font-size:11px; color:#cbd5e1; margin-bottom:8px; line-height:1.4;'>Демо: как я работаю с выгрузкой чеков из iiko / R-Keeper. Шаблон формата:</p>")
        sample_csv_template = (
            "Номер чека,Дата и время,Наименование,Цена,Количество,Категория\n"
            "10001,2026-06-15 09:12:00,Капуччино 0.3,180,1,Coffee\n"
            "10001,2026-06-15 09:12:00,Круассан классик,150,1,Bakery\n"
            "10002,2026-06-15 09:15:00,Латте Макиато,220,1,Coffee\n"
            "10003,2026-06-15 09:40:00,Эспрессо,120,1,Coffee\n"
            "10003,2026-06-15 09:40:00,Миндальный круассан,240,1,Bakery\n"
            "10004,2026-06-15 10:10:00,Капуччино 0.3,180,2,Coffee\n"
            "10004,2026-06-15 10:10:00,Овсяное печенье,90,1,Bakery\n"
            "10005,2026-06-15 10:30:00,Авокадо тост,350,1,Food\n"
            "10005,2026-06-15 10:30:00,Фильтр-кофе,150,1,Coffee\n"
        )
        st.download_button(
            label="📥 Скачать шаблон (CSV)",
            data=sample_csv_template,
            file_name="gastrosense_sample_checks.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_sample_csv_template"
        )
        st.html("<hr style='margin: 8px 0; border: 0; border-top: 1px solid #2d3748;'>")
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

st.html('<hr style="margin-top: 12px; margin-bottom: 24px; border: 0; border-top: 1px solid #1e293b;">')

st.html(render_hero_banner())
st.html(render_services_block())

# ----------------- DATA PREPARATION -----------------
preset_options = list(PRESET_DATASETS.keys())
if is_live:
    preset_options.append("Загруженная база данных (Реальная БД)")

col_sel_label, col_sel_widget = st.columns([3.5, 6.5])
with col_sel_label:
    st.html("""
    <div style="display: flex; align-items: center; height: 100%; padding-top: 6px;">
        <span style="font-size: 14px; font-weight: 700; color: #94a3b8; letter-spacing: -0.2px;">🏬 Пример заведения (демо-данные):</span>
    </div>
    """)
with col_sel_widget:
    _coffee_idx = next(
        (i for i, n in enumerate(preset_options) if "Coffee" in n or "Кофейня" in n),
        0,
    )
    preset_name = st.selectbox(
        label="🏬 Пример заведения (демо-данные):",
        options=preset_options,
        index=len(preset_options) - 1 if is_live else _coffee_idx,
        label_visibility="collapsed",
        key="selected_preset_profile",
    )

# ----------------- DATA PREPARATION -----------------
if preset_name in PRESET_DATASETS:
    # Load from selected Mock Preset
    preset_data = PRESET_DATASETS[preset_name]
    
    total_revenue = preset_data["stats"]["total_revenue"]
    total_orders = preset_data["stats"]["total_orders"]
    avg_check = preset_data["stats"]["avg_check"]
    total_items_sold = preset_data["stats"]["total_items_sold"]
    avg_items_per_check = preset_data["stats"]["avg_items_per_check"]
    
    # 2. Daily History
    base_date = datetime.now() - timedelta(days=21)
    hist_dates = [base_date + timedelta(days=i) for i in range(21)]
    hist_revenue = preset_data["hist_revenue"]
    df_hist = pd.DataFrame({
        "date": hist_dates, 
        "revenue": hist_revenue,
        "orders_count": [int(rev / avg_check) for rev in hist_revenue]
    })
    
    # 3. Forecast
    forecast_dates = [datetime.now() + timedelta(days=i) for i in range(1, 8)]
    predicted_rev = preset_data["pred_revenue"]
    lower_bound = [r * 0.90 for r in predicted_rev]
    upper_bound = [r * 1.10 for r in predicted_rev]
    df_fore = pd.DataFrame({
        "date": forecast_dates,
        "predicted_revenue": predicted_rev,
        "predicted_orders": preset_data["pred_orders"],
        "lower_bound_revenue": lower_bound,
        "upper_bound_revenue": upper_bound
    })
    
    # 4. Menu Analysis
    df_menu = pd.DataFrame(preset_data["menu"])
    
    # 5. Associations
    items_list = preset_data["items_list"]
    assoc_matrix = preset_data["assoc_matrix"]
    offline_assoc_lookup = preset_data["assoc_lookup"]
    simulator_config = preset_data["simulator"]
else:
    # Load from Real/Live Database via API
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

    # Fallbacks for live DB mode
    offline_assoc_lookup = PRESET_DATASETS["Бургерная 'True Burgers'"]["assoc_lookup"]
    simulator_config = PRESET_DATASETS["Бургерная 'True Burgers'"]["simulator"]


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
    
    label_color = "#cbd5e1" if is_highlighted else "#94a3b8"
    value_color = "#ffffff"
    subtext_color = "#a5b4fc" if is_highlighted else "#64748b"
    
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

# PDF example report download
def _build_pdf_bytes():
    menu_records = df_menu.to_dict("records") if not df_menu.empty else []
    puzzles = df_menu[df_menu["cluster_label"] == "Puzzles"] if not df_menu.empty else pd.DataFrame()
    stars = df_menu[df_menu["cluster_label"] == "Stars"] if not df_menu.empty else pd.DataFrame()
    puzzle_name = puzzles.iloc[0]["item_name"] if not puzzles.empty else "—"
    star_name = stars.iloc[0]["item_name"] if not stars.empty else "—"
    combo_text = (
        f"Запустить комбо «{star_name} + {puzzle_name}» со скидкой 10–12% — "
        f"по демо-данным это поднимает продажи маржинальных позиций."
    )
    proc_lines = []
    if preset_name in PRESET_DATASETS and not df_fore.empty:
        sim = PRESET_DATASETS[preset_name]["simulator"]
        orders_sum = int(df_fore["predicted_orders"].sum())
        v1 = int(orders_sum * sim.get("mul1", 1))
        v2 = orders_sum * sim.get("mul2", 0.35)
        v2s = round(v2, 1) if v2 < 100 else int(v2)
        v3 = int(orders_sum * sim.get("mul3", 0.9))
        proc_lines = [
            f"{sim.get('title1', 'Сырьё 1')}: {v1} {sim.get('unit1', 'шт.')}",
            f"{sim.get('title2', 'Сырьё 2')}: {v2s} {sim.get('unit2', 'кг')}",
            f"{sim.get('title3', 'Сырьё 3')}: {v3} {sim.get('unit3', 'шт.')}",
        ]
    actions = []
    if not df_menu.empty:
        for label, emoji, tip in [
            ("Stars", "⭐️", "удерживать в топе меню"),
            ("Workhorses", "🐎", "проверить маржу и фудкост"),
            ("Puzzles", "❓", "продвигать в комбо и акциях"),
            ("Dogs", "❌", "рассмотреть вывод из меню"),
        ]:
            subset = df_menu[df_menu["cluster_label"] == label].head(1)
            for _, row in subset.iterrows():
                actions.append(f"{emoji} {row['item_name']}: {tip}")
    return generate_report_pdf(
        venue_name=preset_name,
        stats={
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "avg_check": avg_check,
            "avg_items_per_check": avg_items_per_check,
        },
        menu_rows=menu_records,
        combo_recommendation=combo_text,
        procurement_lines=proc_lines,
        action_items=actions or None,
    )

pdf_col1, pdf_col2 = st.columns([3, 1])
with pdf_col1:
    st.html(
        "<p style='margin:0; font-size:12px; color:#94a3b8;'>"
        "Скачайте PDF — такой отчёт вы получите при работе со мной. Можно приложить к сообщению владельцу кофейни."
        "</p>"
    )
with pdf_col2:
    st.download_button(
        label="📄 Скачать PDF-отчёт",
        data=_build_pdf_bytes(),
        file_name="gastrosense_primer_otcheta.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        key="download_pdf_report",
    )

st.write("")
make_section_header("Прогнозирование продаж и планирование поставок")

fore_col_left, fore_col_right = st.columns([1.2, 2.3])

with fore_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Симулятор спроса</p>')

        demand_shift = st.slider(
            "Сценарий трафика (%)",
            min_value=-30,
            max_value=50,
            value=0,
            step=5,
            key="demand_shift_slider_single_v4",
        )

        factor = 1 + (demand_shift / 100.0)
        adjusted_predicted_rev = df_fore["predicted_revenue"] * factor
        adjusted_lower_bound = df_fore["lower_bound_revenue"] * factor
        adjusted_upper_bound = df_fore["upper_bound_revenue"] * factor
        adjusted_predicted_orders = df_fore["predicted_orders"] * factor

        model_pred_rev = adjusted_predicted_rev
        model_lower = adjusted_lower_bound
        model_upper = adjusted_upper_bound

        val1 = int(adjusted_predicted_orders.sum() * simulator_config.get("mul1", 1.5))
        val2_raw = adjusted_predicted_orders.sum() * simulator_config.get("mul2", 0.35)
        val2 = round(val2_raw, 1) if val2_raw < 100 else int(val2_raw)
        val3 = int(adjusted_predicted_orders.sum() * simulator_config.get("mul3", 0.9))

        title1 = simulator_config.get("title1", "Сырьё 1")
        unit1 = simulator_config.get("unit1", "шт.")
        title2 = simulator_config.get("title2", "Сырьё 2")
        unit2 = simulator_config.get("unit2", "кг")
        title3 = simulator_config.get("title3", "Сырьё 3")
        unit3 = simulator_config.get("unit3", "шт.")

        st.html(f"""
        <div style="margin-top:8px; border-top: 1px solid #2d3748; padding-top:16px;">
            <p style="font-size:11px; font-weight:800; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px;">📦 Закупка на неделю (прогноз):</p>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8; margin-bottom:6px;">
                <span>{title1}</span>
                <span style="font-weight:700; color:#ffffff;">{val1} {unit1}</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8; margin-bottom:6px;">
                <span>{title2}</span>
                <span style="font-weight:700; color:#ffffff;">{val2} {unit2}</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8;">
                <span>{title3}</span>
                <span style="font-weight:700; color:#ffffff;">{val3} {unit3}</span>
            </div>
        </div>
        """)

with fore_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">7-дневный прогноз выручки</p>')
        if not df_fore.empty and not df_hist.empty:
            fig_fore = go.Figure()
            fig_fore.add_trace(go.Scatter(
                x=df_hist["date"],
                y=df_hist["revenue"],
                name="История (факт)",
                line=dict(color="#64748b", width=2.5),
                mode="lines",
            ))
            conn_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig_fore.add_trace(go.Scatter(
                x=conn_df["date"],
                y=[df_hist.tail(1)["revenue"].values[0], model_pred_rev.values[0]],
                showlegend=False,
                line=dict(color="#94a3b8", width=2.5, dash="dot"),
            ))
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"],
                y=model_pred_rev,
                name="Прогноз",
                line=dict(color="#3b82f6", width=3.5),
                mode="lines+markers",
            ))
            fig_fore.add_trace(go.Scatter(
                x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
                y=model_upper.tolist() + model_lower.tolist()[::-1],
                fill="toself",
                fillcolor="rgba(59, 130, 246, 0.08)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="Доверительный интервал (95%)",
            ))
            fig_fore.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#e2e8f0"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=320,
                xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=10), linecolor="#334155"),
                yaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#94a3b8", size=10), zeroline=False),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10, color="#94a3b8"),
                ),
            )
            st.plotly_chart(fig_fore, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Нет данных прогнозирования.")

st.write("")
make_section_header("Анализ прибыльности и популярности меню")

menu_col_left, menu_col_right = st.columns([1.8, 1])

with menu_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Карта маржинальности блюд</p>')
        
        if not df_menu.empty:
            median_pop = df_menu["popularity_sales"].median()
            median_margin = df_menu["avg_margin"].median()
            
            colors_map = {
                "Stars": "#6366f1",
                "Workhorses": "#10b981",
                "Puzzles": "#f59e0b",
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
            
            fig_scatter.add_vline(x=median_pop, line_dash="dash", line_color="#334155", line_width=1.5)
            fig_scatter.add_hline(y=median_margin, line_dash="dash", line_color="#334155", line_width=1.5)
            
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 1.5, text="🌟 STARS", showarrow=False, font=dict(color="rgba(99, 102, 241, 0.2)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 1.5, y=median_margin * 0.5, text="🐎 WORKHORSES", showarrow=False, font=dict(color="rgba(16, 185, 129, 0.2)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 1.5, text="❓ PUZZLES", showarrow=False, font=dict(color="rgba(245, 158, 11, 0.2)", size=14, weight="bold"))
            fig_scatter.add_annotation(x=median_pop * 0.5, y=median_margin * 0.5, text="🐕 DOGS", showarrow=False, font=dict(color="rgba(239, 68, 68, 0.2)", size=14, weight="bold"))
            
            fig_scatter.update_traces(
                marker=dict(size=12, line=dict(width=1, color="#1e293b")),
                textposition="top center",
                textfont=dict(color="#e2e8f0", size=9)
            )
            
            fig_scatter.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#e2e8f0"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=350,
                xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=10), linecolor="#334155"),
                yaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=10), linecolor="#334155"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=9, color="#94a3b8")
                )
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
            
            # AI Menu Tip Banner to fill empty space under scatter plot
            puzzles = df_menu[df_menu["cluster_label"] == "Puzzles"]
            stars = df_menu[df_menu["cluster_label"] == "Stars"]
            
            puzzle_name = puzzles.iloc[0]["item_name"] if not puzzles.empty else (df_menu.iloc[-1]["item_name"] if len(df_menu) > 1 else "Блюдо-Загадка")
            star_name = stars.iloc[0]["item_name"] if not stars.empty else (df_menu.iloc[0]["item_name"] if not df_menu.empty else "Блюдо-Звезда")
            
            st.html(f"""
            <div style="background-color: rgba(99, 102, 241, 0.03); 
                        border: 1px dashed rgba(99, 102, 241, 0.2); 
                        border-radius: 16px; 
                        padding: 16px; 
                        margin-top: 16px;">
                <span style="font-size: 11px; font-weight: 800; color: #818cf8; text-transform: uppercase; letter-spacing: 1px;">💡 AI-РЕКОМЕНДАЦИЯ ПО МЕНЮ</span>
                <p style="margin: 6px 0 0 0; font-size: 12px; color: #cbd5e1; line-height: 1.5;">
                    Попробуйте объединить высокоприбыльное, но редкое блюдо <b>{puzzle_name}</b> в комбо-набор с популярным лидером продаж <b>{star_name}</b>. 
                    Это простимулирует спрос на маржинальную позицию и увеличит прибыль заведения без раздувания фудкоста.
                </p>
            </div>
            """)
        else:
            st.info("Нет данных меню.")
    
with menu_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:16px; text-transform:uppercase; letter-spacing:0.5px;">Стратегия оптимизации меню</p>')
        
        stars_count, workhorses_count, puzzles_count, dogs_count = 0, 0, 0, 0
        if not df_menu.empty:
            stars_count = int((df_menu["cluster_label"] == "Stars").sum())
            workhorses_count = int((df_menu["cluster_label"] == "Workhorses").sum())
            puzzles_count = int((df_menu["cluster_label"] == "Puzzles").sum())
            dogs_count = int((df_menu["cluster_label"] == "Dogs").sum())
            
        st.html(f"""
        <div style="margin-bottom: 12px; border-left: 3px solid #6366f1; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #818cf8; font-size:12px;">🌟 STARS</strong>
                <span style="font-size: 10px; background-color: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid rgba(99, 102, 241, 0.3);">{stars_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">Высокая маржа и спрос. Не менять рецептуру, продвигать в топе.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #10b981; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #34d399; font-size:12px;">🐎 WORKHORSES</strong>
                <span style="font-size: 10px; background-color: rgba(16, 185, 129, 0.15); color: #34d399; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.3);">{workhorses_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">Высокий спрос, низкая маржа. Сократить фудкост сырья.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #f59e0b; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #fbbf24; font-size:12px;">❓ PUZZLES</strong>
                <span style="font-size: 10px; background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.3);">{puzzles_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">Низкий спрос, высокая маржа. Стимулировать акциями.</p>
        </div>
        <div style="margin-bottom: 0px; border-left: 3px solid #ef4444; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #f87171; font-size:12px;">🐕 DOGS</strong>
                <span style="font-size: 10px; background-color: rgba(239, 68, 68, 0.15); color: #f87171; padding: 2px 6px; border-radius: 8px; font-weight: 700; border: 1px solid rgba(239, 68, 68, 0.3);">{dogs_count} поз.</span>
            </div>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">Низкий спрос и маржа. Исключить или радикально переработать.</p>
        </div>
        """)
 
        # Add Menu Summary Metrics below to balance left-right height in Smith-Shostack layout
        total_items = len(df_menu) if not df_menu.empty else 0
        avg_menu_margin = df_menu["avg_margin"].mean() if not df_menu.empty else 0.0
        best_seller = df_menu.loc[df_menu["popularity_sales"].idxmax()]["item_name"] if not df_menu.empty else "—"
        
        st.html(f"""
        <div style="margin-top: 24px; border-top: 1px solid #2d3748; padding-top: 20px;">
            <p style="font-size:12px; font-weight:800; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px;">📊 Сводка по меню:</p>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94a3b8; margin-bottom:8px;">
                <span>Всего позиций в меню</span>
                <span style="font-weight:700; color:#ffffff;">{total_items} шт.</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94a3b8; margin-bottom:8px;">
                <span>Средняя маржинальность</span>
                <span style="font-weight:700; color:#ffffff;">{avg_menu_margin:,.2f} ₽</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#94a3b8;">
                <span>Лидер по продажам</span>
                <span style="font-weight:700; color:#ffffff;">{best_seller}</span>
            </div>
        </div>
        """)

        # Action Plan Table
        st.html("<p style='font-size:11.5px; font-weight:800; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-top:20px; margin-bottom:8px;'>📋 План действий для заведения:</p>")
        
        actions = []
        if not df_menu.empty:
            stars = df_menu[df_menu["cluster_label"] == "Stars"].head(1)
            workhorses = df_menu[df_menu["cluster_label"] == "Workhorses"].head(1)
            puzzles = df_menu[df_menu["cluster_label"] == "Puzzles"].head(1)
            dogs = df_menu[df_menu["cluster_label"] == "Dogs"].head(1)
            
            for _, row in stars.iterrows():
                actions.append(f"⭐️ <b>{row['item_name']} (Звезда):</b> Удерживать качество рецептуры, стимулировать объем продаж.")
            for _, row in workhorses.iterrows():
                actions.append(f"🐎 <b>{row['item_name']} (Лошадка):</b> Высокий спрос, но мала маржа. Повысить цену на 5% или снизить фудкост.")
            for _, row in puzzles.iterrows():
                actions.append(f"❓ <b>{row['item_name']} (Загадка):</b> Высокая маржа, но мало берут. Продвигать в комбо, добавить в акции.")
            for _, row in dogs.iterrows():
                actions.append(f"❌ <b>{row['item_name']} (Собака):</b> Низкие продажи и маржа. Вывести из меню или пересмотреть рецепт.")
        else:
            actions.append("Нет данных меню для формирования плана действий.")
            
        action_html = "<div style='background-color:#1e293b; padding:12px; border-radius:12px; border:1px solid #2d3748; font-size:11px; line-height:1.5; color:#cbd5e1;'>"
        for act in actions:
            action_html += f"<div style='margin-bottom:8px; border-bottom:1px solid #2d3748; padding-bottom:6px;'>{act}</div>"
        if actions:
            action_html = action_html[:-43] + "</div>" # removes last border-bottom
        action_html += "</div>"
        st.html(action_html)

# ==========================================
# 🤝 SECTION 3: CROSS-SALES (Кросс-продажи)
# ==========================================
make_section_header("Совместные покупки и комбо-конструктор")

cross_col_left, cross_col_right = st.columns([1.5, 1])

with cross_col_left:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Связи между блюдами в чеках</p>')
        
        if len(items_list) > 1 and len(assoc_matrix) > 0:
            fig_heat = go.Figure(data=go.Heatmap(
                z=assoc_matrix,
                x=items_list,
                y=items_list,
                colorscale=[[0, "#161b26"], [0.5, "#3b82f6"], [1, "#6366f1"]],
                hoverongaps=False,
                text=[[f"P({b} | {a}) = {val:.1%}" for b, val in zip(items_list, row)] for a, row in zip(items_list, assoc_matrix)],
                hoverinfo="text"
            ))
            fig_heat.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#e2e8f0"),
                margin=dict(l=0, r=0, t=10, b=40),
                height=480,
                xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=9), linecolor="#334155", tickangle=-45),
                yaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=9), linecolor="#334155")
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Недостаточно данных для матрицы связей.")
    
with cross_col_right:
    with st.container(border=True):
        st.html('<p style="font-size:12px; font-weight:800; color:#ffffff; margin-bottom:12px; text-transform:uppercase; letter-spacing:0.5px;">Интерактивный конструктор комбо</p>')
        
        if items_list:
            selected_item = st.selectbox(
                "Выберите основное блюдо для комбо:", 
                items_list, 
                key="cross_combo_select_single_v4"
            )
        else:
            selected_item = st.selectbox(
                "Выберите основное блюдо для комбо:", 
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
            
        st.html("<p style='font-size:11px; font-weight:700; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-top:16px;'>Топ сопутствующих позиций:</p>")
        
        for name, prob, lift in recommendations:
            st.html(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background-color:#1e293b; padding:8px 14px; border-radius:12px; margin-bottom:6px; border:1px solid #2d3748;">
                <div>
                    <span style="font-weight:700; color:#ffffff; font-size:12px;">{name}</span>
                    <br><span style="font-size:9px; color:#94a3b8;">Lift: {lift}x</span>
                </div>
                <span style="color:#34d399; font-weight:800; font-size:12px;">{prob:.1%}</span>
            </div>
            """)
            
        if recommendations:
            combo_name = f"Комбо '{selected_item.split()[-1] if len(selected_item.split()) > 1 else selected_item} + {recommendations[0][0].split()[-1] if len(recommendations[0][0].split()) > 1 else recommendations[0][0]}'"
            suggested_discount = 12
            margin_lift = 8.4 + (recommendations[0][1] * 10)
            
            st.html(f"""
            <div class="combo-card">
                <p style="font-size:10px; font-weight:800; color:#818cf8; text-transform:uppercase; letter-spacing:1px; margin:0 0 4px 0;">🎯 AI КОМБО-РЕКОМЕНДАЦИЯ</p>
                <h5 style="color:#ffffff; font-weight:800; font-size:13px; margin:0 0 6px 0;">{combo_name}</h5>
                <p style="font-size:11px; color:#94a3b8; line-height:1.4; margin:0 0 8px 0;">
                    Запустите бандл с автоматической скидкой в <strong style="color: #ffffff;">{suggested_discount}%</strong> для увеличения оборачиваемости.
                </p>
                <div style="display:flex; justify-content:space-between; border-top:1px solid #2d3748; padding-top:8px; font-size:11px;">
                    <span style="color:#94a3b8;">Эффект чека:</span>
                    <span style="color:#34d399; font-weight:700;">+{margin_lift:.1f}% маржи</span>
                </div>
            </div>
            """)
            
            st.html("<p style='font-size:11px; font-weight:700; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-top:18px;'>💰 Калькулятор окупаемости комбо:</p>")
            combo_sales_per_day = st.slider(
                "Продаж комбо в день (шт.):", 
                min_value=5, 
                max_value=100, 
                value=20, 
                step=5,
                key="combo_sales_per_day_slider"
            )
            # Estimate additional profit: 18% of avg check is typical margin lift of combo
            combo_profit_per_unit = avg_check * 0.18
            monthly_combo_revenue = combo_sales_per_day * 30 * combo_profit_per_unit
            
            st.html(f"""
            <div style="background-color: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 12px; margin-top: 8px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#cbd5e1; margin-bottom:4px;">
                    <span>Прибавка к марже с комбо:</span>
                    <strong style="color:#34d399;">+{combo_profit_per_unit:,.0f} ₽ / шт.</strong>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#cbd5e1;">
                    <span>Доп. прибыль заведения:</span>
                    <strong style="color:#34d399; font-size:13px;">+{monthly_combo_revenue:,.0f} ₽ / мес.</strong>
                </div>
            </div>
            """)

st.html(f"""
<div style="margin-top:48px; padding:24px; background:#161b26; border:1px solid #2d3748; border-radius:16px; text-align:center;">
    <p style="margin:0 0 8px 0; font-size:14px; font-weight:800; color:#ffffff;">Хотите такой же разбор для своей кофейни?</p>
    <p style="margin:0 0 12px 0; font-size:12px; color:#94a3b8; line-height:1.5;">
        Первый мини-разбор чеков из iiko — бесплатно. Пишите в Telegram или на почту.
    </p>
    <p style="margin:0; font-size:12px; color:#cbd5e1;">
        <b>{CONTACT_NAME}</b> · {CONTACT_TELEGRAM} · {CONTACT_EMAIL}
    </p>
</div>
""")
