"""
App web da ferramenta de análise técnica de sites.
Roda com: streamlit run app.py
Hospedagem gratuita: streamlit.io/cloud (ver README.md)
"""
import streamlit as st
import io
import os
import re
from analyzer import (get_pagespeed, fetch_html, fetch_gtm_containers_content,
                       detect_tags, detect_forms, detect_usability_issues,
                       DEFAULT_PAGESPEED_API_KEY)
from report import build_pdf

# A chave pode vir dos "Secrets" do Streamlit Cloud, de uma variável de ambiente,
# ou usará por padrão a chave embutida da Agência Mestre.
try:
    PAGESPEED_API_KEY = st.secrets.get("PAGESPEED_API_KEY", os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY))
except Exception:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY)

st.set_page_config(page_title="Análise Técnica de Sites — Munz", page_icon="🔍", layout="centered")

st.title("🔍 Análise Técnica de Sites")
st.caption("PageSpeed, tags de rastreamento, formulários e usabilidade — gera um PDF pronto pra enviar ao cliente.")

with st.form("audit_form"):
    url_input = st.text_input("URL do site", placeholder="https://www.sitedocliente.com.br")
    cliente = st.text_input("Nome do cliente/projeto", placeholder="Ex: New Line Segurança")
    is_ecommerce = st.checkbox("Este projeto é um E-commerce")
    submitted = st.form_submit_button("Analisar site", use_container_width=True)

if submitted:
    if not url_input or not cliente:
        st.error("Preencha a URL e o nome do cliente antes de continuar.")
        st.stop()

    url = url_input if url_input.startswith("http") else f"https://{url_input}"

    progress = st.progress(0, text="Iniciando análise...")

    progress.progress(10, text="Consultando PageSpeed (mobile)...")
    ps_mobile = get_pagespeed(url, "mobile", api_key=PAGESPEED_API_KEY)
    if "error" in ps_mobile:
        st.warning(f"PageSpeed mobile: {ps_mobile['error']}")

    progress.progress(25, text="Consultando PageSpeed (desktop)...")
    ps_desktop = get_pagespeed(url, "desktop", api_key=PAGESPEED_API_KEY)

    progress.progress(45, text="Baixando HTML do site...")
    try:
        html = fetch_html(url)
        html_ok = True
    except Exception as e:
        html = ""
        html_ok = False
        st.warning(f"Não foi possível baixar o HTML do site ({e}). "
                   "O PDF será gerado só com os dados de PageSpeed. "
                   "Isso costuma acontecer em sites com proteção anti-bot (Cloudflare, etc.).")

    progress.progress(60, text="Lendo containers GTM (se houver)...")
    gtm_js_content = fetch_gtm_containers_content(html) if html_ok else ""

    progress.progress(75, text="Detectando tags e formulários...")
    if html_ok:
        tags = detect_tags(html, gtm_js_content)
        forms_data = detect_forms(html, url)
    else:
        tags = {"gtm_containers": [], "ga4_properties": [], "google_ads_ids": [], "meta_pixel_ids": [],
                "gtag_ids": [], "issues": []}
        forms_data = {"forms": [], "duplicated_cta_targets": []}

    progress.progress(88, text="Checando usabilidade...")
    usability_issues = detect_usability_issues(html, url) if html_ok else []

    progress.progress(95, text="Gerando PDF...")
    buffer = io.BytesIO()
    build_pdf(
        output_path=buffer,
        cliente=cliente,
        url=url,
        is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile,
        pagespeed_desktop=ps_desktop,
        tags=tags,
        forms_data=forms_data,
        usability_issues=usability_issues,
    )
    buffer.seek(0)
    progress.progress(100, text="Concluído!")

    st.success("Relatório gerado com sucesso.")

    # Preview rápido dos scores na tela, além do PDF
    if "error" not in ps_mobile:
        cols = st.columns(4)
        labels = [("Performance", "performance"), ("Acessibilidade", "accessibility"),
                  ("Boas práticas", "best_practices"), ("SEO", "seo")]
        for col, (label, key) in zip(cols, labels):
            col.metric(label, ps_mobile["scores"].get(key, "-"))

    slug = re.sub(r"[^\w\s-]", "", cliente).strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)
    st.download_button(
        label="⬇️ Baixar PDF do relatório",
        data=buffer,
        file_name=f"relatorio-{slug}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )