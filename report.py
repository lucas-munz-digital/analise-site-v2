"""
Gera o PDF do relatório no formato Deck de Slides Widescreen 16:9 
seguindo a nova identidade visual dark/minimalista da Agência Mestre.
Aplica categorização de urgência (Vermelho x Amarelo) em cada bloco de análise.
"""
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib import colors
from datetime import datetime

BG_DARK = colors.HexColor("#121212")
CARD_BG = colors.HexColor("#1E1E1E")
CARD_LIGHT = colors.HexColor("#292929")
TEXT_WHITE = colors.HexColor("#FFFFFF")
TEXT_MUTED = colors.HexColor("#A0A0A0")

# Cores de Urgência Mestre
COLOR_RED = colors.HexColor("#EF4444")
COLOR_YELLOW = colors.HexColor("#F59E0B")

STYLES = getSampleStyleSheet()

STYLES.add(ParagraphStyle("DeckTitle", parent=STYLES["Normal"], fontSize=28, leading=34, textColor=TEXT_WHITE, fontName="Helvetica-Bold"))
STYLES.add(ParagraphStyle("DeckSubTitle", parent=STYLES["Normal"], fontSize=16, leading=22, textColor=TEXT_MUTED))
STYLES.add(ParagraphStyle("SlideHeader", parent=STYLES["Normal"], fontSize=18, leading=22, textColor=TEXT_WHITE, fontName="Helvetica-Bold"))
STYLES.add(ParagraphStyle("SlideSubHeader", parent=STYLES["Normal"], fontSize=11, leading=15, textColor=TEXT_MUTED))
STYLES.add(ParagraphStyle("CardTitle", parent=STYLES["Normal"], fontSize=12, leading=16, textColor=TEXT_WHITE, fontName="Helvetica-Bold"))
STYLES.add(ParagraphStyle("CardBodyWhite", parent=STYLES["Normal"], fontSize=10, leading=14, textColor=TEXT_WHITE))
STYLES.add(ParagraphStyle("ScoreVal", parent=STYLES["Normal"], fontSize=24, leading=28, textColor=TEXT_WHITE, fontName="Helvetica-Bold", alignment=TA_CENTER))
STYLES.add(ParagraphStyle("ScoreLbl", parent=STYLES["Normal"], fontSize=9, leading=12, textColor=TEXT_MUTED, alignment=TA_CENTER))

POSSIBLE_LOGOS = [
    "agncia_mestre_logo.jpeg", "agncia_mestre_logo.jpg", 
    "logo_mestre.jpg", "logo_mestre.jpeg", "logo_mestre.png"
]


def draw_slide_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    
    logo_file = next((f for f in POSSIBLE_LOGOS if os.path.exists(f)), None)
    if logo_file:
        canvas.drawImage(logo_file, doc.pagesize[0] - 2.8 * cm, doc.pagesize[1] - 1.8 * cm, width=1.6 * cm, height=1.6 * cm, preserveAspectRatio=True)
    
    canvas.setStrokeColor(CARD_BG)
    canvas.setLineWidth(1)
    canvas.line(1.5 * cm, 1.2 * cm, doc.pagesize[0] - 1.5 * cm, 1.2 * cm)
    
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5 * cm, 0.7 * cm, "Agência Mestre | Análise Técnica do Site para Mídia")
    canvas.drawRightString(doc.pagesize[0] - 1.5 * cm, 0.7 * cm, f"Slide {doc.page}")
    canvas.restoreState()


