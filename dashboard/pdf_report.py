import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fpdf import FPDF

from portfolio_config import CONTACT_NAME, CONTACT_TELEGRAM, CONTACT_EMAIL


FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", FONT_PATH)
        self.set_auto_page_break(auto=True, margin=18)

    def section_title(self, title: str):
        self.set_font("DejaVu", "", 13)
        self.set_text_color(30, 41, 59)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def body_text(self, text: str, size: int = 10):
        self.set_font("DejaVu", "", size)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text: str):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 6, f"  •  {text}")
        self.ln(1)


def _fmt_rub(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def generate_report_pdf(
    venue_name: str,
    stats: Dict[str, Any],
    menu_rows: List[Dict[str, Any]],
    combo_recommendation: Optional[str] = None,
    procurement_lines: Optional[List[str]] = None,
    action_items: Optional[List[str]] = None,
) -> bytes:
    pdf = ReportPDF()
    pdf.add_page()

    # Header
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "GastroSense · Пример аналитического отчёта", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, venue_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(
        0,
        6,
        f"Дата отчёта: {datetime.now().strftime('%d.%m.%Y')}  ·  Демо-данные для портфолио",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(6)

    pdf.body_text(
        "Ниже — пример того, как выглядит еженедельный разбор для заведения. "
        "Для реального клиента все цифры строятся на выгрузке чеков из iiko / R-Keeper."
    )

    # KPI
    pdf.section_title("Ключевые показатели (за период)")
    kpi_lines = [
        f"Выручка: {_fmt_rub(stats.get('total_revenue', 0))}",
        f"Заказов: {stats.get('total_orders', 0):,}".replace(",", " "),
        f"Средний чек: {_fmt_rub(stats.get('avg_check', 0))}",
        f"Позиций в чеке (среднее): {stats.get('avg_items_per_check', 0):.1f}",
    ]
    for line in kpi_lines:
        pdf.bullet(line)
    pdf.ln(4)

    # Menu
    pdf.section_title("Анализ меню")
    if menu_rows:
        stars = [r for r in menu_rows if r.get("cluster_label") == "Stars"]
        dogs = [r for r in menu_rows if r.get("cluster_label") == "Dogs"]
        puzzles = [r for r in menu_rows if r.get("cluster_label") == "Puzzles"]
        workhorses = [r for r in menu_rows if r.get("cluster_label") == "Workhorses"]

        if stars:
            pdf.bullet(f"Звёзды (держать в топе): {', '.join(r['item_name'] for r in stars[:3])}")
        if workhorses:
            pdf.bullet(
                f"Лошадки (высокий спрос, смотреть маржу): "
                f"{', '.join(r['item_name'] for r in workhorses[:2])}"
            )
        if puzzles:
            pdf.bullet(
                f"Загадки (высокая маржа, мало продаж — продвигать): "
                f"{', '.join(r['item_name'] for r in puzzles[:2])}"
            )
        if dogs:
            pdf.bullet(
                f"Кандидаты на вывод из меню: {', '.join(r['item_name'] for r in dogs[:2])}"
            )
    else:
        pdf.body_text("Нет данных по меню.")

    pdf.ln(4)

    # Combo
    pdf.section_title("Рекомендация по комбо")
    pdf.body_text(combo_recommendation or "Сформируется на основе связей в чеках клиента.")

    # Procurement
    pdf.section_title("Закупки на неделю (прогноз)")
    if procurement_lines:
        for line in procurement_lines:
            pdf.bullet(line)
    else:
        pdf.body_text("Расчёт сырья — по прогнозу заказов на 7 дней.")

    # Actions
    pdf.section_title("План действий")
    items = action_items or ["Уточнить рекомендации после разбора реальных чеков заведения."]
    for item in items:
        pdf.bullet(item)

    pdf.ln(8)
    pdf.section_title("Контакты аналитика")
    pdf.body_text(f"{CONTACT_NAME}")
    pdf.body_text(f"Telegram: {CONTACT_TELEGRAM}")
    pdf.body_text(f"Email: {CONTACT_EMAIL}")
    pdf.body_text("Первый мини-разбор чеков — бесплатно.")

    return pdf.output()
