"""
Gera o PDF final do relatório a partir dos dados coletados pelo analyzer.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib import colors
from datetime import datetime

RED = colors.HexColor("#E03131")
YELLOW = colors.HexColor("#F5B800")
GRAY = colors.HexColor("#4A4A48")
DARK = colors.HexColor("#1A1A1A")
GREEN = colors.HexColor("#2F9E44")

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("H1c", parent=STYLES["Heading1"], fontSize=20, textColor=DARK, spaceAfter=4))
STYLES.add(ParagraphStyle("H2c", parent=STYLES["Heading2"], fontSize=14, textColor=DARK, spaceBefore=10, spaceAfter=6))
STYLES.add(ParagraphStyle("Body", parent=STYLES["Normal"], fontSize=10.5, leading=15, textColor=DARK, alignment=TA_LEFT))
STYLES.add(ParagraphStyle("Small", parent=STYLES["Normal"], fontSize=9, leading=13, textColor=GRAY))
STYLES.add(ParagraphStyle("Tag", parent=STYLES["Normal"], fontSize=9, textColor=colors.white))


def _severity_color(sev):
    return {"critico": RED, "medio": YELLOW, "baixo": colors.HexColor("#868E96")}.get(sev, GRAY)


def _severity_label(sev):
    return {"critico": "ATENÇÃO IMEDIATA", "medio": "MÉDIO/LONGO PRAZO", "baixo": "OBSERVAÇÃO"}.get(sev, "")


def _issue_block(title, sev, text):
    color = _severity_color(sev)
    tag = Table([[Paragraph(f"<b>{_severity_label(sev)}</b>", STYLES["Tag"])]], colWidths=[4.5 * cm])
    tag.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [
        tag,
        Spacer(1, 4),
        Paragraph(f"<b>{title}</b>", STYLES["H2c"]),
        Paragraph(text, STYLES["Body"]),
        Spacer(1, 10),
    ]


def build_pdf(output_path: str, cliente: str, url: str, is_ecommerce: bool,
              pagespeed_mobile: dict, pagespeed_desktop: dict, tags: dict,
              forms_data: dict, usability_issues: list, broken_links: list = None):

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    story = []

    # Capa
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Análise Técnica do Site", STYLES["H1c"]))
    story.append(Paragraph(cliente, ParagraphStyle("sub", parent=STYLES["Body"], fontSize=14, textColor=GRAY)))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(url, STYLES["Small"]))
    story.append(Paragraph(datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M"), STYLES["Small"]))
    story.append(PageBreak())

    # PageSpeed
    for label, data in [("Mobile", pagespeed_mobile), ("Desktop", pagespeed_desktop)]:
        story.append(Paragraph(f"Desempenho do Site — {label}", STYLES["H2c"]))
        if "error" in data:
            story.append(Paragraph(f"Não foi possível obter os dados: {data['error']}", STYLES["Body"]))
        else:
            interp = data.get("interpretation", {})
            if interp.get("level") == "red":
                story.extend(_issue_block("Atenção no Desempenho", "critico", interp["text"]))
            elif interp.get("level") == "orange":
                story.extend(_issue_block("Oportunidade de Melhoria", "medio", interp["text"]))
            elif interp.get("level") == "none":
                story.append(Paragraph(f"<b>Status:</b> {interp['text']}", STYLES["Body"]))
                story.append(Spacer(1, 6))

            if data["opportunities"]:
                story.append(Paragraph("<b>Principais oportunidades de melhoria:</b>", STYLES["Body"]))
                for opp in data["opportunities"]:
                    saving = f" (economia estimada de {round(opp['savings_ms']/1000, 1)}s)" if opp["savings_ms"] else ""
                    story.append(Paragraph(f"• {opp['title']}{saving}", STYLES["Small"]))
        story.append(Spacer(1, 14))
    story.append(PageBreak())

    # Tags
    story.append(Paragraph("Tags e Scripts de Rastreamento", STYLES["H2c"]))
    rows = [
        ["GTM", ", ".join(tags["gtm_containers"]) or "não encontrado"],
        ["GA4", ", ".join(tags["ga4_properties"]) or "não encontrado"],
        ["Google Ads", ", ".join(tags["google_ads_ids"]) or "não encontrado"],
        ["Meta Pixel", ", ".join(tags["meta_pixel_ids"]) or "não encontrado"],
    ]
    tt = Table(rows, colWidths=[4 * cm, 12 * cm])
    tt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#EEEEEE")),
    ]))
    story.append(tt)
    story.append(Spacer(1, 10))

    # Formulários
    story.append(Paragraph("Formulários e Conversão", STYLES["H2c"]))
    if not forms_data["forms"]:
        story.append(Paragraph("Nenhum formulário &lt;form&gt; foi encontrado no HTML estático da página.", STYLES["Body"]))
    for f in forms_data["forms"]:
        story.append(Paragraph(f"<b>Formulário #{f['id']}</b> — {f['num_campos']} campo(s): {', '.join(f['fields']) or '-'}", STYLES["Body"]))
        story.append(Paragraph(f"Destino: {f['destino']} → <font size=8>{f['action']}</font>", STYLES["Small"]))
        if not f.get("has_thank_you_page"):
            story.extend(_issue_block(
                f"Formulário #{f['id']} sem Página de Agradecimento",
                "medio",
                f"Página de agradecimento não encontrada no formulário #{f['id']}. Isto não impossibilita o tracking do formulário, porém implica na criação de soluções que estão sujeitas a maior taxa de erro de contabilização. (form_submit, click_text, etc)"
            ))
        story.append(Spacer(1, 8))

    # Links Quebrados
    if broken_links:
        story.append(Paragraph("Links Quebrados Detectados", STYLES["H2c"]))
        for bl in broken_links:
            story.extend(_issue_block("Link Indisponível", "critico", f"URL quebrada ({bl['status']}): {bl['url']}"))

    # Usabilidade
    story.append(Paragraph("Usabilidade e Design (checagem automática)", STYLES["H2c"]))
    for sev, text in usability_issues:
        story.extend(_issue_block("Achado", sev, text))

    doc.build(story)
