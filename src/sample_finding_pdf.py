"""Tek sayfalık örnek bulgu PDF'i — alıcıya gösterilen şey bu.
Üretim: .venv/bin/python src/sample_finding_pdf.py
Çıktı:  out/sample-finding.pdf
"""
from __future__ import annotations
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
PDF = os.path.join(OUT, "sample-finding.pdf")

INK = colors.HexColor("#1d2731")
MUTED = colors.HexColor("#5b6b7a")
ACCENT = colors.HexColor("#c1440e")
RULE = colors.HexColor("#d8dee4")
W, H = A4


def main() -> None:
    c = canvas.Canvas(PDF, pagesize=A4)
    c.setTitle("Spare parts stock policy audit — sample finding")

    x = 20 * mm
    y = H - 20 * mm

    # başlık
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(x, y, "Spare parts stock policy audit")
    y -= 7 * mm
    c.setFont("Helvetica", 10.5)
    c.setFillColor(MUTED)
    c.drawString(x, y, "Sample finding — one page, produced from two years of part movement history")
    y -= 5 * mm
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.line(x, y, W - x, y)
    y -= 8 * mm

    # veri kaynağı
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x, y, "What this example is based on")
    y -= 5 * mm
    c.setFont("Helvetica", 9.5)
    c.setFillColor(MUTED)
    for line in [
        "Open benchmark data: 2,674 automotive part numbers, 51 months of monthly movement",
        "(Monash Time Series Forecasting Archive, CC-BY 4.0). No client data was used.",
    ]:
        c.drawString(x, y, line)
        y -= 4.6 * mm
    y -= 4 * mm

    # bulgu kutuları
    findings = [
        ("75.9%", "of all month-part observations are zero.",
         "Average-consumption logic is answering a different question."),
        ("99.4%", "of parts fall outside the 'smooth' region.",
         "One model applied to the whole catalogue is an unearned claim."),
        ("16.6%", "lower forecast error than the ERP baseline.",
         "Achieved by selecting the method per part, validated out-of-sample."),
        ("698", "parts had no movement in the last 12 months.",
         "A cash-release list that needs no forecasting at all."),
    ]
    box_h = 15 * mm
    for big, head, sub in findings:
        c.setFillColor(colors.HexColor("#f6f8fa"))
        c.rect(x, y - box_h, W - 2 * x, box_h, stroke=0, fill=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(x + 4 * mm, y - 6.5 * mm, big)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x + 26 * mm, y - 6.2 * mm, head)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.8)
        c.drawString(x + 26 * mm, y - 11 * mm, sub)
        y -= box_h + 2.5 * mm

    y -= 3 * mm

    # karar cümlesi
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x, y, "The decision this produces")
    y -= 5.5 * mm
    c.setFont("Helvetica-Bold", 11.5)
    c.setFillColor(ACCENT)
    c.drawString(x, y, "Going from 95% to 99% fill rate costs five times the capital.")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(x, y, "95% fill = EUR 59,400 tied up   ·   99% fill = EUR 288,000 tied up   "
                       "(200 fastest-moving parts, 2-month lead time)")
    y -= 6 * mm

    # grafik
    img = os.path.join(OUT, "chart_service_capital_en.png")
    if os.path.exists(img):
        ir = ImageReader(img)
        iw, ih = ir.getSize()
        draw_w = W - 2 * x
        draw_h = draw_w * ih / iw
        max_h = 62 * mm
        if draw_h > max_h:
            draw_h = max_h
            draw_w = draw_h * iw / ih
        c.drawImage(ir, x, y - draw_h, width=draw_w, height=draw_h, mask="auto")
        y -= draw_h + 6 * mm

    # ne istiyorum
    c.setStrokeColor(RULE)
    c.line(x, y, W - x, y)
    y -= 6 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(x, y, "To draw this curve with your own part numbers")
    y -= 5 * mm
    c.setFont("Helvetica", 9.3)
    c.setFillColor(MUTED)
    for line in [
        "One CSV export from your ERP: part number, date, quantity moved. Two to three years.",
        "Optional: unit cost and lead time. No sensors, no integration, no pilot server.",
        "Turnaround for one part family: 2 working days, free of charge.",
    ]:
        c.drawString(x, y, line)
        y -= 4.6 * mm

    # alt bilgi
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawString(x, 15 * mm, "Yigit Celik  ·  yigit@yigitc.tech  ·  yigitc.tech")
    c.drawRightString(W - x, 15 * mm, "Method and code: github.com/yigitckk/intermittent-demand-audit")

    c.showPage()
    c.save()
    print("yazildi:", PDF)


if __name__ == "__main__":
    main()
