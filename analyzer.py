"""
Módulo de análise técnica de sites.
Não usa nenhuma chamada de IA - apenas requests HTTP + parsing de HTML/regex.
"""
import os
import re
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
GTM_JS_URL = "https://www.googletagmanager.com/gtm.js"
TIMEOUT_PAGESPEED = 120
TIMEOUT_HTTP = 25
UA_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

DEFAULT_PAGESPEED_API_KEY = "AIzaSyBuvA0OE36shPYEkoGY886S-Lii6Tb8INk"

OPPORTUNITIES_MAP = {
    "Reduce unused JavaScript": "Reduzir JavaScript não utilizado",
    "Reduce unused CSS": "Reduzir CSS não utilizado",
    "Minify CSS": "Minificar CSS",
    "Minify JavaScript": "Minificar JavaScript",
    "Eliminate render-blocking resources": "Eliminar recursos que bloqueiam a renderização",
    "Efficiently encode images": "Codificar imagens de forma eficiente",
    "Enable text compression": "Ativar compressão de texto (Gzip/Brotli)",
    "Properly size images": "Dimensionar imagens adequadamente",
    "Serve images in next-gen formats": "Servir imagens em formatos de última geração (WebP/AVIF)",
    "Defer offscreen images": "Adiar o carregamento de imagens fora da tela (Lazy Loading)",
}

