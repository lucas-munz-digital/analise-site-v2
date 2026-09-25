"""
Gera o relatório visual em HTML/CSS nativo no formato de Presentation Deck 16:9.
Utiliza CSS Print p/ exportação perfeita em PDF pelo navegador.
"""
from datetime import datetime
import os

POSSIBLE_LOGOS = [
    "agncia_mestre_logo.jpeg", "agncia_mestre_logo.jpg", 
    "logo_mestre.jpg", "logo_mestre.jpeg", "logo_mestre.png"
]


def build_html_report(cliente: str, url: str, is_ecommerce: bool,
                       pagespeed_mobile: dict, pagespeed_desktop: dict,
                       tags: dict, forms_data: dict, usability_issues: list,
                       broken_links: list = None, ai_insights: dict = None) -> str:

    ai = ai_insights or {}
    score_m = pagespeed_mobile.get("scores", {}).get("performance", "-")
    score_d = pagespeed_desktop.get("scores", {}).get("performance", "-")
    now_str = datetime.now().strftime("%d/%m/%Y")

    logo_file = next((f for f in POSSIBLE_LOGOS if os.path.exists(f)), "agncia_mestre_logo.jpeg")

    # Helper para renderizar badges de status em HTML
    def get_status_badge(status):
        if status == "vermelho":
            return '<span class="badge badge-red">🔴 ATENÇÃO IMEDIATA - IMPACTA ANÚNCIOS</span>'
        elif status == "amarelo":
            return '<span class="badge badge-yellow">🟡 MÉDIO PRAZO - OPORTUNIDADE</span>'
        return ''

    forms = forms_data.get("forms", [])
    forms_html = ""
    if not forms:
        forms_html = '<div class="card card-red"><div class="card-title">Alertas de Formulários ' + get_status_badge("vermelho") + '</div><p>Nenhum formulário HTML estático ou script de automação foi detectado.</p></div>'
    else:
        for f in forms[:3]:
            st_code = "amarelo" if f.get("has_thank_you_page") else "vermelho"
            ty_status = "✅ Página de Agradecimento Identificada" if f.get("has_thank_you_page") else "🔴 Sem Página de Agradecimento (Página de Sucesso/Popup)"
            forms_html += f'''
            <div class="card card-{st_code}" style="margin-bottom: 12px;">
                <div class="card-title">Formulário #{f['id']} {get_status_badge(st_code)}</div>
                <p><b>Tipo:</b> {f.get('tipo')} | <b>Destino:</b> {f.get('destino')}<br/><b>Status de Tracking:</b> {ty_status}</p>
            </div>
            '''

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Análise do Site para Mídia — {cliente}</title>
<style>
    @page {{
        size: 16in 9in; /* Formato Widescreen 16:9 Nativo */
        margin: 0;
    }}
    * {{ box-sizing: border-box; }}
    body {{ 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
        background: #0A0A0A; 
        color: #FFFFFF; 
        margin: 0; 
        padding: 20px; 
    }}
    .slide {{ 
        background: #121212; 
        border: 1px solid #262626; 
        border-radius: 12px; 
        padding: 40px; 
        width: 100%;
        max-width: 1200px; 
        height: 675px; /* Proporção 16:9 perfeita */
        margin: 0 auto 30px auto; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        page-break-after: always;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }}
    .header-logo {{
        position: absolute;
        top: 35px;
        right: 40px;
        max-width: 100px;
        max-height: 80px;
        object-fit: contain;
    }}
    .tag-section {{ 
        font-size: 12px; 
        font-weight: 700; 
        color: #A0A0A0; 
        letter-spacing: 1.5px; 
        text-transform: uppercase; 
        margin-bottom: 6px; 
    }}
    h1 {{ font-size: 32px; margin: 0 0 10px 0; color: #FFFFFF; font-weight: 700; }}
    h2 {{ font-size: 22px; margin: 0 0 20px 0; color: #FFFFFF; font-weight: 600; }}
    p {{ font-size: 14px; line-height: 1.6; color: #CCCCCC; margin: 0; }}
    
    /* CARDS E BADGES */
    .card {{ 
        background: #1E1E1E; 
        border-left: 5px solid #3B82F6; 
        padding: 18px 22px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
    }}
    .card-red {{ border-left-color: #EF4444; }}
    .card-yellow {{ border-left-color: #F59E0B; }}
    .card-title {{ 
        font-weight: 700; 
        font-size: 15px; 
        color: #FFFFFF; 
        margin-bottom: 8px; 
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .badge {{
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }}
    .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; }}
    .badge-yellow {{ background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }}

    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .score-card {{ background: #1E1E1E; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #333; }}
    .score-val {{ font-size: 38px; font-weight: bold; color: #3B82F6; }}
    .score-lbl {{ font-size: 12px; color: #A0A0A0; text-transform: uppercase; margin-top: 4px; }}
    
    .table-dark {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    .table-dark th {{ text-align: left; background: #262626; padding: 12px; color: #FFF; border-bottom: 2px solid #333; }}
    .table-dark td {{ padding: 12px; border-bottom: 1px solid #262626; color: #DDD; }}
    
    .footer-slide {{ 
        display: flex; 
        justify-content: space-between; 
        font-size: 11px; 
        color: #666666; 
        border-top: 1px solid #222222; 
        padding-top: 14px; 
    }}

    @media print {{
        body {{ background: #121212; padding: 0; }}
        .slide {{ border: none; box-shadow: none; width: 100vw; height: 100vh; max-width: none; border-radius: 0; }}
        .no-print {{ display: none; }}
    }}
</style>
</head>
<body>

<!-- SLIDE 1: CAPA -->
<div class="slide">
    <img src="{logo_file}" class="header-logo" alt="Agência Mestre" />
    <div>
        <div class="tag-section">AGÊNCIA MESTRE | AUDITORIA TÉCNICA</div>
        <h1>Análise do Site para Mídia</h1>
        <p style="font-size: 16px; margin-top: 10px;"><b>Projeto:</b> {cliente}<br/><b>URL:</b> {url}</p>
    </div>
    <div class="footer-slide"><span>Gerado em {now_str}</span><span>Slide 1</span></div>
</div>

<!-- SLIDE 2: PARECER EXECUTIVO -->
<div class="slide">
    <img src="{logo_file}" class="header-logo" alt="Agência Mestre" />
    <div>
        <div class="tag-section">01 | PARECER EXECUTIVO</div>
        <h2>Diagnóstico Geral de Mídia & Prontidão do Site</h2>
        <div class="card card-blue">
            <div class="card-title">Visão Geral do Consultor Sênior</div>
            <p>{ai.get("resumo_executivo", "Análise executiva não disponível.")}</p>
        </div>
        <div class="grid-2">
            <div class="card" style="border-left-color: #3B82F6; background: #1A1A1A;">
                <div class="card-title">🎯 Objetivo</div>
                <p style="font-size: 13px;">Detectar oportunidades no site para maximizar o ROI e o Índice de Qualidade das campanhas.</p>
            </div>
            <div class="card" style="border-left-color: #EF4444; background: #1A1A1A;">
                <div class="card-title">⚠️ Legenda de Urgência</div>
                <p style="font-size: 13px;">🔴 <b>Atenção Imediata:</b> Impacta anúncios/resultados.<br/>🟡 <b>Médio Prazo:</b> Oportunidade de otimização.</p>
            </div>
        </div>
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 2</span></div>
</div>

<!-- SLIDE 3: PERFORMANCE -->
<div class="slide">
    <img src="{logo_file}" class="header-logo" alt="Agência Mestre" />
    <div>
        <div class="tag-section">02 | PERFORMANCE & CORE WEB VITALS</div>
        <h2>Desempenho do Site e Impacto no CPC</h2>
        <div class="grid-2" style="margin-bottom: 16px;">
            <div class="score-card"><div class="score-val">{score_m}</div><div class="score-lbl">Mobile Score</div></div>
            <div class="score-card"><div class="score-val">{score_d}</div><div class="score-lbl">Desktop Score</div></div>
        </div>
        <div class="card card-{ai.get('status_desempenho', 'vermelho')}">
            <div class="card-title">Impacto na Mídia Paga & Rejeição {get_status_badge(ai.get('status_desempenho', 'vermelho'))}</div>
            <p>{ai.get("consideracoes_desempenho", "Consulte os números acima.")}</p>
        </div>
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 3</span></div>
</div>

<!-- SLIDE 4: TRACKING -->
<div class="slide">
    <img src="{logo_file}" class="header-logo" alt="Agência Mestre" />
    <div>
        <div class="tag-section">03 | MENSURAÇÃO & TRACKING</div>
        <h2>Auditoria do Ecossistema de Rastreamento</h2>
        <div class="card card-{ai.get('status_tags', 'amarelo')}">
            <div class="card-title">Diagnóstico de Tracking {get_status_badge(ai.get('status_tags', 'amarelo'))}</div>
            <p>{ai.get("consideracoes_tags", "Consulte a tabela abaixo.")}</p>
        </div>
        <table class="table-dark">
            <thead><tr><th>Ferramenta</th><th>IDs Detectados</th></tr></thead>
            <tbody>
                <tr><td><b>Google Tag Manager (GTM)</b></td><td>{", ".join(tags.get("gtm_containers", [])) or "Não encontrado 🔴"}</td></tr>
                <tr><td><b>Google Analytics 4 (GA4)</b></td><td>{", ".join(tags.get("ga4_properties", [])) or "Não encontrado 🔴"}</td></tr>
                <tr><td><b>Google Ads</b></td><td>{", ".join(tags.get("google_ads_ids", [])) or "Não encontrado 🔴"}</td></tr>
                <tr><td><b>Meta Pixel</b></td><td>{", ".join(tags.get("meta_pixel_ids", [])) or "Não encontrado 🔴"}</td></tr>
            </tbody>
        </table>
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 4</span></div>
</div>

<!-- SLIDE 5: CRO & FORMS -->
<div class="slide">
    <img src="{logo_file}" class="header-logo" alt="Agência Mestre" />
    <div>
        <div class="tag-section">04 | CONVERSÃO & CRO</div>
        <h2>Mapeamento de Captura de Leads e Thank You Pages</h2>
        <div class="card card-{ai.get('status_conversao', 'vermelho')}">
            <div class="card-title">Parecer de Conversão & UX {get_status_badge(ai.get('status_conversao', 'vermelho'))}</div>
            <p>{ai.get("consideracoes_conversao", "Consulte os formulários abaixo.")}</p>
        </div>
        {forms_html}
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 5</span></div>
</div>

</body>
</html>"""
