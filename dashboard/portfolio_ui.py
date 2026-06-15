from portfolio_config import CONTACT_NAME, CONTACT_TELEGRAM, CONTACT_EMAIL, CONTACT_PHONE, DEMO_URL


def render_hero_banner():
    demo_line = (
        f'<p style="margin: 8px 0 0 0; font-size: 11px; color: #818cf8;">'
        f'🔗 Живое демо: <a href="{DEMO_URL}" style="color:#818cf8;">{DEMO_URL}</a></p>'
        if DEMO_URL
        else ""
    )
    return f"""
<div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.06) 100%);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 16px;
            padding: 20px 24px;
            margin-bottom: 24px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px;">
        <div style="flex:1; min-width:280px;">
            <p style="margin:0 0 4px 0; font-size:10px; font-weight:800; color:#818cf8; text-transform:uppercase; letter-spacing:1px;">
                Портфолио · Аналитика для кофеен и HoReCa
            </p>
            <h3 style="margin:0 0 8px 0; font-size:18px; font-weight:800; color:#ffffff;">
                Пример отчёта, который я делаю для заведений
            </h3>
            <p style="margin:0; font-size:12px; color:#cbd5e1; line-height:1.6;">
                Это <b>демонстрация</b>, а не готовый сервис. Для реального клиента я разбираю <b>ваши чеки</b>
                из iiko / R-Keeper и готовлю персональные рекомендации: меню, комбо, закупки, средний чек.
                Выберите профиль кофейни ниже или скачайте PDF-пример отчёта.
            </p>
            {demo_line}
        </div>
        <div style="min-width:200px; background:#161b26; border:1px solid #2d3748; border-radius:12px; padding:14px 16px;">
            <p style="margin:0 0 8px 0; font-size:10px; font-weight:800; color:#94a3b8; text-transform:uppercase;">Связаться</p>
            <p style="margin:0 0 4px 0; font-size:12px; color:#ffffff; font-weight:700;">{CONTACT_NAME}</p>
            <p style="margin:0 0 2px 0; font-size:11px; color:#cbd5e1;">Telegram: {CONTACT_TELEGRAM}</p>
            <p style="margin:0; font-size:11px; color:#cbd5e1;">Email: {CONTACT_EMAIL}</p>
            {"<p style='margin:4px 0 0 0; font-size:11px; color:#cbd5e1;'>Тел: " + CONTACT_PHONE + "</p>" if CONTACT_PHONE else ""}
        </div>
    </div>
</div>
"""


def render_services_block():
    return """
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:24px;">
    <div style="background:#161b26; border:1px solid #2d3748; border-radius:14px; padding:16px;">
        <p style="margin:0 0 6px 0; font-size:20px;">📊</p>
        <p style="margin:0 0 4px 0; font-size:12px; font-weight:700; color:#ffffff;">Разбор меню</p>
        <p style="margin:0; font-size:11px; color:#94a3b8; line-height:1.4;">Что продвигать, что убрать, где теряется маржа</p>
    </div>
    <div style="background:#161b26; border:1px solid #2d3748; border-radius:14px; padding:16px;">
        <p style="margin:0 0 6px 0; font-size:20px;">🤝</p>
        <p style="margin:0 0 4px 0; font-size:12px; font-weight:700; color:#ffffff;">Комбо и допродажи</p>
        <p style="margin:0; font-size:11px; color:#94a3b8; line-height:1.4;">Какие наборы запустить, чтобы поднять средний чек</p>
    </div>
    <div style="background:#161b26; border:1px solid #2d3748; border-radius:14px; padding:16px;">
        <p style="margin:0 0 6px 0; font-size:20px;">📦</p>
        <p style="margin:0 0 4px 0; font-size:12px; font-weight:700; color:#ffffff;">Закупки</p>
        <p style="margin:0; font-size:11px; color:#94a3b8; line-height:1.4;">Прогноз спроса и расчёт сырья на неделю</p>
    </div>
    <div style="background:#161b26; border:1px solid #2d3748; border-radius:14px; padding:16px;">
        <p style="margin:0 0 6px 0; font-size:20px;">📈</p>
        <p style="margin:0 0 4px 0; font-size:12px; font-weight:700; color:#ffffff;">Еженедельный отчёт</p>
        <p style="margin:0; font-size:11px; color:#94a3b8; line-height:1.4;">Коротко и по делу — в Telegram или PDF</p>
    </div>
</div>
"""
