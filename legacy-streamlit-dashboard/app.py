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

from pdf_report import generate_report_pdf
from presets import PRESET_DATASETS
from portfolio_ui import render_hero_banner, render_services_block

# Page configuration for a wide, premium feel
st.set_page_config(
    page_title="GastroSense | Restaurant Intelligence AI Dashboard",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom premium dark theme styling
_STYLE_PATH = _APP_DIR / "assets" / "style.css"
if _STYLE_PATH.exists():
    st.html(f"<style>{_STYLE_PATH.read_text(encoding='utf-8')}</style>")

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

def _pct_change(recent: float, previous: float) -> float:
    if previous <= 0:
        return 0.0
    return (recent - previous) / previous * 100.0


def _format_delta(pct: float, suffix: str) -> dict:
    sign = "+" if pct >= 0 else ""
    return {"text": f"{sign}{pct:.1f}% {suffix}", "positive": pct >= 0}


def compute_kpi_deltas_from_hist(df_hist: pd.DataFrame) -> dict:
    """Считает динамику KPI по последним 7 дням vs предыдущим 7."""
    if df_hist is None or df_hist.empty or len(df_hist) < 14:
        return {
            "revenue": {"text": "н/д за период", "positive": True},
            "orders": {"text": "н/д за период", "positive": True},
            "avg_check": {"text": "н/д за период", "positive": True},
            "items_depth": {"text": "н/д за период", "positive": True},
        }
    tail7 = df_hist.tail(7)
    prev7 = df_hist.iloc[-14:-7]
    rev_pct = _pct_change(tail7["revenue"].mean(), prev7["revenue"].mean())
    ord_pct = _pct_change(tail7["orders_count"].mean(), prev7["orders_count"].mean())
    check_recent = tail7["revenue"].sum() / max(tail7["orders_count"].sum(), 1)
    check_prev = prev7["revenue"].sum() / max(prev7["orders_count"].sum(), 1)
    check_pct = _pct_change(check_recent, check_prev)
    depth_pct = check_pct * 0.55 + ord_pct * 0.25
    return {
        "revenue": _format_delta(rev_pct, "vs прошлая неделя"),
        "orders": _format_delta(ord_pct, "к прошлому периоду"),
        "avg_check": _format_delta(check_pct, "к среднему чеку"),
        "items_depth": _format_delta(depth_pct, "глубины чека"),
    }


def _menu_unit_price(row) -> float:
    sales = max(int(row["popularity_sales"]), 1)
    return float(row["total_revenue"]) / sales


def evaluate_combo_bundle(df_menu: pd.DataFrame, main_item: str, addon_item: str, lift: float, attach_prob: float) -> dict:
    """Оценка комбо по марже позиций: скидка может дать отрицательный эффект."""
    if df_menu.empty:
        return None
    main_rows = df_menu[df_menu["item_name"] == main_item]
    addon_rows = df_menu[df_menu["item_name"] == addon_item]
    if main_rows.empty or addon_rows.empty:
        return None

    main = main_rows.iloc[0]
    addon = addon_rows.iloc[0]
    price_a = _menu_unit_price(main)
    price_b = _menu_unit_price(addon)
    margin_a = float(main["avg_margin"])
    margin_b = float(addon["avg_margin"])
    cat_a = str(main.get("category", "")).lower()
    cat_b = str(addon.get("category", "")).lower()

    bundle_price = price_a + price_b
    bundle_margin_full = margin_a + margin_b

    substitute_penalty = 0.0
    if main_item == addon_item:
        substitute_penalty = 0.40
    elif cat_a == cat_b and cat_a in ("bakery", "burgers", "pizza", "coffee", "drinks", "sides"):
        substitute_penalty = 0.14
    elif cat_a == cat_b:
        substitute_penalty = 0.08

    base_discount = 13.0 - min(float(lift), 2.2) * 3.5 + substitute_penalty * 28.0
    suggested_discount = int(round(max(5.0, min(20.0, base_discount))))

    discount_rub = bundle_price * (suggested_discount / 100.0)
    combo_net_margin = bundle_margin_full - discount_rub
    addon_discount_share = discount_rub * (price_b / bundle_price) if bundle_price > 0 else discount_rub

    if main_item == addon_item:
        incremental_margin = combo_net_margin - bundle_margin_full
    else:
        incremental_margin = margin_b - addon_discount_share

    rate_full = bundle_margin_full / bundle_price if bundle_price > 0 else 0.0
    combo_sell_price = bundle_price - discount_rub
    rate_combo = combo_net_margin / combo_sell_price if combo_sell_price > 0 else 0.0
    margin_rate_delta_pct = ((rate_combo - rate_full) / rate_full * 100.0) if rate_full > 0 else 0.0

    if main_item == addon_item:
        note = "Одинаковые позиции: скидка почти всегда уводит маржу в минус."
    elif incremental_margin < 0:
        note = "Скидка больше маржи доп. позиции — комбо снижает прибыль с чека."
    elif margin_rate_delta_pct < -3:
        note = "Маржинальность бандла ниже раздельной продажи, зато может поднять объём."
    else:
        note = "Комбо окупается: доп. позиция приносит прибыль после скидки."

    return {
        "suggested_discount": suggested_discount,
        "combo_net_margin": combo_net_margin,
        "incremental_margin": incremental_margin,
        "margin_rate_delta_pct": margin_rate_delta_pct,
        "is_healthy": incremental_margin > 0 and combo_net_margin > 0 and main_item != addon_item,
        "note": note,
        "attach_prob": attach_prob,
    }


stats_data = get_data("/analytics/stats")
is_live = stats_data is not None and stats_data.get("total_orders", 0) > 0

# Render Top Navigation Bar
col_logo, col_crm, col_reset = st.columns([7, 1.5, 1.5])

with col_logo:
    st.html("""
    <div class="logo-area" style="padding: 6px 0;">
        <div class="header-column-marker"></div>
        <span class="logo-text" style="font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">🍷 GastroSense <span style="background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI</span></span>
    </div>
    """)

with col_crm:
    with st.popover("Импорт CRM", use_container_width=True):
        st.html("<p style='font-size:11px; color:#cbd5e1; margin-bottom:8px; line-height:1.4;'>Загрузите чеки в CSV или Excel для анализа. Для теста выгрузки скачайте шаблон:</p>")
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
        <span style="font-size: 14px; font-weight: 700; color: #94a3b8; letter-spacing: -0.2px;">🏬 Профиль заведения (Симуляция):</span>
    </div>
    """)
with col_sel_widget:
    preset_name = st.selectbox(
        label="🏬 Профиль заведения (Симуляция):",
        options=preset_options,
        index=len(preset_options) - 1 if is_live else 0,
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
    kpi_deltas = preset_data["kpi_deltas"]
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
    kpi_deltas = compute_kpi_deltas_from_hist(df_hist)


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
            delta=kpi_deltas["revenue"]["text"], 
            is_positive=kpi_deltas["revenue"]["positive"],
            is_highlighted=True
        ))
with c2:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Количество заказов", 
            f"{total_orders:,.0f}".replace(",", " "), 
            "Всего чеков закрыто", 
            delta=kpi_deltas["orders"]["text"], 
            is_positive=kpi_deltas["orders"]["positive"]
        ))
with c3:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Средний чек", 
            f"{avg_check:,.2f} ₽".replace(",", " "), 
            "На одного посетителя", 
            delta=kpi_deltas["avg_check"]["text"], 
            is_positive=kpi_deltas["avg_check"]["positive"]
        ))
with c4:
    with st.container(border=True):
        st.html(make_metric_card_content(
            "Продано позиций", 
            f"{total_items_sold:,.0f}".replace(",", " "), 
            f"Среднее в чеке: {avg_items_per_check:.1f} ед.", 
            delta=kpi_deltas["items_depth"]["text"], 
            is_positive=kpi_deltas["items_depth"]["positive"]
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
        "Экспорт сводного отчёта по ключевым метрикам, меню, комбо и закупкам для выбранного профиля."
        "</p>"
    )
with pdf_col2:
    st.download_button(
        label="📄 Скачать отчёт (PDF)",
        data=_build_pdf_bytes(),
        file_name="gastrosense_analytics_report.pdf",
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

        menu_names = df_menu["item_name"].tolist() if not df_menu.empty else [r[0] for r in recommendations]
        default_addon = recommendations[0][0] if recommendations else menu_names[0]
        default_idx = menu_names.index(default_addon) if default_addon in menu_names else 0
        addon_item = st.selectbox(
            "Доп. позиция в комбо:",
            menu_names,
            index=default_idx,
            key="combo_addon_item_select",
        )

        rec_map = {name: (prob, lift) for name, prob, lift in recommendations}
        if addon_item in rec_map:
            addon_prob, addon_lift = rec_map[addon_item]
        elif is_live and selected_item in items_list and addon_item in items_list:
            i, j = items_list.index(selected_item), items_list.index(addon_item)
            addon_prob = assoc_matrix[i][j]
            addon_lift = round(1.0 + addon_prob * 0.5, 1)
        else:
            addon_prob, addon_lift = 0.12, 0.85
            
        if recommendations or addon_item:
            combo_eval = evaluate_combo_bundle(df_menu, selected_item, addon_item, addon_lift, addon_prob)

            combo_name = f"Комбо '{selected_item.split()[-1] if len(selected_item.split()) > 1 else selected_item} + {addon_item.split()[-1] if len(addon_item.split()) > 1 else addon_item}'"

            if combo_eval:
                suggested_discount = combo_eval["suggested_discount"]
                margin_delta = combo_eval["margin_rate_delta_pct"]
                incremental_margin = combo_eval["incremental_margin"]
                is_healthy = combo_eval["is_healthy"]
                combo_note = combo_eval["note"]
                effect_color = "#34d399" if is_healthy else "#f87171"
                effect_sign = "+" if margin_delta >= 0 else ""
                margin_line = f"{effect_sign}{margin_delta:.1f}% маржинальности бандла"
                incremental_sign = "+" if incremental_margin >= 0 else ""
            else:
                suggested_discount = 12
                margin_delta = 0.0
                incremental_margin = avg_check * 0.05
                is_healthy = True
                combo_note = "Недостаточно данных по марже позиций."
                effect_color = "#94a3b8"
                effect_sign = ""
                margin_line = "н/д"
                incremental_sign = "+"

            st.html(f"""
            <div class="combo-card">
                <p style="font-size:10px; font-weight:800; color:#818cf8; text-transform:uppercase; letter-spacing:1px; margin:0 0 4px 0;">🎯 AI КОМБО-РЕКОМЕНДАЦИЯ</p>
                <h5 style="color:#ffffff; font-weight:800; font-size:13px; margin:0 0 6px 0;">{combo_name}</h5>
                <p style="font-size:11px; color:#94a3b8; line-height:1.4; margin:0 0 8px 0;">
                    Рекомендуемая скидка на бандл: <strong style="color: #ffffff;">{suggested_discount}%</strong>.
                    {combo_note}
                </p>
                <div style="display:flex; justify-content:space-between; border-top:1px solid #2d3748; padding-top:8px; font-size:11px; margin-bottom:6px;">
                    <span style="color:#94a3b8;">Маржинальность бандла vs раздельно:</span>
                    <span style="color:{effect_color}; font-weight:700;">{margin_line}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:#94a3b8;">Прибыль с доп. позиции после скидки:</span>
                    <span style="color:{effect_color}; font-weight:700;">{incremental_sign}{incremental_margin:,.0f} ₽ / комбо</span>
                </div>
            </div>
            """)
            
            st.html("<p style='font-size:11px; font-weight:700; color:#ffffff; text-transform:uppercase; letter-spacing:0.5px; margin-top:18px;'>💰 Калькулятор окупаемости комбо:</p>")
            combo_sales_per_day = st.slider(
                "Продаж комбо в день (шт.):", 
                min_value=0, 
                max_value=20, 
                value=10, 
                step=1,
                key="combo_sales_per_day_slider"
            )
            monthly_combo_revenue = combo_sales_per_day * 30 * incremental_margin
            profit_color = "#34d399" if monthly_combo_revenue >= 0 else "#f87171"
            profit_sign = "+" if incremental_margin >= 0 else ""
            monthly_sign = "+" if monthly_combo_revenue >= 0 else ""
            
            st.html(f"""
            <div style="background-color: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 12px; padding: 12px; margin-top: 8px;">
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#cbd5e1; margin-bottom:4px;">
                    <span>Прибыль с одного комбо (после скидки):</span>
                    <strong style="color:{profit_color};">{profit_sign}{incremental_margin:,.0f} ₽ / шт.</strong>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#cbd5e1;">
                    <span>Эффект за месяц при текущем объёме:</span>
                    <strong style="color:{profit_color}; font-size:13px;">{monthly_sign}{monthly_combo_revenue:,.0f} ₽ / мес.</strong>
                </div>
            </div>
            """)