def get_pagespeed(url: str, strategy: str = "mobile", api_key: str = None) -> dict:
    api_key = api_key or os.environ.get("PAGESPEED_API_KEY") or DEFAULT_PAGESPEED_API_KEY
    categories = ["performance"] if strategy == "mobile" else ["performance", "seo"]

    params = {
        "url": url, 
        "strategy": strategy, 
        "category": categories,
        "locale": "pt_BR"
    }
    if api_key:
        params["key"] = api_key

    data = None
    last_error = ""

    for attempt in range(2):
        try:
            current_params = params.copy()
            if attempt == 1:
                current_params.pop("locale", None)

            resp = requests.get(PAGESPEED_API, params=current_params, timeout=TIMEOUT_PAGESPEED)
            resp.raise_for_status()
            res_json = resp.json()
            
            if "error" not in res_json and "lighthouseResult" in res_json:
                data = res_json
                break
            elif "error" in res_json:
                last_error = res_json["error"].get("message", "Erro na API do Google")
        except Exception as e:
            last_error = str(e)

        time.sleep(1)

    if not data:
        return {"error": last_error or "Não foi possível obter dados do Google PageSpeed."}

    lh = data.get("lighthouseResult", {})
    cats = lh.get("categories", {})
    audits = lh.get("audits", {})

    def score(cat):
        try:
            return round(cats[cat]["score"] * 100)
        except (KeyError, TypeError):
            return None

    def metric(key):
        try:
            return audits[key]["displayValue"]
        except KeyError:
            return "-"

    perf_score = score("performance")
    
    if perf_score is not None:
        if perf_score < 80:
            interpretation = {"level": "red", "text": "Melhorias no desempenho necessárias para campanhas."}
        elif 80 <= perf_score <= 90:
            interpretation = {"level": "orange", "text": "Pontuação positiva, com oportunidades de melhoria."}
        else:
            interpretation = {"level": "none", "text": "Boa pontuação!"}
    else:
        interpretation = {"level": "none", "text": "Pontuação indisponível."}

    opportunities = []
    for key, audit in audits.items():
        if audit.get("score") is not None and audit["score"] < 1 and "details" in audit and audit["details"].get("type") == "opportunity":
            raw_title = audit["title"]
            translated_title = OPPORTUNITIES_MAP.get(raw_title, raw_title)
            opportunities.append({
                "title": translated_title,
                "description": re.sub(r"\[.*?\]\(.*?\)", "", audit.get("description", "")),
                "savings_ms": audit["details"].get("overallSavingsMs", 0),
            })
    opportunities.sort(key=lambda x: -x["savings_ms"])

    return {
        "strategy": strategy,
        "interpretation": interpretation,
        "scores": {
            "performance": perf_score,
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

def fetch_html(url: str) -> str:
    headers = {**UA_HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_HTTP, allow_redirects=True)
    resp.raise_for_status()
    return resp.text

def extract_page_context(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    title_text = title.text.strip() if title else ""

    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_text = meta_desc.get("content", "").strip() if meta_desc else ""

    h1_list = [h.get_text().strip() for h in soup.find_all("h1") if h.get_text().strip()]
    h2_list = [h.get_text().strip() for h in soup.find_all("h2") if h.get_text().strip()][:5]

    cta_buttons = []
    for elem in soup.find_all(["a", "button"]):
        txt = elem.get_text().strip()
        if txt and len(txt) < 50 and any(w in txt.lower() for w in ["comprar", "contratar", "solicitar", "falar", "whatsapp", "orçamento", "saiba mais"]):
            cta_buttons.append(txt)

    return {
        "title": title_text,
        "meta_description": desc_text,
        "h1": h1_list,
        "h2_exemplos": h2_list,
        "ctas_encontrados": list(set(cta_buttons))[:6]
    }

def check_broken_links(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    broken_links = []
    
    links = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if href and not href.startswith(("#", "javascript:", "mailto:", "tel:", "wa.me", "whatsapp:")):
            abs_url = urljoin(base_url, href)
            if urlparse(abs_url).netloc == parsed_base.netloc:
                links.add(abs_url)

    for link in list(links)[:15]:
        try:
            resp = requests.head(link, headers=UA_HEADERS, timeout=5, allow_redirects=True)
            if resp.status_code in (404, 500, 502, 503):
                broken_links.append({"url": link, "status": resp.status_code})
        except Exception:
            continue

    return broken_links

def fetch_gtm_containers_content(html: str) -> str:
    gtm_ids = sorted(set(re.findall(r"GTM-[A-Z0-9]+", html)))
    chunks = []
    for gtm_id in gtm_ids:
        try:
            resp = requests.get(GTM_JS_URL, params={"id": gtm_id}, headers=UA_HEADERS, timeout=TIMEOUT_HTTP)
            if resp.ok:
                chunks.append(resp.text)
        except Exception:
            continue
    return "\n".join(chunks)

def detect_tags(html: str, gtm_js_content: str = "") -> dict:
    combined = html + "\n" + gtm_js_content
    ga4_html_only = set(re.findall(r"\bG-[A-Z0-9]{6,}\b", html))
    ads_html_only = set(re.findall(r"\bAW-[0-9]{5,}\b", html))

    pixel_matches = re.findall(r"fbq\(\\?['\"]init\\?['\"],\s*\\?['\"](\d{13,16})\\?['\"]", combined)
    pixel_matches += re.findall(r"id=(\d{13,16})", combined)

    findings = {
        "gtm_containers": sorted(set(re.findall(r"GTM-[A-Z0-9]+", html))),
        "ga4_properties": sorted(set(re.findall(r"\bG-[A-Z0-9]{6,}\b", combined))),
        "google_ads_ids": sorted(set(re.findall(r"\bAW-[0-9]{5,}\b", combined))),
        "meta_pixel_ids": sorted(set(pixel_matches)),
    }

    issues = []
    if len(findings["gtm_containers"]) > 1:
        issues.append(f"Mais de um contêiner GTM encontrado ({', '.join(findings['gtm_containers'])})")
    if not findings["gtm_containers"] and not findings["ga4_properties"] and not findings["google_ads_ids"] and not findings["meta_pixel_ids"]:
        issues.append("Nenhuma tag de rastreamento foi detectada.")
    findings["issues"] = issues
    return findings

def detect_forms(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    form_id_counter = 1

    for form in soup.find_all("form"):
        action = form.get("action", "") or "(mesma página)"
        action_abs = urljoin(base_url, action) if action != "(mesma página)" else action
        fields = [f.get("name") or f.get("id") or "campo" for f in form.find_all(["input", "textarea", "select"]) if f.get("type") not in ("hidden", "submit", "button")]

        destino = "desconhecido"
        low = action_abs.lower()
        has_thank_you_page = any(w in low for w in ["obrigad", "thank", "sucesso", "agradec"])

        if "wa.me" in low or "whatsapp" in low:
            destino = "WhatsApp"
        elif action_abs == "(mesma página)":
            destino = "mesma página"
        else:
            destino = "endpoint externo"

        forms.append({
            "id": form_id_counter,
            "tipo": "Formulário HTML Nativo",
            "fields": fields,
            "action": action_abs,
            "destino": destino,
            "num_campos": len(fields),
            "has_thank_you_page": has_thank_you_page
        })
        form_id_counter += 1

    rd_scripts = re.findall(r'd335luupugsy2\.cloudfront\.net.*?/([a-f0-9-]+)\.js', html)
    if rd_scripts or "rdstation" in html.lower():
        forms.append({
            "id": form_id_counter,
            "tipo": "RD Station / Automação",
            "fields": ["Campos RD Station"],
            "action": "Endpoint RD Station",
            "destino": "CRM RD Station",
            "num_campos": 1,
            "has_thank_you_page": bool(re.search(r'(redirect_to|url_retorno|obrigad)', html, re.I))
        })

    return {"forms": forms}

def detect_usability_issues(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    issues = []

    if not soup.find("meta", attrs={"name": "viewport"}):
        issues.append(("critico", "Página sem meta tag viewport."))
    if not soup.find("title"):
        issues.append(("critico", "Página sem tag <title>."))

    return issues
