"""
Gera o preview HTML do relatório no formato de Apresentação Dark Deck (Agência Mestre).
"""
from datetime import datetime


def build_html_report(cliente: str, url: str, is_ecommerce: bool,
                       pagespeed_mobile: dict, pagespeed_desktop: dict,
                       tags: dict, forms_data: dict, usability_issues: list,
                       broken_links: list = None, ai_insights: dict = None) -> str:

    ai = ai_insights or {}

    score_m = pagespeed_mobile.get("scores", {}).get("performance", "-")
    score_d = pagespeed_desktop.get("scores", {}).get("performance", "-")

    now_str = datetime.now().strftime("%d/%m/%Y")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0A0A0A; color: #FFFFFF; padding: 20px; }}
    .slide {{ background: #121212; border: 1px solid #262626; border-radius: 12px; padding: 32px; max-width: 900px; margin: 0 auto 24px auto; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
    .tag-section {{ font-size: 11px; font-weight: bold; color: #A0A0A0; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }}
    h1 {{ font-size: 26px; margin: 0 0 16px 0; color: #FFFFFF; font-weight: 700; }}
    h2 {{ font-size: 20px; margin: 0 0 16px 0; color: #FFFFFF; }}
    p {{ font-size: 14px; line-height: 1.6; color: #CCCCCC; margin-top: 0; }}
    .card {{ background: #1E1E1E; border-left: 4px solid #3B82F6; padding: 16px 20px; border-radius: 6px; margin-bottom: 16px; }}
    .card-title {{ font-weight: bold; font-size: 14px; color: #FFFFFF; margin-bottom: 6px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .score-card {{ background: #1E1E1E; padding: 16px; border-radius: 8px; text-align: center; border: 1px solid #333; }}
    .score-val {{ font-size: 32px; font-weight: bold; color: #3B82F6; }}
    .score-lbl {{ font-size: 12px; color: #A0A0A0; }}
    .table-dark {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13.5px; }}
    .table-dark th {{ text-align: left; background: #262626; padding: 10px; color: #FFF; }}
    .table-dark td {{ padding: 10px; border-bottom: 1px solid #262626; color: #DDD; }}
    .footer-slide {{ display: flex; justify-content: space-between; font-size: 11px; color: #666; margin-top: 24px; border-top: 1px solid #222; padding-top: 12px; }}
</style>
</head>
<body>

<div class="slide">
    <div class="tag-section">AGÊNCIA MESTRE | RELATÓRIO EXECUTIVO</div>
    <h1>Análise do Site para Mídia</h1>
    <p><b>Projeto:</b> {cliente}<br/><b>URL:</b> <a href="{url}" target="_blank" style="color: #3B82F6;">{url}</a></p>
    <div class="footer-slide"><span>Gerado em {now_str}</span><span>Slide 1</span></div>
</div>

<div class="slide">
    <div class="tag-section">01 | PARECER EXECUTIVO</div>
    <h2>Diagnóstico Geral de Mídia & CRO</h2>
    <div class="card">
        <div class="card-title">🤖 Visão do Especialista Sênior (IA Gemini)</div>
        <p>{ai.get("resumo_executivo", "Análise não disponível.")}</p>
    </div>
    <div class="grid-2">
        <div class="card" style="border-left-color: #F59E0B; background: #262626;">
            <div class="card-title">🎯 Objetivo</div>
            <p style="font-size: 12.5px;">Detectar oportunidades no site para maximizar o ROI e o Índice de Qualidade das campanhas.</p>
        </div>
        <div class="card" style="border-left-color: #EF4444; background: #262626;">
            <div class="card-title">⚠️ Legenda de Urgência</div>
            <p style="font-size: 12.5px;">🔴 <b>Atenção Imediata:</b> Prejudica resultados.<br/>🟡 <b>Médio Prazo:</b> Otimização contínua.</p>
        </div>
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 2</span></div>
</div>

<div class="slide">
    <div class="tag-section">02 | PERFORMANCE</div>
    <h2>Desempenho & Core Web Vitals</h2>
    <div class="grid-2" style="margin-bottom: 16px;">
        <div class="score-card"><div class="score-val">{score_m}</div><div class="score-lbl">Mobile Score</div></div>
        <div class="score-card"><div class="score-val">{score_d}</div><div class="score-lbl">Desktop Score</div></div>
    </div>
    <div class="card">
        <div class="card-title">💡 Impacto no Custo por Clique (CPC) e Rejeição</div>
        <p>{ai.get("consideracoes_desempenho", "Consulte os números brutos.")}</p>
    </div>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 3</span></div>
</div>

<div class="slide">
    <div class="tag-section">03 | TRACKING & MENSURAÇÃO</div>
    <h2>Auditoria do Ecossistema de Rastreamento</h2>
    <div class="card">
        <div class="card-title">💡 Diagnóstico de Tracking</div>
        <p>{ai.get("consideracoes_tags", "Consulte a tabela abaixo.")}</p>
    </div>
    <table class="table-dark">
        <thead><tr><th>Ferramenta</th><th>IDs Detectados</th></tr></thead>
        <tbody>
            <tr><td><b>GTM</b></td><td>{", ".join(tags.get("gtm_containers", [])) or "Não encontrado 🔴"}</td></tr>
            <tr><td><b>GA4</b></td><td>{", ".join(tags.get("ga4_properties", [])) or "Não encontrado 🔴"}</td></tr>
            <tr><td><b>Google Ads</b></td><td>{", ".join(tags.get("google_ads_ids", [])) or "Não encontrado 🔴"}</td></tr>
            <tr><td><b>Meta Pixel</b></td><td>{", ".join(tags.get("meta_pixel_ids", [])) or "Não encontrado 🔴"}</td></tr>
        </tbody>
    </table>
    <div class="footer-slide"><span>Agência Mestre</span><span>Slide 4</span></div>
</div>

</body>
</html>"""
