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
        # Checa se no HTML existe indicação de redirecionamento/página de obrigado
        has_rd_thank_you = bool(re.search(r'(redirect_to|url_retorno|obrigad|thank|sucesso)', html, re.I))
        
        forms.append({
            "id": form_id_counter,
            "tipo": "RD Station / Pop-up de Automação",
            "fields": ["Campos carregados via script RD Station"],
            "action": "Endpoint da RD Station (d335luupugsy2.cloudfront.net)",
            "destino": "CRM / Automação RD Station",
            "num_campos": 1, # Representativo
            "has_thank_you_page": has_rd_thank_you
        })
        form_id_counter += 1

    # C) Detecção de iFrames de Formulários Externos (Typeform, HubSpot, etc.)
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
