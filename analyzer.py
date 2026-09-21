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

# ---------------------------------------------------------------------------
# 1. PAGESPEED
# ---------------------------------------------------------------------------
def get_pagespeed(url: str, strategy: str = "mobile", api_key: str = None) -> dict:
    """Chama a API do Google PageSpeed Insights com resiliência contra erros internos do Lighthouse."""
    api_key = api_key or os.environ.get("PAGESPEED_API_KEY") or DEFAULT_PAGESPEED_API_KEY
    
    # Para mobile, usamos apenas a categoria performance para evitar estouro de memória no Lighthouse do Google
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

    # Tentativa 1: Com locale pt_BR
    # Tentativa 2: Fallback sem locale (resolve o erro 'Something went wrong' em sites pesados no Mobile)
    for attempt in range(2):
        try:
            current_params = params.copy()
            if attempt == 1:
                current_params.pop("locale", None) # Remove locale na 2ª tentativa se o Google falhou

            resp = requests.get(PAGESPEED_API, params=current_params, timeout=TIMEOUT_PAGESPEED)
            resp.raise_for_status()
            res_json = resp.json()
            
            if "error" not in res_json and "lighthouseResult" in res_json:
                data = res_json
                break
            elif "error" in res_json:
                last_error = res_json["error"].get("message", "Erro na API do Google")
        except requests.exceptions.Timeout:
            last_error = f"Tempo limite excedido ({TIMEOUT_PAGESPEED}s)."
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                return {"error": "Cota da API do PageSpeed excedida (erro 429)."}
            try:
                err_data = e.response.json()
                last_error = err_data.get("error", {}).get("message", str(e))
            except Exception:
                last_error = str(e)
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
            interpretation = {
                "level": "red",
                "text": "Melhorias no desempenho necessárias para que as campanhas obtenham melhores resultados."
            }
        elif 80 <= perf_score <= 90:
            interpretation = {
                "level": "orange",
                "text": "Pontuação positiva, porém com oportunidades de melhorias."
            }
        else:
            interpretation = {
                "level": "none",
                "text": "Boa pontuação! Sem grandes melhorias encontradas, detalhamento abaixo para que verifique as oportunidades."
            }
    else:
        interpretation = {"level": "none", "text": "Pontuação de performance indisponível."}

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

# ---------------------------------------------------------------------------
# 2. FETCH HTML & CHECAGEM DE LINKS QUEBRADOS
# ---------------------------------------------------------------------------
def fetch_html(url: str) -> str:
    headers = {**UA_HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_HTTP, allow_redirects=True)
    resp.raise_for_status()
    return resp.text

def check_broken_links(html: str, base_url: str) -> list:
    """Verifica links internos da página e identifica retornos de erro 404/500."""
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

# ---------------------------------------------------------------------------
# 3. TAGS
# ---------------------------------------------------------------------------
def detect_tags(html: str, gtm_js_content: str = "") -> dict:
    combined = html + "\n" + gtm_js_content

    ga4_html_only = set(re.findall(r"\bG-[A-Z0-9]{6,}\b", html))
    ads_html_only = set(re.findall(r"\bAW-[0-9]{5,}\b", html))

    pixel_matches = re.findall(r"fbq\(\\?['\"]init\\?['\"],\s*\\?['\"](\d{13,16})\\?['\"]", combined)
    pixel_matches += re.findall(r"id=(\d{13,16})", combined)

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
# 4. FORMULÁRIOS & PÁGINAS DE AGRADECIMENTO (Nativos + RD Station / Hubspot)
# ---------------------------------------------------------------------------
def detect_forms(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    form_id_counter = 1

    # A) Checagem de Formulários Nativos <form>
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
        has_thank_you_page = any(w in low for w in ["obrigad", "thank", "sucesso", "agradec"])

        if "wa.me" in low or "whatsapp" in low or "api.whatsapp" in low:
            destino = "WhatsApp (fora do CRM)"
        elif "mailto:" in low:
            destino = "e-mail direto"
        elif action_abs == "(mesma página)":
            destino = "mesma página (verificar JS de submit / webhook)"
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

    # B) Detecção de Formulários RD Station / Automação (Injetados via Script ou iFrame)
    rd_scripts = re.findall(r'd335luupugsy2\.cloudfront\.net.*?/([a-f0-9-]+)\.js', html)
    rd_forms_embed = soup.find_all(attrs={"data-rd-form": True}) or re.findall(r'RDStation\.Form\s*\(', html)
    
    if rd_scripts or rd_forms_embed or "rdstation" in html.lower():
        has_rd_thank_you = bool(re.search(r'(redirect_to|url_retorno|obrigad|thank|sucesso)', html, re.I))
        
        forms.append({
            "id": form_id_counter,
            "tipo": "RD Station / Pop-up de Automação",
            "fields": ["Campos carregados via script RD Station"],
            "action": "Endpoint da RD Station (d335luupugsy2.cloudfront.net)",
            "destino": "CRM / Automação RD Station",
            "num_campos": 1,
            "has_thank_you_page": has_rd_thank_you
        })
        form_id_counter += 1

    # C) Detecção de iFrames de Formulários Externos
    for iframe in soup.find_all("iframe", src=True):
        src = iframe.get("src", "").lower()
        if any(w in src for w in ["typeform", "hubspot", "activecampaign", "form"]):
            forms.append({
                "id": form_id_counter,
                "tipo": "Formulário Externo (iFrame)",
                "fields": ["Campos dentro do iFrame"],
                "action": iframe.get("src"),
                "destino": "Plataforma de Terceiros (iFrame)",
                "num_campos": 1,
                "has_thank_you_page": any(w in src for w in ["obrigad", "thank", "sucesso"])
            })
            form_id_counter += 1

    ctas = [a.get("href") for a in soup.find_all("a", href=True) if any(w in (a.get_text() or "").lower() for w in
            ["orçamento", "cotação", "contrat", "solicit", "comprar", "fale conosco", "saiba mais"])]
    duplicated_ctas = {href for href in ctas if ctas.count(href) > 1 and href not in ("#", "")}

    return {"forms": forms, "duplicated_cta_targets": sorted(duplicated_ctas)}

# ---------------------------------------------------------------------------
# 5. USABILIDADE / DESIGN
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
