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


def _score_table(scores: dict):
    labels = ["Performance", "Acessibilidade", "Boas práticas", "SEO"]
    keys = ["performance", "accessibility", "best_practices", "seo"]
    row_vals = []
    row_colors = []
    for k in keys:
        v = scores.get(k)
        row_vals.append(str(v) if v is not None else "-")
        if v is None:
            row_colors.append(colors.HexColor("#868E96"))
        elif v >= 90:
            row_colors.append(GREEN)
        elif v >= 50:
            row_colors.append(YELLOW)
        else:
            row_colors.append(RED)

    data = [labels, row_vals]
    t = Table(data, colWidths=[4 * cm] * 4)
    style = [
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), GRAY),
        ("FONTSIZE", (0, 1), (-1, 1), 22),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#DDDDDD")),
    ]
    for i, c in enumerate(row_colors):
        style.append(("TEXTCOLOR", (i, 1), (i, 1), c))
    t.setStyle(TableStyle(style))
    return t


def _vitals_table(vitals: dict):
    data = [
        ["FCP", vitals.get("fcp", "-")],
        ["LCP", vitals.get("lcp", "-")],
        ["Total Blocking Time", vitals.get("tbt", "-")],
        ["CLS", vitals.get("cls", "-")],
        ["Speed Index", vitals.get("speed_index", "-")],
    ]
    t = Table(data, colWidths=[6 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#EEEEEE")),
    ]))
    return t


