"""
Módulo de análise por IA usando o Google Gemini.
Gera pareceres técnicos e resumos executivos em linguagem natural.
"""
import os
import json
from google import genai
from google.genai import types

# Usamos a mesma chave do PageSpeed como padrão caso a GEMINI_API_KEY não seja definida separadamente
DEFAULT_GEMINI_API_KEY = "AIzaSyBuvA0OE36shPYEkoGY886S-Lii6Tb8INk"


def generate_ai_insights(cliente: str, url: str, pagespeed_mobile: dict, 
                         pagespeed_desktop: dict, tags: dict, 
                         forms_data: dict, usability_issues: list, 
                         broken_links: list = None, api_key: str = None) -> dict:
    """
    Consolida os dados técnicos coletados e faz chamada à API do Gemini
    para gerar considerações humanas e pareceres por tópico.
    """
    gemini_key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY

    try:
        client = genai.Client(api_key=gemini_key)

        # Consolidação dos dados brutos para alimentar o modelo
        audit_data = {
            "cliente": cliente,
            "url": url,
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
                "problemas_tags": tags.get("issues", [])
            },
            "formularios": [
                {
                    "id": f.get("id"),
                    "tipo": f.get("tipo"),
                    "destino": f.get("destino"),
                    "tem_pagina_agradecimento": f.get("has_thank_you_page")
                } for f in forms_data.get("forms", [])
            ],
            "links_quebrados": [bl.get("url") for bl in (broken_links or [])],
            "problemas_usabilidade": [u[1] for u in usability_issues]
        }

        prompt = f"""
Você é um Consultor Especialista de Mídia Paga, Tracking e SEO da Agência Mestre.
Sua missão é analisar os dados técnicos da auditoria de onboarding do site de um novo cliente e traduzi-los em pareceres estratégicos claros, objetivos e humanos para o analista e para a diretoria do cliente.

DADOS DA AUDITORIA:
{json.dumps(audit_data, ensure_ascii=False, indent=2)}

INSTRUÇÕES DE RESPOSTA:
Retorne estritamente um objeto JSON com as seguintes chaves (sem formatação extra além do JSON):

1. "resumo_executivo": Parecer geral (3 a 4 linhas) direcionado à diretoria do cliente. Avalie se o site está pronto para receber verba de anúncios ou se há impedimentos críticos que vão queimar orçamento.
2. "consideracoes_desempenho": Análise prática do impacto da velocidade mobile e desktop na taxa de conversão e no custo por clique (CPC) das campanhas.
3. "consideracoes_tags": Diagnóstico sobre a maturidade do rastreamento (Pixel, GA4, Ads, GTM). Destaque os riscos de perda de inteligência nos anúncios ou duplicidade.
4. "consideracoes_conversao": Análise sobre a captação de leads (formulários, WhatsApp, páginas de agradecimento). Destaque a confiabilidade do tracking de conversão.
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        return json.loads(response.text)

    except Exception as e:
        # Fallback gracioso caso a API falhe para não travar o relatório
        return {
            "resumo_executivo": "O parecer automatizado via IA não pôde ser gerado nesta análise. Verifique as métricas técnicas abaixo.",
            "consideracoes_desempenho": "Consulte as pontuações do PageSpeed e métricas FCP/LCP no quadro abaixo.",
            "consideracoes_tags": "Consulte as tags detectadas e os alertas do GTM na tabela abaixo.",
            "consideracoes_conversao": "Consulte o mapeamento de formulários e páginas de agradecimento abaixo."
        }