def _make_card(title, body, status=None, bg_color=CARD_BG, width=25*cm):
    content = []
    
    # Adiciona a tag visual Amarelo/Vermelho
    if status == "vermelho":
        badge = "<font color='#EF4444'><b>[🔴 ATENÇÃO IMEDIATA - IMPACTA ANÚNCIOS]</b></font>"
    elif status == "amarelo":
        badge = "<font color='#F59E0B'><b>[🟡 MÉDIO PRAZO - OPORTUNIDADE DE MELHORIA]</b></font>"
    else:
        badge = ""

    header_text = f"<b>{title}</b> {badge}".strip()
    content.append(Paragraph(header_text, STYLES["CardTitle"]))
    content.append(Spacer(1, 4))
    content.append(Paragraph(body, STYLES["CardBodyWhite"]))
    
    border_color = COLOR_RED if status == "vermelho" else (COLOR_YELLOW if status == "amarelo" else bg_color)

    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LINELEFT", (0, 0), (0, -1), 4, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build_pdf(output_path: str, cliente: str, url: str, is_ecommerce: bool,
              pagespeed_mobile: dict, pagespeed_desktop: dict, tags: dict,
              forms_data: dict, usability_issues: list, broken_links: list = None,
              ai_insights: dict = None):

    ai = ai_insights or {}

    doc = SimpleDocTemplate(
        output_path, 
        pagesize=landscape(A4),
        topMargin=1.8 * cm, 
        bottomMargin=1.8 * cm,
        leftMargin=1.5 * cm, 
        rightMargin=1.5 * cm
    )
    story = []

    # SLIDE 1: Capa
    story.append(Spacer(1, 1 * cm))
    logo_file = next((f for f in POSSIBLE_LOGOS if os.path.exists(f)), None)
    
    if logo_file:
        story.append(Image(logo_file, width=3.2 * cm, height=3.2 * cm, kind='proportional'))
        story.append(Spacer(1, 0.5 * cm))
    
    story.append(Paragraph("Análise do Site para Mídia", STYLES["DeckTitle"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Projeto: <b>{cliente}</b>", STYLES["DeckSubTitle"]))
    story.append(Paragraph(f"URL: {url}", STYLES["CardBodyWhite"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(datetime.now().strftime("Gerado em %d/%m/%Y"), STYLES["CardBodyWhite"]))
    story.append(PageBreak())

    # SLIDE 2: Parecer Executivo
    story.append(Paragraph("01 | PARECER EXECUTIVO", STYLES["SlideSubHeader"]))
    story.append(Paragraph("Diagnóstico Geral de Mídia & Prontidão do Site", STYLES["SlideHeader"]))
    story.append(Spacer(1, 12))

    resumo = ai.get("resumo_executivo", "Análise executiva não disponível.")
    story.append(_make_card("Visão Geral do Consultor Sênior", resumo, bg_color=CARD_BG, width=25*cm))
    story.append(Spacer(1, 10))

    c1 = _make_card("Objetivo do Documento", "Detectar oportunidades no site para maximizar o ROI e o Índice de Qualidade das campanhas.", CARD_LIGHT, width=12*cm)
    c2 = _make_card("Legenda de Urgência", "🔴 <b>Atenção Imediata:</b> Impacta diretamente os resultados/anúncios.<br/>🟡 <b>Médio/Longo Prazo:</b> Oportunidades para otimização contínua.", CARD_LIGHT, width=12.5*cm)
    
    grid_table = Table([[c1, c2]], colWidths=[12.3*cm, 12.7*cm])
    grid_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(grid_table)
    story.append(PageBreak())

    # SLIDE 3: Performance
    story.append(Paragraph("02 | PERFORMANCE & CORE WEB VITALS", STYLES["SlideSubHeader"]))
    story.append(Paragraph("Desempenho do Site e Impacto no Custo por Clique (CPC)", STYLES["SlideHeader"]))
    story.append(Spacer(1, 10))

    score_m = pagespeed_mobile.get("scores", {}).get("performance", "-")
    score_d = pagespeed_desktop.get("scores", {}).get("performance", "-")

    sc_m = Table([[Paragraph(f"<b>{score_m}</b>", STYLES["ScoreVal"])], [Paragraph("Mobile Score", STYLES["ScoreLbl"])]], colWidths=[5*cm])
    sc_m.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CARD_BG), ("PADDING", (0, 0), (-1, -1), 6)]))

    sc_d = Table([[Paragraph(f"<b>{score_d}</b>", STYLES["ScoreVal"])], [Paragraph("Desktop Score", STYLES["ScoreLbl"])]], colWidths=[5*cm])
    sc_d.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CARD_BG), ("PADDING", (0, 0), (-1, -1), 6)]))

    perf_ai = ai.get("consideracoes_desempenho", "Consulte os números abaixo.")
    perf_status = ai.get("status_desempenho", "vermelho")
    card_perf = _make_card("Impacto na Mídia Paga & Rejeição", perf_ai, status=perf_status, bg_color=CARD_BG, width=14.5*cm)

    scores_row = Table([[sc_m, sc_d, card_perf]], colWidths=[5.2*cm, 5.2*cm, 14.6*cm])
    scores_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(scores_row)
    story.append(Spacer(1, 10))

    opps = pagespeed_mobile.get("opportunities", [])
    opp_text = "<br/>".join([f"• <b>{o['title']}</b>" for o in opps[:4]]) if opps else "Sem grandes oportunidades detectadas."
    story.append(_make_card("Principais Gargalos Detectados no Mobile", opp_text, status="vermelho" if score_m < 50 else "amarelo", bg_color=CARD_LIGHT, width=25*cm))
    story.append(PageBreak())

    # SLIDE 4: Tracking
    story.append(Paragraph("03 | MENSURAÇÃO & TRACKING", STYLES["SlideSubHeader"]))
    story.append(Paragraph("Auditoria do Ecossistema de Rastreamento de Tags", STYLES["SlideHeader"]))
    story.append(Spacer(1, 10))

    tags_ai = ai.get("consideracoes_tags", "Consulte a tabela abaixo.")
    tags_status = ai.get("status_tags", "amarelo")
    story.append(_make_card("Diagnóstico de Tracking pelo Especialista", tags_ai, status=tags_status, bg_color=CARD_BG, width=25*cm))
    story.append(Spacer(1, 10))

    tag_rows = [
        [Paragraph("<b>Ferramenta</b>", STYLES["CardTitle"]), Paragraph("<b>IDs Identificados</b>", STYLES["CardTitle"])],
        [Paragraph("Google Tag Manager (GTM)", STYLES["CardBodyWhite"]), Paragraph(", ".join(tags.get("gtm_containers", [])) or "Não encontrado 🔴", STYLES["CardBodyWhite"])],
        [Paragraph("Google Analytics 4 (GA4)", STYLES["CardBodyWhite"]), Paragraph(", ".join(tags.get("ga4_properties", [])) or "Não encontrado 🔴", STYLES["CardBodyWhite"])],
        [Paragraph("Google Ads", STYLES["CardBodyWhite"]), Paragraph(", ".join(tags.get("google_ads_ids", [])) or "Não encontrado 🔴", STYLES["CardBodyWhite"])],
        [Paragraph("Meta Pixel", STYLES["CardBodyWhite"]), Paragraph(", ".join(tags.get("meta_pixel_ids", [])) or "Não encontrado 🔴", STYLES["CardBodyWhite"])]
    ]
    t_tags = Table(tag_rows, colWidths=[8*cm, 17*cm])
    t_tags.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CARD_LIGHT),
        ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_tags)
    story.append(PageBreak())

    # SLIDE 5: Conversão & CRO
    story.append(Paragraph("04 | CONVERSÃO & CRO", STYLES["SlideSubHeader"]))
    story.append(Paragraph("Mapeamento de Captura de Leads e Thank You Pages", STYLES["SlideHeader"]))
    story.append(Spacer(1, 10))

    conv_ai = ai.get("consideracoes_conversao", "Consulte os formulários abaixo.")
    conv_status = ai.get("status_conversao", "vermelho")
    story.append(_make_card("Parecer de Conversão & UX", conv_ai, status=conv_status, bg_color=CARD_BG, width=25*cm))
    story.append(Spacer(1, 10))

    forms = forms_data.get("forms", [])
    if not forms:
        story.append(_make_card("Alertas de Formulários", "Nenhum formulário HTML estático ou script de automação (RD Station) foi detectado.", status="vermelho", bg_color=CARD_LIGHT, width=25*cm))
    else:
        for f in forms[:3]:
            ty_status = "✅ Página de Agradecimento Identificada" if f.get("has_thank_you_page") else "🔴 Sem Página de Agradecimento (Página de Sucesso/Popup)"
            f_body = f"<b>Tipo:</b> {f.get('tipo')} | <b>Destino:</b> {f.get('destino')}<br/><b>Status de Tracking:</b> {ty_status}"
            story.append(_make_card(f"Formulário #{f['id']}", f_body, status="amarelo" if f.get("has_thank_you_page") else "vermelho", bg_color=CARD_LIGHT, width=25*cm))
            story.append(Spacer(1, 6))

    doc.build(story, onFirstPage=draw_slide_background, onLaterPages=draw_slide_background)