def build_pdf(output_path: str, cliente: str, url: str, is_ecommerce: bool,
              pagespeed_mobile: dict, pagespeed_desktop: dict, tags: dict,
              forms_data: dict, usability_issues: list):

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

    # Legenda
    story.append(Paragraph("Legenda", STYLES["H2c"]))
    legend_rows = []
    for sev, desc in [("critico", "Itens que precisam de atenção imediata — impactam diretamente os resultados."),
                       ("medio", "Itens de melhoria a médio/longo prazo."),
                       ("baixo", "Observações gerais, sem urgência.")]:
        legend_rows.append([
            Table([[""]], colWidths=[0.4 * cm], rowHeights=[0.4 * cm],
                  style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), _severity_color(sev))])),
            Paragraph(desc, STYLES["Body"]),
        ])
    lt = Table(legend_rows, colWidths=[0.8 * cm, 15 * cm])
    lt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(lt)
    story.append(Spacer(1, 0.5 * cm))

    # PageSpeed
    for label, data in [("Mobile", pagespeed_mobile), ("Desktop", pagespeed_desktop)]:
        story.append(Paragraph(f"Desempenho do Site — {label}", STYLES["H2c"]))
        if "error" in data:
            story.append(Paragraph(f"Não foi possível obter os dados: {data['error']}", STYLES["Body"]))
        else:
            story.append(_score_table(data["scores"]))
            story.append(Spacer(1, 8))
            story.append(_vitals_table(data["vitals"]))
            story.append(Spacer(1, 8))
            if data["opportunities"]:
                story.append(Paragraph("<b>Principais oportunidades de melhoria:</b>", STYLES["Body"]))
                for opp in data["opportunities"]:
                    saving = f" (economia estimada de {round(opp['savings_ms']/1000, 1)}s)" if opp["savings_ms"] else ""
                    story.append(Paragraph(f"• {opp['title']}{saving}", STYLES["Small"]))
        story.append(Spacer(1, 14))
    story.append(PageBreak())

    # Tags
    story.append(Paragraph("Tags e Scripts de Rastreamento", STYLES["H2c"]))

    def _fmt_ids(ids, only_via_gtm):
        if not ids:
            return "não encontrado"
        parts = [f"{i} (via GTM)" if i in only_via_gtm else i for i in ids]
        return ", ".join(parts)

    rows = [
        ["GTM", ", ".join(tags["gtm_containers"]) or "não encontrado"],
        ["GA4", _fmt_ids(tags["ga4_properties"], tags.get("ga4_only_via_gtm", []))],
        ["Google Ads", _fmt_ids(tags["google_ads_ids"], tags.get("google_ads_only_via_gtm", []))],
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
    if tags.get("ga4_only_via_gtm") or tags.get("google_ads_only_via_gtm"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "<font size=8 color='#868E96'>(via GTM) = tag configurada dentro do Google Tag Manager, "
            "não solta no HTML da página — só é detectável lendo o container publicado.</font>",
            STYLES["Small"]))
    story.append(Spacer(1, 10))
    for issue in tags["issues"]:
        sev = "critico" if ("duplicad" in issue.lower() or "nenhuma tag" in issue.lower()) else "medio"
        story.extend(_issue_block("Achado", sev, issue))
    story.append(PageBreak())

    # Formulários
    story.append(Paragraph("Formulários e Conversão", STYLES["H2c"]))
    if not forms_data["forms"]:
        story.append(Paragraph("Nenhum formulário &lt;form&gt; foi encontrado no HTML estático da página.", STYLES["Body"]))
    for i, f in enumerate(forms_data["forms"], start=1):
        story.append(Paragraph(f"<b>Formulário {i}</b> — {f['num_campos']} campo(s): {', '.join(f['fields']) or '-'}", STYLES["Body"]))
        story.append(Paragraph(f"Destino: {f['destino']} → <font size=8>{f['action']}</font>", STYLES["Small"]))
        story.append(Spacer(1, 8))
        if "WhatsApp" in f["destino"]:
            story.extend(_issue_block("Lead não passa por CRM",
                                       "critico",
                                       "O formulário direciona para o WhatsApp em vez de um endpoint de CRM. "
                                       "Recomenda-se confirmar armazenamento dos dados e avaliar integração direta com o CRM."))
    if forms_data["duplicated_cta_targets"]:
        story.extend(_issue_block("Botões de CTA duplicados",
                                   "medio",
                                   "Mais de um botão/CTA aponta para o mesmo destino "
                                   f"({', '.join(forms_data['duplicated_cta_targets'])}), dificultando identificar a origem do clique/lead."))
    story.append(PageBreak())

    # Usabilidade
    story.append(Paragraph("Usabilidade e Design (checagem automática)", STYLES["H2c"]))
    if not usability_issues:
        story.append(Paragraph("Nenhum ponto crítico identificado nas checagens automáticas.", STYLES["Body"]))
    for sev, text in usability_issues:
        story.extend(_issue_block("Achado", sev, text))

    # E-commerce - checklist manual
    if is_ecommerce:
        story.append(PageBreak())
        story.append(Paragraph("Fluxo de Compra (E-commerce) — preenchimento manual", STYLES["H2c"]))
        story.append(Paragraph(
            "Este site foi identificado como E-commerce. A verificação do fluxo de compra "
            "(carrinho, checkout e eventos de conversão) exige navegação manual pelo analista. "
            "Preencha os itens abaixo durante a auditoria:", STYLES["Body"]))
        story.append(Spacer(1, 8))
        checklist = [
            "Evento add_to_cart dispara corretamente no dataLayer/GTM?",
            "Evento begin_checkout dispara corretamente?",
            "Evento purchase dispara corretamente com valor e ID do pedido?",
            "Existe página de agradecimento com URL própria após a compra?",
            "O checkout funciona em mobile sem erros?",
            "Métodos de pagamento configurados estão funcionando (teste)?",
            "Frete é calculado corretamente?",
            "Cupons de desconto (se houver) funcionam?",
        ]
        rows = []
        for item in checklist:
            rows.append([
                Table([[""]], colWidths=[0.5 * cm], rowHeights=[0.5 * cm],
                      style=TableStyle([("BOX", (0, 0), (-1, -1), 0.8, GRAY)])),
                Paragraph(item, STYLES["Body"]),
            ])
        ct = Table(rows, colWidths=[1 * cm, 14.5 * cm])
        ct.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        story.append(ct)
        story.append(Spacer(1, 14))
        story.append(Paragraph("Observações do analista:", STYLES["Body"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceBefore=20, spaceAfter=20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceBefore=20, spaceAfter=20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceBefore=20, spaceAfter=20))

    doc.build(story)
