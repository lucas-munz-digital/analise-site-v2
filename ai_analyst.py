"""
Módulo de análise por IA usando o Google Gemini.
Gera pareceres profundos de UX/CRO e Mídia Paga com persona Sênior.
"""
import os
import json
from google import genai
from google.genai import types

DEFAULT_GEMINI_API_KEY = "AIzaSyBuvA0OE36shPYEkoGY886S-Lii6Tb8INk"


def generate_ai_insights(cliente: str, url: str, pagespeed_mobile: dict, 
                         pagespeed_desktop: dict, tags: dict, 
                         forms_data: dict, usability_issues: list, 
                         broken_links: list = None, page_context: dict = None,
                         api_key: str = None) -> dict:
    """
    Combina as métricas técnicas e o contexto comercial da página para gerar
    análises estratégicas profundas através do Gemini.
    """
    gemini_key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY

    try:
        client = genai.Client(api_key=gemini_key)

        audit_payload = {
            "cliente": cliente,
            "url": url,
            "contexto_da_pagina": page_context or {},
            "desempenho_mobile": {
                "score_performance": pagespeed_mobile.get("scores", {}).get("performance"),
                "vitals": pagespeed_mobile.get("vitals", {}),
                "oportunidades": [o.get("title") for o in pagespeed_mobile.get("opportunities", [])]
            },
            "desempenho_desktop": {
                "score_performance": pagespeed_desktop.get("scores", {}).get("performance"),
                "vitals": pagespeed_desktop.get("vitals", {}),
                "oportunidades": [o.get("title") for o in pagespeed_desktop.get("opportunities", [])]
            },
            "tags_rastreamento": {
                "gtm": tags.get("gtm_containers"),
                "ga4": tags.get("ga4_properties"),
                "google_ads": tags.get("google_ads_ids"),
                "meta_pixel": tags.get("meta_pixel_ids"),
                "alertas": tags.get("issues", [])
            },
            "formularios_e_conversao": forms_data.get("forms", []),
            "links_quebrados": [bl.get("url") for bl in (broken_links or [])],
            "usabilidade_heuristica": [u[1] for u in usability_issues]
        }

        prompt = f"""
Sua persona: Você é o Diretor de Mídia Paga e CRO/UX Sênior da Agência Mestre. Sua experiência abrange a gestão de milhões de reais em tráfego pago (Google Ads, Meta Ads) e a otimização de Landing Pages de alta conversão.

Sua missão: Analisar os dados técnicos e mercadológicos da auditoria abaixo e emitir um parecer estratégico profundo, humano e altamente profissional. Evite generalidades; fundamente suas observações considerando o modelo de negócio inferido pelos títulos, meta description e CTAs da página.

DADOS COMPLETOS DA AUDITORIA:
{json.dumps(audit_payload, ensure_ascii=False, indent=2)}

DIRETRIZES DE RESPOSTA (Gere ESTRITAMENTE um objeto JSON com estas chaves):

1. "resumo_executivo": 
   - Um parecer de 4 a 5 linhas para o C-Level da empresa.
   - Avalie se a página está pronta para escalar tráfego pago. Seja direto sobre riscos financeiros (CPC alto, perda de conversão) decorrentes das falhas encontradas.

2. "consideracoes_desempenho":
   - Análise detalhada do impacto do FCP, LCP e score mobile na experiência do usuário e no Índice de Qualidade das campanhas.
   - Explique exatamente como a lentidão mobile afeta o custo por lead (CPL) e a retenção do tráfego vindo dos anúncios.

3. "consideracoes_tags":
   - Avalie a robustez da infraestrutura de dados (GA4, GTM, Meta Pixel, Google Ads).
   - Indique riscos específicos de perda de atribuição, invisibilidade das conversões nas plataformas de tráfego pago ou duplicidade de eventos.

4. "consideracoes_conversao":
   - Analise os formulários, iFrames e botões de CTA sob a ótica de UX/CRO.
   - Comente sobre a presença ou ausência de Thank You Page e oriente sobre as melhores práticas para que a equipe de mídia possa otimizar as campanhas por meta de conversão real.
"""

        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )

        return json.loads(response.text)

    except Exception as e:
        return {
            "resumo_executivo": f"Análise técnica concluída. O parecer estratégico de IA temporariamente indisponível ({str(e)}).",
            "consideracoes_desempenho": "Analise as métricas de LCP/FCP no quadro abaixo para identificar gargalos de velocidade.",
            "consideracoes_tags": "Verifique a lista de tags e alertas do GTM para garantir o correto rastreamento de conversão.",
            "consideracoes_conversao": "Verifique a tabela de formulários e a existência de Thank You Page para alinhar o disparo de eventos no CRM."
        }
