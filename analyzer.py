def detect_forms(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    form_id_counter = 1

    # 1. Busca por formulários HTML nativos
    for form in soup.find_all("form"):
        action = form.get("action", "") or "(mesma página)"
        action_abs = urljoin(base_url, action) if action != "(mesma página)" else action
        fields = [f.get("name") or f.get("id") or "campo" for f in form.find_all(["input", "textarea", "select"]) if f.get("type") not in ("hidden", "submit", "button")]

        destino = "desconhecido"
        low = action_abs.lower()
        has_thank_you_page = any(w in low for w in ["obrigad", "thank", "sucesso", "agradec"])

        if "wa.me" in low or "whatsapp" in low:
            destino = "WhatsApp"
        elif "rdstation" in low or "rd.services" in low:
            destino = "RD Station CRM"
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

    # 2. Varredura aprofundada de RD Station (Popups, Scripts, Form ID, iFrames)
    html_low = html.lower()
    has_rd_script = bool(re.search(r'(d335luupugsy2\.cloudfront\.net|rdstation|RDStationForms|rd-form)', html, re.I))
    has_rd_attributes = bool(soup.find_all(attrs={"data-rd-form-id": True})) or ("rd-form" in html_low) or ("rdstation" in html_low)

    if has_rd_script or has_rd_attributes:
        # Extrai os IDs dos formulários da RD se presentes
        rd_ids = re.findall(r'data-rd-form-id=["\']([a-f0-9-]+)["\']', html, re.I)
        rd_ids_str = f" (ID: {', '.join(set(rd_ids))})" if rd_ids else ""

        forms.append({
            "id": form_id_counter,
            "tipo": "RD Station Marketing / Popup Embed",
            "fields": [f"Script de Captura Integrado{rd_ids_str}"],
            "action": "Endpoint Seguro RD Station",
            "destino": "RD Station CRM",
            "num_campos": 1,
            "has_thank_you_page": bool(re.search(r'(redirect_to|url_retorno|obrigad|thank)', html, re.I))
        })

    return {"forms": forms}
