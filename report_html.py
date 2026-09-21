"""
Gera o preview HTML do relatório para exibição direta na tela do Streamlit.
"""
from datetime import datetime


def build_html_report(cliente: str, url: str, is_ecommerce: bool,
                       pagespeed_mobile: dict, pagespeed_desktop: dict,
                       tags: dict, forms_data: dict, usability_issues: list) -> str:

    def get_score_class(score):
        if score is None:
            return "neutral"
        if score >= 90:
            return "good"
        if score >= 50:
            return "average"
        return "poor"

    def render_pagespeed_block(title, data):
        if "error" in data:
            return f'<div class="error-box"><b>{title}:</b> Não foi possível obter dados ({data["error"]})</div>'
        
        scores = data.get("scores", {})
        vitals = data.get("vitals", {})
        opportunities = data.get("opportunities", [])

        html = f'<h3>Desempenho — {title}</h3>'
        html += '<div class="scores-grid">'
        for label, key in [("Performance", "performance"), ("Acessibilidade", "accessibility"),
                           ("Boas Práticas", "best_practices"), ("SEO", "seo")]:
            val = scores.get(key, "-")
            cls = get_score_class(val)
            html += f'<div class="score-card {cls}"><span class="score-val">{val}</span><span class="score-lbl">{label}</span></div>'
        html += '</div>'

        html += '<table class="data-table"><thead><tr><th>Core Web Vital</th><th>Valor</th></tr></thead><tbody>'
        for k, v in [("First Contentful Paint (FCP)", vitals.get("fcp")),
                     ("Largest Contentful Paint (LCP)", vitals.get("lcp")),
                     ("Total Blocking Time (TBT)", vitals.get("tbt")),
                     ("Cumulative Layout Shift (CLS)", vitals.get("cls")),
                     ("Speed Index", vitals.get("speed_index"))]:
            html += f'<tr><td>{k}</td><td><b>{v or "-"}</b></td></tr>'
        html += '</tbody></table>'

        if opportunities:
            html += '<p><b>Principais Oportunidades:</b></p><ul>'
            for opp in opportunities:
                saving = f' (economia de ~{round(opp["savings_ms"]/1000, 1)}s)' if opp.get("savings_ms") else ''
                html += f'<li>{opp["title"]}{saving}</li>'
            html += '</ul>'
        return html

    # Tags
    tags_html = '<h3>Tags e Scripts de Rastreamento</h3><table class="data-table"><tbody>'
    for name, key in [("GTM", "gtm_containers"), ("GA4", "ga4_properties"),
                      ("Google Ads", "google_ads_ids"), ("Meta Pixel", "meta_pixel_ids")]:
        items = tags.get(key, [])
        val = ", ".join(items) if items else "não encontrado"
        tags_html += f'<tr><td><b>{name}</b></td><td>{val}</td></tr>'
    tags_html += '</tbody></table>'

    if tags.get("issues"):
        for issue in tags["issues"]:
            tags_html += f'<div class="issue-card critical"><b>Achado:</b> {issue}</div>'

    # Formulários
    forms_html = '<h3>Formulários e Conversão</h3>'
    if not forms_data.get("forms"):
        forms_html += '<p>Nenhum formulário &lt;form&gt; detectado no HTML estático.</p>'
    else:
        for i, f in enumerate(forms_data["forms"], 1):
            forms_html += f'''<div class="form-box">
                <b>Formulário {i}</b> ({f["num_campos"]} campos): {", ".join(f["fields"]) or "-"}<br>
                <small>Destino: <b>{f["destino"]}</b> → {f["action"]}</small>
            </div>'''
            if "WhatsApp" in f["destino"]:
                forms_html += '<div class="issue-card critical"><b>Atenção:</b> Formulário envia direto para WhatsApp sem registrar no CRM.</div>'

    # Usabilidade
    usability_html = '<h3>Usabilidade e Design</h3>'
    if not usability_issues:
        usability_html += '<p>Nenhum problema crítico identificado nas checagens automáticas.</p>'
    else:
        for sev, text in usability_issues:
            cls = "critical" if sev == "critico" else ("warning" if sev == "medio" else "info")
            usability_html += f'<div class="issue-card {cls}"><b>[{sev.upper()}]</b> {text}</div>'

    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1A1A1A; padding: 20px; background: #FAFAFA; }}
    .container {{ max-width: 800px; margin: 0 auto; background: #FFF; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    h1 {{ font-size: 24px; margin-bottom: 4px; color: #111; }}
    .subtitle {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
    h3 {{ font-size: 18px; border-bottom: 2px solid #EEE; padding-bottom: 6px; margin-top: 28px; }}
    .scores-grid {{ display: flex; gap: 12px; margin-bottom: 16px; }}
    .score-card {{ flex: 1; text-align: center; padding: 12px; border-radius: 6px; background: #F8F9FA; border: 1px solid #E9ECEF; }}
    .score-val {{ display: block; font-size: 26px; font-weight: bold; }}
    .score-lbl {{ font-size: 12px; color: #666; }}
    .good {{ color: #2F9E44; }} .average {{ color: #F5B800; }} .poor {{ color: #E03131; }} .neutral {{ color: #868E96; }}
    .data-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
    .data-table th, .data-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #EEE; }}
    .data-table th {{ background: #F8F9FA; color: #555; }}
    .issue-card {{ padding: 10px 14px; border-radius: 6px; margin: 8px 0; font-size: 13.5px; line-height: 1.4; }}
    .critical {{ background: #FFF5F5; border-left: 4px solid #E03131; color: #C92A2A; }}
    .warning {{ background: #FFF9DB; border-left: 4px solid #F5B800; color: #B58100; }}
    .info {{ background: #F1F3F5; border-left: 4px solid #868E96; color: #495057; }}
    .form-box {{ background: #F8F9FA; padding: 10px; border-radius: 6px; margin-bottom: 6px; font-size: 13.5px; }}
    .error-box {{ background: #FFF5F5; color: #C92A2A; padding: 10px; border-radius: 6px; margin: 10px 0; }}
</style>
</head>
<body>
<div class="container">
    <h1>Análise Técnica: {cliente}</h1>
    <div class="subtitle"><a href="{url}" target="_blank">{url}</a> | Gerado em {now_str}</div>
    {render_pagespeed_block("Mobile", pagespeed_mobile)}
    {render_pagespeed_block("Desktop", pagespeed_desktop)}
    {tags_html}
    {forms_html}
    {usability_html}
</div>
</body>
</html>"""
