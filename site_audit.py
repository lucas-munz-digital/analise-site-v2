#!/usr/bin/env python3
"""
Ferramenta de análise técnica de sites — Munz Digital
Uso:
    python site_audit.py --url https://www.exemplo.com.br --cliente "Nome do Cliente"
    python site_audit.py --url https://loja.com.br --cliente "Loja X" --ecommerce
"""
import argparse
import sys
import re
from analyzer import (get_pagespeed, fetch_html, fetch_gtm_containers_content,
                       detect_tags, detect_forms, detect_usability_issues)
from report import build_pdf


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s]+", "-", text)


def main():
    parser = argparse.ArgumentParser(description="Análise técnica automatizada de sites")
    parser.add_argument("--url", required=True, help="URL do site a ser analisado")
    parser.add_argument("--cliente", required=True, help="Nome do cliente/projeto")
    parser.add_argument("--ecommerce", action="store_true", help="Marca o projeto como E-commerce")
    parser.add_argument("--saida", default=None, help="Caminho do PDF de saída (opcional)")
    parser.add_argument("--api-key", default=None,
                         help="Chave da API do PageSpeed (opcional; também pode vir da variável de ambiente PAGESPEED_API_KEY). Veja README.md.")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else f"https://{args.url}"
    output_path = args.saida or f"relatorio-{slugify(args.cliente)}.pdf"

    print(f"→ Analisando {url} ...")

    print("  [1/6] PageSpeed mobile...")
    ps_mobile = get_pagespeed(url, "mobile", api_key=args.api_key)
    if "error" in ps_mobile:
        print(f"  aviso: {ps_mobile['error']}")

    print("  [2/6] PageSpeed desktop...")
    ps_desktop = get_pagespeed(url, "desktop", api_key=args.api_key)

    print("  [3/6] Baixando HTML...")
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  ERRO ao baixar HTML: {e}")
        html = ""

    print("  [4/6] Lendo containers GTM (se houver)...")
    gtm_js_content = fetch_gtm_containers_content(html) if html else ""

    print("  [5/6] Detectando tags e formulários...")
    tags = detect_tags(html, gtm_js_content) if html else {"gtm_containers": [], "ga4_properties": [], "google_ads_ids": [],
                                             "meta_pixel_ids": [], "gtag_ids": [],
                                             "issues": ["Não foi possível baixar o HTML da página."]}
    forms_data = detect_forms(html, url) if html else {"forms": [], "duplicated_cta_targets": []}

    print("  [6/6] Checando usabilidade...")
    usability_issues = detect_usability_issues(html, url) if html else []

    print(f"→ Gerando PDF em {output_path} ...")
    build_pdf(
        output_path=output_path,
        cliente=args.cliente,
        url=url,
        is_ecommerce=args.ecommerce,
        pagespeed_mobile=ps_mobile,
        pagespeed_desktop=ps_desktop,
        tags=tags,
        forms_data=forms_data,
        usability_issues=usability_issues,
    )
    print("✓ Concluído!")


if __name__ == "__main__":
    main()
