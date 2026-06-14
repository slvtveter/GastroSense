import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
from datetime import datetime, date

# Page configuration
st.set_page_config(
    page_title="GastroSense | Restaurant Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode custom CSS injection for premium styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #1e222b;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 14px;
        color: #8a909d;
        text-transform: uppercase;
        font-weight: bold;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #ffffff;
        margin-top: 5px;
    }
    .recommendation-card {
        background-color: #1a2332;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #00d2c4;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allowed_html=True)

# Connection Settings
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# Helper function to query the API
def get_data(endpoint: str):
    try:
        response = requests.get(f"{BACKEND_API_URL}{endpoint}", timeout=10)
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

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🍷 GastroSense</h1>", unsafe_allowed_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #8a909d;'>SaaS-платформа ресторанного ML-анализа</p>", unsafe_allowed_html=True)
st.sidebar.markdown("---")

# Health check connection status
backend_status = get_data("/")
if backend_status:
    st.sidebar.success("🟢 Бэкенд API: Подключено")
else:
    st.sidebar.error("🔴 Бэкенд API: Оффлайн (Запустите docker-compose)")

st.sidebar.markdown("### 📥 Импорт данных")

# 1-Click Demo Button
if st.sidebar.button("🚀 Запустить демо-режим (1 клик)", use_container_width=True):
    with st.spinner("Генерация 180 дней истории продаж для 'True Burgers'..."):
        res = post_data("/upload/seed-demo")
        if res.get("success"):
            st.sidebar.success(f"Готово! Загружено {res.get('orders_seeded')} чеков.")
            st.rerun()
        else:
            st.sidebar.error(f"Ошибка: {res.get('message')}")

st.sidebar.markdown("<p style='text-align: center; color: #8a909d; font-size: 12px;'>Или загрузите собственную CRM-выгрузку:</p>", unsafe_allowed_html=True)

# CRM File uploader
uploaded_file = st.sidebar.file_uploader(
    "Файл чеков (CSV / XLSX)", 
    type=["csv", "xlsx"], 
    help="Колонки должны содержать: Дата, ID чека, Блюдо, Цена, Количество"
)

if uploaded_file is not None:
    if st.sidebar.button("📤 Обработать файл", use_container_width=True):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        with st.spinner("Загрузка и валидация чеков..."):
            res = post_data("/upload/checks", files=files)
            if res.get("success"):
                st.sidebar.success(f"Успех! Обработано {res.get('orders_processed')} заказов.")
                st.rerun()
            else:
                st.sidebar.error(f"Ошибка загрузки: {res.get('detail', 'Неизвестная ошибка')}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Управление ML-моделями")
if st.sidebar.button("⚙️ Запустить обучение моделей", use_container_width=True):
    with st.spinner("Обучение K-Means и LightGBM..."):
        res = post_data("/ml/train")
        if res.get("success"):
            st.sidebar.success("Обучение запущено в фоновом режиме!")
        else:
            st.sidebar.error("Не удалось запустить обучение.")

# ----------------- MAIN AREA -----------------

# Fetch stats to check if DB is seeded
stats = get_data("/analytics/stats")

