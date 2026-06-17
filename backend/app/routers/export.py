from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import os
from datetime import datetime
from fpdf import FPDF
from app import crud, models
from app.database import get_db

router = APIRouter(prefix="/export", tags=["export"])

FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "DejaVuSans.ttf")

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
    return f"${value:,.2f}"

@router.get("/pdf")
def export_pdf_report(preset_name: str = "Analytics Report", db: Session = Depends(get_db)):
    """Generate and return a PDF report based on current database state."""
    # 1. Fetch Stats
    from sqlalchemy import func
    stats = db.query(
        func.sum(models.Order.total_amount).label("total_revenue"),
        func.count(models.Order.id).label("total_orders")
    ).first()
    total_revenue = float(stats.total_revenue or 0.0)
    total_orders = int(stats.total_orders or 0)
    avg_check = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    total_qty = db.query(func.sum(models.OrderItem.quantity)).scalar() or 0
    avg_items_per_check = round(total_qty / total_orders, 1) if total_orders > 0 else 0.0

    # 2. Fetch Menu Analysis
    menu_rows = [m.__dict__ for m in crud.get_menu_analysis(db)]

    # 3. Build PDF
    pdf = ReportPDF()
    pdf.add_page()

    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "GastroSense AI Analytics Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, preset_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%Y-%m-%d')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # KPI
    pdf.section_title("Performance Overview (180 Days)")
    pdf.bullet(f"Total Revenue: {_fmt_rub(total_revenue)}")
    pdf.bullet(f"Total Orders: {total_orders:,}")
    pdf.bullet(f"Average Check: {_fmt_rub(avg_check)}")
    pdf.bullet(f"Avg Items per Check: {avg_items_per_check:.1f}")
    pdf.ln(4)

    # Menu
    pdf.section_title("Menu Engineering (BCG Matrix)")
    if menu_rows:
        stars = [r for r in menu_rows if r.get("cluster_label") == "Stars"]
        dogs = [r for r in menu_rows if r.get("cluster_label") == "Dogs"]
        puzzles = [r for r in menu_rows if r.get("cluster_label") == "Puzzles"]
        workhorses = [r for r in menu_rows if r.get("cluster_label") == "Workhorses"]

        if stars:
            pdf.bullet(f"Stars (High Vol / High Margin): {', '.join(r['item_name'] for r in stars[:3])}")
        if workhorses:
            pdf.bullet(f"Workhorses (High Vol / Low Margin): {', '.join(r['item_name'] for r in workhorses[:2])}")
        if puzzles:
            pdf.bullet(f"Puzzles (Low Vol / High Margin - Needs Promo): {', '.join(r['item_name'] for r in puzzles[:2])}")
        if dogs:
            pdf.bullet(f"Dogs (Consider Removing): {', '.join(r['item_name'] for r in dogs[:2])}")
    else:
        pdf.body_text("No menu data available.")

    pdf.ln(8)
    pdf.section_title("AI Copilot Recommendations")
    pdf.body_text("For customized cross-selling bundles and deep insights, interact with the GastroSense AI Copilot on the dashboard.")

    # Return PDF response
    pdf_bytes = bytes(pdf.output())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={preset_name.replace(' ', '_')}_Report.pdf"}
    )
