"""
Módulo de análise técnica de sites.
Não usa nenhuma chamada de IA - apenas requests HTTP + parsing de HTML/regex.
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
GTM_JS_URL = "https://www.googletagmanager.com/gtm.js"
TIMEOUT = 90  # Aumentado para 90s para evitar Read Timeout na API do PageSpeed
UA_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# Chave de API padrão da Agência Mestre
DEFAULT_PAGESPEED_API_KEY = "AIzaSyBuvA0OE36shPYEkoGY886S-Lii6Tb8INk"


# ---------------------------------------------------------------------------
# 1. PAGESPEED
# ---------------------------------------------------------------------------
def get_pagespeed(url: str, strategy: str = "mobile", api_key: str = None) -> dict:
    """Chama a API do Google PageSpeed Insights.

    Usa por padrão a chave de API embutida caso não seja informada via parâmetro
    ou variável de ambiente.
    """
    api_key = api_key or os.environ.get("PAGESPEED_API_KEY") or DEFAULT_PAGESPEED_API_KEY
    params = {"url": url, "strategy": strategy, "category": ["performance", "accessibility", "best-practices", "seo"]}
    if api_key:
        params["key"] = api_key
    try:
        resp = requests.get(PAGESPEED_API, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return {"error": "Cota da API do PageSpeed excedida (erro 429). "
                              "Configure uma chave de API gratuita para aumentar o limite — veja o README.md."}
        try:
            data = e.response.json()
            return {"error": data.get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

    if "error" in data:
        return {"error": data["error"].get("message", "Erro desconhecido")}

    lh = data["lighthouseResult"]
    cats = lh["categories"]
    audits = lh["audits"]

    def score(cat):
        try:
            return round(cats[cat]["score"] * 100)
        except (KeyError, TypeError):
            return None

    def metric(key, suffix=""):
        try:
            val = audits[key]["displayValue"]
            return val
        except KeyError:
            return "-"

    # oportunidades (economia de tempo) ordenadas pelas piores primeiro
    opportunities = []
    for key, audit in audits.items():
        if audit.get("score") is not None and audit["score"] < 1 and "details" in audit and audit["details"].get("type") == "opportunity":
            opportunities.append({
                "title": audit["title"],
                "description": re.sub(r"\[.*?\]\(.*?\)", "", audit.get("description", "")),
                "savings_ms": audit["details"].get("overallSavingsMs", 0),
            })
    opportunities.sort(key=lambda x: -x["savings_ms"])

    return {
        "strategy": strategy,
        "scores": {
            "performance": score("performance"),
            "accessibility": score("accessibility"),
            "best_practices": score("best-practices"),
            "seo": score("seo"),
        },
        "vitals": {
            "fcp": metric("first-contentful-paint"),
            "lcp": metric("largest-contentful-paint"),
            "tbt": metric("total-blocking-time"),
            "cls": metric("cumulative-layout-shift"),
            "speed_index": metric("speed-index"),
        },
        "opportunities": opportunities[:6],
    }


# ---------------------------------------------------------------------------
# 2. FETCH HTML
# ---------------------------------------------------------------------------
def fetch_html(url: str) -> str:
    headers = {**UA_HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


def fetch_gtm_containers_content(html: str) -> str:
    """Baixa o conteúdo publicado (gtm.js) de cada container GTM encontrado no HTML."""
    gtm_ids = sorted(set(re.findall(r"GTM-[A-Z0-9]+", html)))
    chunks = []
    for gtm_id in gtm_ids:
        try:
            resp = requests.get(GTM_JS_URL, params={"id": gtm_id}, headers=UA_HEADERS, timeout=TIMEOUT)
            if resp.ok:
                chunks.append(resp.text)
        except Exception:
            continue
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# 3. TAGS E SCRIPTS
# ---------------------------------------------------------------------------
def detect_tags(html: str, gtm_js_content: str = "") -> dict:
    """Detecta tags de rastreamento."""
    combined = html + "\n" + gtm_js_content

    ga4_html_only = set(re.findall(r"\bG-[A-Z0-9]{6,}\b", html))
    ads_html_only = set(re.findall(r"\bAW-[0-9]{5,}\b", html))

    # Regex aprimorado para capturar IDs do Meta Pixel (fbq init ou fbevents.js, incluindo dentro do GTM minificado)
    pixel_matches = re.findall(r"fbq\(\\?['\"]init\\?['\"],\s*\\?['\"](\d{13,16})\\?['\"]", combined)
    pixel_matches += re.findall(r"id=(\d{13,16})", combined)  # Captura URLs de fbevents / noscript pixel

    meta_pixels = sorted(set(pixel_matches))

    findings = {
        "gtm_containers": sorted(set(re.findall(r"GTM-[A-Z0-9]+", html))),
        "ga4_properties": sorted(set(re.findall(r"\bG-[A-Z0-9]{6,}\b", combined))),
        "google_ads_ids": sorted(set(re.findall(r"\bAW-[0-9]{5,}\b", combined))),
        "meta_pixel_ids": meta_pixels,
        "gtag_ids": sorted(set(re.findall(r"\bGT-[A-Z0-9]+\b", combined))),
    }

    findings["ga4_only_via_gtm"] = sorted(set(findings["ga4_properties"]) - ga4_html_only)
    findings["google_ads_only_via_gtm"] = sorted(set(findings["google_ads_ids"]) - ads_html_only)

    issues = []
    total_ads_conversions = len(findings["google_ads_ids"])
    if len(findings["gtm_containers"]) > 1:
        issues.append(f"Mais de um contêiner GTM encontrado ({', '.join(findings['gtm_containers'])}) — pode gerar disparo duplicado de eventos.")
    if len(findings["ga4_properties"]) > 1:
        issues.append(f"Mais de uma propriedade GA4 encontrada ({', '.join(findings['ga4_properties'])}) — verificar qual é a ativa.")
    if total_ads_conversions >= 3:
        issues.append(f"{total_ads_conversions} IDs de Google Ads disparando simultaneamente — recomenda-se mapear origem e remover inativos.")
    if not findings["gtm_containers"] and not findings["ga4_properties"] and not findings["google_ads_ids"] and not findings["meta_pixel_ids"]:
        detail = " (nenhum container GTM encontrado para checar tags internas)" if not gtm_js_content else ""
        issues.append(f"Nenhuma tag de rastreamento (GTM/GA4/Google Ads/Meta) foi detectada{detail}.")
    findings["issues"] = issues
    return findings


# ---------------------------------------------------------------------------
# 4. FORMULÁRIOS
# ---------------------------------------------------------------------------
def detect_forms(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        action = form.get("action", "") or "(mesma página)"
        action_abs = urljoin(base_url, action) if action != "(mesma página)" else action
        fields = []
        for field in form.find_all(["input", "textarea", "select"]):
            ftype = field.get("type", field.name)
            fname = field.get("name") or field.get("id") or "(sem nome)"
            if ftype not in ("hidden", "submit", "button"):
                fields.append(f"{fname} ({ftype})")

        destino = "desconhecido"
        low = action_abs.lower()
        if "wa.me" in low or "whatsapp" in low or "api.whatsapp" in low:
            destino = "WhatsApp (fora do CRM)"
        elif "mailto:" in low:
            destino = "e-mail direto"
        elif action_abs == "(mesma página)":
            destino = "mesma página (verificar JS de submit / webhook)"
        else:
            destino = "endpoint externo"

        forms.append({
            "fields": fields,
            "action": action_abs,
            "destino": destino,
            "num_campos": len(fields),
        })

    ctas = [a.get("href") for a in soup.find_all("a", href=True) if any(w in (a.get_text() or "").lower() for w in
            ["orçamento", "cotação", "contrat", "solicit", "comprar", "fale conosco", "saiba mais"])]
    duplicated_ctas = {href for href in ctas if ctas.count(href) > 1 and href not in ("#", "")}

    return {"forms": forms, "duplicated_cta_targets": sorted(duplicated_ctas)}


# ---------------------------------------------------------------------------
# 5. USABILIDADE / DESIGN (heurísticas automáticas)
# ---------------------------------------------------------------------------
def detect_usability_issues(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    issues = []

    if not soup.find("meta", attrs={"name": "viewport"}):
        issues.append(("critico", "Página sem meta tag viewport — pode quebrar a responsividade em mobile."))

    title = soup.find("title")
    if not title or not title.text.strip():
        issues.append(("critico", "Página sem <title> definido — impacta SEO e CTR nos resultados de busca."))

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc or not meta_desc.get("content", "").strip():
        issues.append(("medio", "Meta description ausente ou vazia."))

    imgs = soup.find_all("img")
    sem_alt = [i for i in imgs if not i.get("alt", "").strip()]
    if imgs and len(sem_alt) / len(imgs) > 0.3:
        pct = round(len(sem_alt) / len(imgs) * 100)
        issues.append(("medio", f"{pct}% das imagens ({len(sem_alt)}/{len(imgs)}) estão sem atributo alt — afeta acessibilidade e SEO."))

    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        issues.append(("critico", "Site não está servindo em HTTPS."))

    if not soup.find("link", attrs={"rel": re.compile("icon", re.I)}):
        issues.append(("baixo", "Favicon não encontrado."))

    if re.search(r'data-count(er)?=["\']?\d+', html, re.I) or re.search(r'class=["\'][^"\']*counter[^"\']*["\']', html, re.I):
        issues.append(("baixo", "Foram encontrados elementos de contador animado (counters) — validar manualmente se carregam com valor final visível caso o JS falhe."))

    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        issues.append(("medio", "Nenhum H1 encontrado na página."))
    elif len(h1s) > 1:
        issues.append(("baixo", f"{len(h1s)} tags H1 encontradas — o ideal é apenas uma por página."))

    return issues
