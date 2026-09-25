"""
Módulo de análise por IA usando o Google Gemini.
Gera pareceres profundos de UX/CRO e Mídia Paga com persona Sênior.
Classifica cada pilar com status 'vermelho' (impede/prejudica anúncios) ou 'amarelo' (melhoria sem bloqueio).
"""
import os
import json
import time
from google import genai
from google.genai import types

DEFAULT_GEMINI_API_KEY = "AIzaSyBuvA0OE36shPYEkoGY886S-Lii6Tb8INk"

MODELS_TO_TRY = [
    'gemini-3.8-flash',
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite'
]


def generate_ai_insights(cliente: str, url: str, pagespeed_mobile: dict, 
                         pagespeed_desktop: dict, tags: dict, 
                         forms_data: dict, usability_issues: list, 
                         broken_links: list = None, page_context: dict = None,
                         api_key: str = None) -> dict:

    gemini_key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY

    try:
        client = genai.Client(api_key=gemini_key)
    except Exception as e:
        return _fallback_response(f"Erro ao inicializar cliente Gemini: {str(e)}")

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
        "tags_rastreamento": tags,
        "formularios_e_conversao": forms_data.get("forms", []),
        "links_quebrados": [bl.get("url") for bl in (broken_links or [])],
        "usabilidade_heuristica": [u[1] for u in usability_issues]
    }

    prompt = f"""
Sua persona: Você é o Diretor de Mídia Paga e CRO/UX Sênior da Agência Mestre.

Sua missão: Analisar os dados técnicos e mercadológicos abaixo e emitir pareceres estratégicos para cada pilar.

DADOS DA AUDITORIA:
{json.dumps(audit_payload, ensure_ascii=False, indent=2)}

REGRAS DE CATEGORIZAÇÃO DE STATUS (Defina obrigatoriamente "vermelho" ou "amarelo" para cada pilar):
- "vermelho": O item impacta diretamente a veiculação dos anúncios, reduz o Índice de Qualidade/algoritmo, gera perda de rastreamento/conversão ou cria lentidão crítica que perde tráfego pago.
- "amarelo": Há oportunidade clara de melhoria, mas a falha NÃO impede a veiculação nem destrói a coleta principal de dados de imediato.

DIRETRIZES DE RESPOSTA (Gere ESTRITAMENTE um objeto JSON válido):

{{
  "resumo_executivo": "Parecer geral de 4-5 linhas para o C-Level avaliando se o site pode receber escala de tráfego pago.",
  "consideracoes_desempenho": "Análise técnica do impacto do FCP, LCP e score mobile na Mídia Paga.",
  "status_desempenho": "vermelho ou amarelo",
  "consideracoes_tags": "Análise da infraestrutura de tracking (GTM, GA4, Meta, Ads) e perda de atribuição.",
  "status_tags": "vermelho ou amarelo",
  "consideracoes_conversao": "Análise de formulários, RD Station, CTAs e Thank You Pages sob a ótica de CRO.",
  "status_conversao": "vermelho ou amarelo"
}}
"""

    last_exception = None

    for model_name in MODELS_TO_TRY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3
                    )
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                last_exception = e
                time.sleep(2 * (attempt + 1))

    return _fallback_response(str(last_exception))


def _fallback_response(err_msg: str) -> dict:
    return {
        "resumo_executivo": f"Análise técnica concluída. O parecer estratégico por IA está temporariamente indisponível ({err_msg}).",
        "consideracoes_desempenho": "Analise as métricas de LCP/FCP no quadro abaixo para identificar gargalos de velocidade.",
        "status_desempenho": "vermelho",
        "consideracoes_tags": "Verifique a lista de tags e alertas do GTM para garantir o correto rastreamento de conversão.",
        "status_tags": "amarelo",
        "consideracoes_conversao": "Verifique a tabela de formulários e a existência de Thank You Page para alinhar o disparo de eventos no CRM.",
        "status_conversao": "vermelho"
    }
