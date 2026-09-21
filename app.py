"""
App web da ferramenta de análise técnica de sites.
Roda com: streamlit run app.py
Hospedagem gratuita: streamlit.io/cloud
"""
import streamlit as st
import streamlit.components.v1 as components
import io
import os
import re
from analyzer import (get_pagespeed, fetch_html, fetch_gtm_containers_content,
                       detect_tags, detect_forms, detect_usability_issues,
                       DEFAULT_PAGESPEED_API_KEY)
from report import build_pdf
from report_html import build_html_report

try:
    PAGESPEED_API_KEY = st.secrets.get("PAGESPEED_API_KEY", os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY))
except Exception:
    PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", DEFAULT_PAGESPEED_API_KEY)

st.set_page_config(page_title="Análise Técnica de Sites — Munz", page_icon="🔍", layout="wide")

st.title("🔍 Análise Técnica de Sites")
st.caption("PageSpeed, tags de rastreamento, formulários e usabilidade — visualização rápida na tela + download em PDF.")

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

    # Avisa o usuário sobre o tempo estimado da auditoria
    st.info("⏱️ **Tempo estimado:** A análise do PageSpeed pelo Google costuma levar entre **1 a 2 minutos**. Por favor, aguarde sem fechar a página.")

    progress = st.progress(0, text="Iniciando análise...")

    # [1/4] PageSpeed Mobile
    progress.progress(10, text="⏳ [1/4] Consultando PageSpeed Mobile no Google (pode levar até 60s)...")
    ps_mobile = get_pagespeed(url, "mobile", api_key=PAGESPEED_API_KEY)

    # [2/4] PageSpeed Desktop
    progress.progress(45, text="⏳ [2/4] Consultando PageSpeed Desktop no Google (pode levar até 60s)...")
    ps_desktop = get_pagespeed(url, "desktop", api_key=PAGESPEED_API_KEY)

    # [3/4] Download do HTML e tags
    progress.progress(80, text="🔍 [3/4] Baixando HTML do site e auditando tags GTM/GA4/Pixel...")
    try:
        html = fetch_html(url)
        html_ok = True
    except Exception:
        html = ""
        html_ok = False

    gtm_js_content = fetch_gtm_containers_content(html) if html_ok else ""

    if html_ok:
        tags = detect_tags(html, gtm_js_content)
        forms_data = detect_forms(html, url)
        usability_issues = detect_usability_issues(html, url)
    else:
        tags = {"gtm_containers": [], "ga4_properties": [], "google_ads_ids": [], "meta_pixel_ids": [], "issues": ["Não foi possível baixar o HTML do site (bloqueio anti-bot ou indisponibilidade)."]}
        forms_data = {"forms": [], "duplicated_cta_targets": []}
        usability_issues = []

    # [4/4] Gerando relatórios
    progress.progress(95, text="📄 [4/4] Montando visualização na tela e PDF...")
    
    # 1. Gera HTML para Preview
    html_report = build_html_report(
        cliente=cliente, url=url, is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data, usability_issues=usability_issues
    )

    # 2. Gera PDF para Download
    pdf_buffer = io.BytesIO()
    build_pdf(
        output_path=pdf_buffer, cliente=cliente, url=url, is_ecommerce=is_ecommerce,
        pagespeed_mobile=ps_mobile, pagespeed_desktop=ps_desktop,
        tags=tags, forms_data=forms_data, usability_issues=usability_issues
    )
    pdf_buffer.seek(0)
    progress.progress(100, text="Concluído!")

    st.success("Análise concluída com sucesso!")

    # Botão de Download do PDF
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

    st.subheader("📋 Preview do Relatório")
    components.html(html_report, height=800, scrolling=True)
