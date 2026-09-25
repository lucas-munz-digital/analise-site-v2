"""
App web da ferramenta de análise técnica de sites — Agência Mestre.
Gera relatórios em HTML Widescreen (Presentation Deck) nativo.
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import re
from analyzer import (get_pagespeed, fetch_html, extract_page_context, check_broken_links, fetch_gtm_containers_content,
                       detect_tags, detect_forms, detect_usability_issues,
                       DEFAULT_PAGESPEED_API_KEY)
from ai_analyst import generate_ai_insights
from report_html import build_html_report

try:
    PAGESPEED_API_KEY = st.secrets.get("PAGESPEED_API_KEY", os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY))
except Exception:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY)

st.set_page_config(page_title="Análise do Site para Mídia — Agência Mestre", page_icon="⚡", layout="wide")

col_logo, col_title = st.columns([1, 4])
with col_logo:
    possible_logos = ["agncia_mestre_logo.jpeg", "agncia_mestre_logo.jpg", "logo_mestre.jpg", "logo_mestre.png"]
    logo_path = next((f for f in possible_logos if os.path.exists(f)), None)
    if logo_path:
        st.image(logo_path, width=110)
    else:
        st.markdown("### **MESTRE**")

with col_title:
    st.title("Análise Técnica do Site — Foco em Mídia")
    st.caption("Diagnóstico de Performance, Tracking, Conversão e UX/CRO em formato de Deck Executivo.")

st.markdown("---")

with st.form("audit_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        url_input = st.text_input("URL do site", placeholder="https://www.sitedocliente.com.br")
    with col2:
        cliente = st.text_input("Nome do cliente/projeto", placeholder="Ex: TP-Link | Vigi")
    is_ecommerce = st.checkbox("Este projeto é um E-commerce")
    submitted = st.form_submit_button("Gerar Análise para Mídia", use_container_width=True)

if submitted:
    if not url_input or not cliente:
        st.error("Preencha a URL e o nome do cliente antes de continuar.")
        st.stop()

    url = url_input if url_input.startswith("http") else f"https://{url_input}"

    progress = st.progress(0, text="Iniciando auditoria...")

    progress.progress(15, text="⏳ Auditando PageSpeed Mobile...")
    ps_mobile = get_pagespeed(url, "mobile", api_key=PAGESPEED_API_KEY)

    progress.progress(40, text="⏳ Auditando PageSpeed Desktop...")
    ps_desktop = get_pagespeed(url, "desktop", api_key=PAGESPEED_API_KEY)

    progress.progress(60, text="🔍 Mapeando estrutura e links...")
    try:
        html = fetch_html(url)
        html_ok = True
        page_context = extract_page_context(html)
        broken_links = check_broken_links(html, url)
    except Exception:
        html = ""
        html_ok = False
        page_context = {}
        broken_links = []

    progress.progress(75, text="📊 Identificando tags e formulários...")
    gtm_js_content = fetch_gtm_containers_content(html) if html_ok else ""

    if html_ok:
        tags = detect_tags(html, gtm_js_content)
        forms_data = detect_forms(html, url)
        usability_issues = detect_usability_issues(html, url)
    else:
        tags = {"gtm_containers": [], "ga4_properties": [], "google_ads_ids": [], "meta_pixel_ids": [], "issues": ["Não foi possível baixar o HTML."]}
        forms_data = {"forms": []}
        usability_issues = []

    progress.progress(88, text="🤖 Gemini AI formulando pareceres estratégicos...")
    ai_insights = generate_ai_insights(
        cliente=cliente, url=url,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data,
        usability_issues=usability_issues, broken_links=broken_links,
        page_context=page_context
    )

    progress.progress(98, text="📄 Compilando Presentation Deck HTML...")
    html_report = build_html_report(
        cliente=cliente, url=url, is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data, usability_issues=usability_issues,
        broken_links=broken_links, ai_insights=ai_insights
    )
    progress.progress(100, text="Concluído!")

    st.success("Relatório gerado com sucesso!")

    slug = re.sub(r"[^\w\s-]", "", cliente).strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)

    st.download_button(
        label="🌐 Baixar Relatório HTML (Deck 16:9 Nativo)",
        data=html_report,
        file_name=f"analise-site-midia-{slug}.html",
        mime="text/html",
        type="primary",
        use_container_width=True
    )

    st.subheader("📋 Presentation Deck Interativo")
    components.html(html_report, height=800, scrolling=True)
