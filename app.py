"""
App web da ferramenta de análise técnica de sites.
Roda com: streamlit run app.py
"""
import streamlit as st
import streamlit.components.v1 as components
import io
import os
import re
from analyzer import (get_pagespeed, fetch_html, check_broken_links, fetch_gtm_containers_content,
                       detect_tags, detect_forms, detect_usability_issues,
                       DEFAULT_PAGESPEED_API_KEY)
from ai_analyst import generate_ai_insights
from report import build_pdf
from report_html import build_html_report

try:
    PAGESPEED_API_KEY = st.secrets.get("PAGESPEED_API_KEY", os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY))
except Exception:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY)

st.set_page_config(page_title="Análise Técnica de Sites — Munz", page_icon="🔍", layout="wide")

st.title("🔍 Análise Técnica de Sites")
st.caption("PageSpeed, tags de rastreamento, formulários, links quebrados e parecer inteligente via Gemini AI.")

with st.form("audit_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        url_input = st.text_input("URL do site", placeholder="https://www.sitedocliente.com.br")
    with col2:
        cliente = st.text_input("Nome do cliente/projeto", placeholder="Ex: Agência Mestre")
    is_ecommerce = st.checkbox("Este projeto é um E-commerce")
    submitted = st.form_submit_button("Analisar site", use_container_width=True)

if submitted:
    if not url_input or not cliente:
        st.error("Preencha a URL e o nome do cliente antes de continuar.")
        st.stop()

    url = url_input if url_input.startswith("http") else f"https://{url_input}"

    st.info("⏱️ **Tempo estimado:** A análise técnica completa leva cerca de **1 a 2 minutos**. Por favor, aguarde.")

    progress = st.progress(0, text="Iniciando análise...")

    # [1/6] PageSpeed Mobile
    progress.progress(10, text="⏳ [1/6] Consultando PageSpeed Mobile no Google...")
    ps_mobile = get_pagespeed(url, "mobile", api_key=PAGESPEED_API_KEY)

    # [2/6] PageSpeed Desktop
    progress.progress(35, text="⏳ [2/6] Consultando PageSpeed Desktop no Google...")
    ps_desktop = get_pagespeed(url, "desktop", api_key=PAGESPEED_API_KEY)

    # [3/6] HTML & Links Quebrados
    progress.progress(60, text="🔍 [3/6] Baixando HTML e checando se há links quebrados...")
    try:
        html = fetch_html(url)
        html_ok = True
        broken_links = check_broken_links(html, url)
    except Exception:
        html = ""
        html_ok = False
        broken_links = []

    # [4/6] Tags e Formulários
    progress.progress(75, text="📊 [4/6] Auditando tags GTM/GA4/Pixel e formulários...")
    gtm_js_content = fetch_gtm_containers_content(html) if html_ok else ""

    if html_ok:
        tags = detect_tags(html, gtm_js_content)
        forms_data = detect_forms(html, url)
        usability_issues = detect_usability_issues(html, url)
    else:
        tags = {"gtm_containers": [], "ga4_properties": [], "google_ads_ids": [], "meta_pixel_ids": [], "issues": ["Não foi possível baixar o HTML do site."]}
        forms_data = {"forms": [], "duplicated_cta_targets": []}
        usability_issues = []

    # [5/6] Inteligência Artificial Gemini
    progress.progress(88, text="🤖 [5/6] Gemini AI gerando pareceres técnicos e resumo executivo...")
    ai_insights = generate_ai_insights(
        cliente=cliente, url=url,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data,
        usability_issues=usability_issues, broken_links=broken_links
    )

    # [6/6] Compilação dos Relatórios
    progress.progress(98, text="📄 [6/6] Compilando visualização na tela e PDF...")
    
    html_report = build_html_report(
        cliente=cliente, url=url, is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data, usability_issues=usability_issues,
        broken_links=broken_links, ai_insights=ai_insights
    )

    pdf_buffer = io.BytesIO()
    build_pdf(
        output_path=pdf_buffer, cliente=cliente, url=url, is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data, usability_issues=usability_issues,
        broken_links=broken_links, ai_insights=ai_insights
    )
    pdf_buffer.seek(0)
    progress.progress(100, text="Concluído!")

    st.success("Análise concluída com sucesso!")

    slug = re.sub(r"[^\w\s-]", "", cliente).strip().lower()
    slug = re.sub(r"[\s]+", "-", slug)
    
    st.download_button(
        label="📄 Baixar Relatório em PDF",
        data=pdf_buffer,
        file_name=f"relatorio-{slug}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

    st.subheader("📋 Preview do Relatório com Análise por IA")
    components.html(html_report, height=850, scrolling=True)