if not stats or stats.get("total_orders", 0) == 0:
    # --- Landing Page / Setup Guide ---
    st.markdown("<h2 style='text-align: center;'>Добро пожаловать в GastroSense! 👋</h2>", unsafe_allowed_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #8a909d;'>Профессиональная ML-аналитика для ресторанного бизнеса.</p>", unsafe_allowed_html=True)
    
    st.info("💡 **Как начать работу:** Для работы платформы необходимы исторические чеки. Запустите демо-режим в боковой панели слева (кнопка **'Запустить демо-режим (1 клик)'**), либо загрузите свою CRM-выгрузку.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Искусственный Интеллект в HoReCa")
        st.markdown("""
        Платформа решает критически важные аналитические задачи:
        - **Прогнозирование спроса**: Модель LightGBM с учетом сезонности и лагов предсказывает выручку и объем заказов на 7 дней вперед.
        - **Menu Engineering**: Кластеризация K-Means делит меню на 4 прибыльные группы (Звезды, Лошадки, Загадки, Собаки).
        - **Анализ совместных покупок**: Расчет условных вероятностей совместных заказов блюд.
        """)
    with col2:
        st.subheader("📈 Производственная Архитектура (Production)")
        st.markdown("""
        - **FastAPI Backend**: Быстрый асинхронный движок для парсинга и валидации данных.
        - **MySQL DB**: Нормализованное хранилище транзакций.
        - **Streamlit Frontend**: Интерактивный интерактивный интерфейс.
        - **Docker Compose**: Изолированные контейнеры для легкого деплоя.
        """)
    
    # Showcase images if we had any, otherwise keep it clean.
else:
    # --- Live Dashboard ---
    st.markdown("<h1 style='margin-bottom: 0px;'>📊 Дашборд ресторанной аналитики</h1>", unsafe_allowed_html=True)
    st.markdown("<p style='color: #8a909d; margin-bottom: 25px;'>Анализ заведения: <strong>True Burgers</strong> (демо-режим)</p>", unsafe_allowed_html=True)
    
    # 1. KPI Cards Row
    col_rev, col_ord, col_chk, col_item = st.columns(4)
    
    with col_rev:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #00d2c4;">
            <div class="metric-title">Общая Выручка</div>
            <div class="metric-value">{stats.get('total_revenue'):,.2f} ₽</div>
        </div>
        """, unsafe_allowed_html=True)
        
    with col_ord:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <div class="metric-title">Всего заказов</div>
            <div class="metric-value">{stats.get('total_orders'):,}</div>
        </div>
        """, unsafe_allowed_html=True)
        
    with col_chk:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <div class="metric-title">Средний чек</div>
            <div class="metric-value">{stats.get('avg_check'):,.2f} ₽</div>
        </div>
        """, unsafe_allowed_html=True)
        
    with col_item:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ec4899;">
            <div class="metric-title">Позиций продано</div>
            <div class="metric-value">{stats.get('total_items_sold'):,} шт.</div>
        </div>
        """, unsafe_allowed_html=True)

    st.markdown("<br>", unsafe_allowed_html=True)

    # Tabs
    tab_forecast, tab_menu, tab_assoc, tab_data = st.tabs([
        "📈 Прогноз спроса (Time Series)",
        "🌟 Матрица меню (K-Means)",
        "🤝 Совместные покупки",
        "📋 Журнал транзакций"
    ])

    # 2. TAB: DEMAND FORECAST
    with tab_forecast:
        st.subheader("Прогнозирование дневной выручки на 7 дней вперед")
        
        hist_data = get_data("/analytics/history?days=21")
        fore_data = get_data("/analytics/forecast")
        
        if hist_data and fore_data:
            df_hist = pd.DataFrame(hist_data)
            df_fore = pd.DataFrame(fore_data)
            
            df_hist["date"] = pd.to_datetime(df_hist["date"])
            df_fore["date"] = pd.to_datetime(df_fore["date"])
            
            # Interactive Line Chart with Confidence Bands
            fig = go.Figure()
            
            # History Line
            fig.add_trace(go.Scatter(
                x=df_hist["date"],
                y=df_hist["revenue"],
                name="История (Факт)",
                line=dict(color="#3b82f6", width=3)
            ))
            
            # Connection dot between history and forecast
            connection_df = pd.concat([df_hist.tail(1), df_fore.head(1)])
            fig.add_trace(go.Scatter(
                x=connection_df["date"],
                y=connection_df["revenue"] if "revenue" in connection_df else connection_df["predicted_revenue"],
                showlegend=False,
                line=dict(color="#ff4b4b", dash="dash")
            ))
            
            # Forecast Line
            fig.add_trace(go.Scatter(
                x=df_fore["date"],
                y=df_fore["predicted_revenue"],
                name="Прогноз (ML)",
                line=dict(color="#ff4b4b", width=3, dash="dash")
            ))
            
            # Confidence Interval Upper Bound
            fig.add_trace(go.Scatter(
                x=df_fore["date"].tolist() + df_fore["date"].tolist()[::-1],
                y=df_fore["upper_bound_revenue"].tolist() + df_fore["lower_bound_revenue"].tolist()[::-1],
                fill="toself",
                fillcolor="rgba(255, 75, 75, 0.15)",
                line=dict(color="rgba(255, 255, 255, 0)"),
                hoverinfo="skip",
                name="Доверительный интервал (95%)"
            ))
            
            fig.update_layout(
                title="История продаж и прогноз выручки с коридором неопределенности",
                xaxis_title="Дата",
                yaxis_title="Выручка (руб.)",
                template="plotly_dark",
                hovermode="x unified",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Alerts and Smart Recommendation Panel
            st.markdown("### 💡 Интеллектуальные рекомендации")
            
            # Determine peak forecasted day
            peak_day = df_fore.loc[df_fore["predicted_revenue"].idxmax()]
            avg_forecast = df_fore["predicted_revenue"].mean()
            growth_pct = ((peak_day["predicted_revenue"] - avg_forecast) / avg_forecast) * 100
            
            st.markdown(f"""
            <div class="recommendation-card">
                <h4>🎯 Пик спроса ожидается: <strong>{peak_day['date'].strftime('%d.%m.%Y')} ({peak_day['date'].strftime('%A')})</strong></h4>
                <p>Прогноз выручки: <strong>{peak_day['predicted_revenue']:,.2f} ₽</strong> (+{growth_pct:.1f}% к среднему за неделю).</p>
                <p>⚠️ <strong>Рекомендация менеджеру:</strong> Рекомендуется вывести дополнительного повара в смену и проверить запасы скоропортящихся ингредиентов (мясо, булки, зелень) на этот день.</p>
            </div>
            """, unsafe_allowed_html=True)
            
            # Grid of forecast details
            st.subheader("Таблица детального прогноза спроса")
            df_fore_display = df_fore.copy()
            df_fore_display["date"] = df_fore_display["date"].dt.strftime("%d.%m.%Y")
            df_fore_display.columns = ["Дата", "Прогноз Выручки (₽)", "Прогноз Заказов (шт)", "Нижний порог (₽)", "Верхний порог (₽)", "Обновлено"]
            st.dataframe(df_fore_display[["Дата", "Прогноз Выручки (₽)", "Прогноз Заказов (шт)", "Нижний порог (₽)", "Верхний порог (₽)"]], use_container_width=True, hide_index=True)
        else:
            st.info("⚠️ Модели еще не обучены. Пожалуйста, запустите обучение моделей в левой панели.")

    # 3. TAB: MENU ENGINEERING
    with tab_menu:
        st.subheader("Анализ меню (Smith-Shostack Matrix с кластеризацией K-Means)")
        st.markdown("""
        Матрица меню группирует блюда по их популярности (количество продаж) и прибыльности (маржа):
        - 🌟 **Звезды (Stars)**: Очень популярные и высокомаржинальные. Гордость ресторана.
        - 🐎 **Лошадки (Workhorses)**: Популярные, но с низкой маржой. Основной оборот.
        - ❓ **Загадки (Puzzles)**: Редкие продажи при высокой марже. Нужен маркетинг.
        - 🐕 **Собаки (Dogs)**: Низкие продажи, низкая маржа. Кандидаты на удаление.
        """)
        
        menu_data = get_data("/analytics/menu")
        if menu_data:
            df_menu = pd.DataFrame(menu_data)
            
            # Plotly scatter plot
            colors_map = {
                "Stars": "#f59e0b",       # Gold
                "Workhorses": "#10b981",  # Green
                "Puzzles": "#6366f1",     # Indigo
                "Dogs": "#ef4444"         # Red
            }
            
            # Dashed lines for median separation
            median_pop = df_menu["popularity_sales"].median()
            median_margin = df_menu["avg_margin"].astype(float).median()
            
            fig = px.scatter(
                df_menu,
                x="popularity_sales",
                y="avg_margin",
                color="cluster_label",
                text="item_name",
                color_discrete_map=colors_map,
                labels={
                    "popularity_sales": "Популярность (продано шт.)",
                    "avg_margin": "Средняя маржа на единицу (₽)",
                    "cluster_label": "Класс блюда",
                    "item_name": "Название"
                },
                hover_data=["total_revenue"]
            )
            
            # Add quadrant lines
            fig.add_vline(x=median_pop, line_dash="dash", line_color="#8a909d", annotation_text="Медиана продаж", annotation_position="top left")
            fig.add_hline(y=median_margin, line_dash="dash", line_color="#8a909d", annotation_text="Медиана маржи", annotation_position="bottom right")
            
            fig.update_traces(
                marker=dict(size=12, line=dict(width=1, color="white")),
                textposition="top center"
            )
            
            fig.update_layout(
                template="plotly_dark",
                height=550,
                title="K-Means распределение позиций меню"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Actionable recommendations by cluster
            st.subheader("💡 Рекомендации по оптимизации меню")
            
            selected_cluster = st.selectbox(
                "Выберите группу меню для просмотра рекомендаций:", 
                ["Stars", "Workhorses", "Puzzles", "Dogs"]
            )
            
            cluster_items = df_menu[df_menu["cluster_label"] == selected_cluster]
            
            st.markdown(f"**Позиции в группе {selected_cluster} ({len(cluster_items)} шт):**")
            st.write(", ".join(cluster_items["item_name"].tolist()))
            
            if selected_cluster == "Stars":
                st.success("""
                🌟 **План действий для Звезд:**
                - Не изменяйте рецептуру и качество ингредиентов.
                - Оставьте цену стабильной.
                - Разместите эти блюда на самом видном месте бумажного и электронного меню (эффект 'золотого треугольника').
                - Используйте их в рекламных креативах.
                """)
            elif selected_cluster == "Workhorses":
                st.info("""
                🐎 **План действий для Рабочих лошадок:**
                - Блюда популярны, но приносят мало маржи. Попробуйте немного уменьшить себестоимость (найти альтернативных поставщиков сырья).
                - Попробуйте немного поднять цену на 3-5% (поскольку спрос высокий и стабильный, клиенты этого почти не заметят).
                - Делайте комбо-наборы (например, 'Бургер True + Фри' со скидкой, чтобы увеличить объем продаж сопутствующего высокомаржинального фри).
                """)
            elif selected_cluster == "Puzzles":
                st.warning("""
                ❓ **План действий для Загадок:**
                - Блюда прибыльные, но их мало покупают. Проведите промо-акции (например, 'блюдо недели').
                - Обучите официантов активно предлагать эту позицию гостям при заказе.
                - Пересмотрите дизайн меню: возможно, название не привлекает внимания или нет аппетитного фото.
                """)
            elif selected_cluster == "Dogs":
                st.error("""
                🐕 **План действий для Собак:**
                - Позиции приносят мало денег и не пользуются спросом. Рекомендуется полностью вывести их из меню.
                - Если блюдо является 'фирменным' или обязательным (например, веганский бургер), переработайте его рецепт и подачу.
                - Проверьте объемы закупаемых под них заготовок, чтобы снизить списания просрочки.
                """)
        else:
            st.info("⚠️ Модели еще не обучены. Пожалуйста, запустите обучение моделей в левой панели.")

    # 4. TAB: PRODUCT ASSOCIATIONS (HEATMAP)
    with tab_assoc:
        st.subheader("Карта ассоциаций меню (Market Basket Analysis)")
        st.markdown("""
        Эта тепловая карта показывает условную вероятность: **P(Товар B | Товар A)** — вероятность того, что клиент купит Товар B, если он уже заказал Товар A.
        Используйте её для составления меню комбо-наборов и настройки перекрестных продаж (Cross-selling).
        """)
        
        assoc_data = get_data("/analytics/associations")
        if assoc_data and assoc_data.get("index"):
            index_items = assoc_data["index"]
            matrix_data = assoc_data["data"]
            
            # Interactive Plotly Heatmap
            fig = go.Figure(data=go.Heatmap(
                z=matrix_data,
                x=index_items,
                y=index_items,
                colorscale="Viridis",
                hoverongaps=False,
                text=[[f"P({b} | {a}) = {val:.1%}" for b, val in zip(index_items, row)] for a, row in zip(index_items, matrix_data)],
                hoverinfo="text"
            ))
            
            fig.update_layout(
                template="plotly_dark",
                height=600,
                xaxis_title="Товар B (сопутствующий)",
                yaxis_title="Товар A (основной)",
                title="Матрица условных вероятностей совместных покупок"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Extract top association rule for action panel
            st.markdown("### 🍟 Инсайты по совместным продажам")
            
            # Find highest non-diagonal value in matrix
            max_val = 0.0
            best_pair = ("", "")
            for i, row in enumerate(matrix_data):
                for j, val in enumerate(row):
                    if i != j and val > max_val:
                        max_val = val
                        best_pair = (index_items[i], index_items[j])
            
            if max_val > 0:
                st.markdown(f"""
                <div class="recommendation-card" style="border-left-color: #ec4899;">
                    <h4>🚀 Сильнейшая ассоциация меню: <strong>{best_pair[0]} ➔ {best_pair[1]}</strong></h4>
                    <p>Вероятность покупки: При заказе <strong>{best_pair[0]}</strong>, клиент покупает <strong>{best_pair[1]}</strong> в <strong>{max_val:.1%}</strong> случаев.</p>
                    <p>💡 <strong>Маркетинговое решение:</strong> Создайте комбо-набор с этими позициями или настройте POS-систему (терминал официанта) так, чтобы она автоматически предлагала <em>{best_pair[1]}</em> при выборе <em>{best_pair[0]}</em>.</p>
                </div>
                """, unsafe_allowed_html=True)
        else:
            st.info("⚠️ Недостаточно данных для построения карты ассоциаций. Добавьте больше разнообразных чеков.")

    # 5. TAB: DATA LIST
    with tab_data:
        st.subheader("Журнал транзакций")
        st.markdown("Ниже приведены агрегированные исторические данные о продажах по дням.")
        
        hist_data_full = get_data("/analytics/history?days=100")
        if hist_data_full:
            df_hist_full = pd.DataFrame(hist_data_full)
            df_hist_full["date"] = pd.to_datetime(df_hist_full["date"]).dt.strftime("%d.%m.%Y")
            df_hist_full.columns = ["Дата", "Выручка (₽)", "Количество заказов (шт)"]
            
            st.dataframe(df_hist_full, use_container_width=True, hide_index=True)
        else:
            st.info("Данные отсутствуют.")
