# Ferramenta de Análise Técnica de Sites

Gera um relatório em PDF com PageSpeed (mobile + desktop), tags de rastreamento
instaladas, formulários e checagens de usabilidade — para usar sempre que um
projeto novo chegar na agência.

Não usa IA / API paga em nenhuma etapa: só requisições HTTP diretas e leitura
de HTML. Cada analista pode rodar na própria máquina.

## Instalação (uma vez só, por analista)

1. Ter Python 3.9+ instalado ([python.org/downloads](https://www.python.org/downloads/))
2. Abrir o terminal na pasta da ferramenta e rodar:

```bash
pip install -r requirements.txt
```

## Configure a chave gratuita do PageSpeed (recomendado)

Sem chave, a ferramenta funciona, mas usa uma cota pública compartilhada com
todo mundo que faz esse tipo de chamada sem se identificar — com mais de um
analista testando, ela esgota rápido e a API passa a devolver erro 429 (Too
Many Requests). Com uma chave gratuita, o limite sobe para 25.000 consultas
por dia (mais que suficiente).

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/) e crie um projeto (ou use um existente).
2. No menu, vá em **APIs e serviços → Biblioteca**, busque por **"PageSpeed Insights API"** e clique em **Ativar**.
3. Vá em **APIs e serviços → Credenciais → Criar credenciais → Chave de API**.
4. Copie a chave gerada.

**Se for rodar via navegador (Streamlit Cloud):**
No painel do seu app em [share.streamlit.io](https://share.streamlit.io), clique em
**⚙️ Settings → Secrets** e cole:
```
PAGESPEED_API_KEY = "sua-chave-aqui"
```
Salve — o app reinicia sozinho e passa a usar a chave automaticamente.

**Se for rodar localmente (linha de comando):**
```bash
python site_audit.py --url https://site.com.br --cliente "Cliente Y" --api-key "sua-chave-aqui"
```
Ou defina a variável de ambiente `PAGESPEED_API_KEY` uma vez e não precisa mais passar `--api-key` toda hora.

## Como usar (via navegador — recomendado para a equipe)

A forma mais fácil para todos os analistas usarem sem instalar nada é hospedar
o `app.py` (feito em Streamlit) na nuvem, gratuitamente:

1. Crie uma conta em [github.com](https://github.com) (se ainda não tiver) e suba esta pasta
   inteira como um repositório novo (pode ser privado).
2. Crie uma conta em [share.streamlit.io](https://share.streamlit.io) (login com o GitHub).
3. Clique em **"New app"**, selecione o repositório e aponte o arquivo principal
   para `app.py`.
4. Clique em **Deploy**. Em 1-2 minutos você recebe uma URL fixa, tipo:
   `https://munz-site-audit.streamlit.app`
5. Envie essa URL para os outros analistas — eles só precisam abrir no
   navegador, preencher URL + nome do cliente e clicar em "Analisar site".
   O PDF é gerado e baixado direto pelo navegador, sem instalar nada.

**Custo:** gratuito no plano Community do Streamlit para esse volume de uso
(o app "dorme" depois de um tempo sem acesso e acorda em alguns segundos
quando alguém entra de novo — normal no plano free).

**Se quiser algo mais robusto no futuro** (domínio próprio, sem "dormir",
mais controle), as mesmas 3 pastas (`analyzer.py`, `report.py`, `app.py`)
rodam sem alteração em qualquer serviço que suporte Python, como Render.com
ou Railway.app — é só apontar o comando de start para
`streamlit run app.py --server.port $PORT`.

## Como usar (linha de comando — alternativa local)

```bash
python site_audit.py --url https://www.sitedocliente.com.br --cliente "Nome do Cliente"
```

Isso gera `relatorio-nome-do-cliente.pdf` na mesma pasta.

### Se o projeto for um e-commerce

Adicione a flag `--ecommerce` — o PDF vai incluir uma página extra com
checklist para o analista preencher manualmente durante a navegação no
carrinho/checkout (eventos de add_to_cart, checkout, purchase, etc.):

```bash
python site_audit.py --url https://www.loja.com.br --cliente "Loja X" --ecommerce
```

### Escolher onde salvar o PDF

```bash
python site_audit.py --url https://site.com.br --cliente "Cliente Y" --saida "C:\Relatorios\cliente-y.pdf"
```

## O que a ferramenta verifica automaticamente

| Seção | O que faz |
|---|---|
| **PageSpeed** | Chama a API do Google (mobile e desktop): scores de Performance, Acessibilidade, Boas Práticas, SEO + Core Web Vitals + top oportunidades de melhoria |
| **Tags** | Detecta contêineres GTM, propriedades GA4, IDs de Google Ads e Meta Pixel — tanto soltos no HTML quanto configurados **dentro** do container GTM (lendo o `gtm.js` publicado); sinaliza duplicidade de tags |
| **Formulários** | Lista os formulários da página, campos coletados e para onde cada um envia os dados (CRM, WhatsApp, e-mail, etc.) |
| **Usabilidade** | Verifica meta viewport, título, meta description, atributos alt em imagens, HTTPS, favicon, H1 duplicado/ausente, CTAs duplicados apontando pro mesmo destino |
| **E-commerce** (opcional) | Adiciona página de checklist manual para o analista validar o fluxo de compra |

## Limitações importantes

- **Sites com proteção anti-bot forte (Cloudflare, etc.)** podem bloquear o
  download do HTML. Quando isso acontece, o PDF é gerado mesmo assim, mas as
  seções de Tags/Formulários/Usabilidade ficam vazias (o PageSpeed continua
  funcionando normalmente, pois usa a API oficial do Google).
- **PageSpeed sem chave de API** está sujeito a uma cota pública baixa e pode
  devolver erro 429 quando vários analistas usam ao mesmo tempo — configure
  a chave gratuita (seção acima) para evitar isso.
- **Fluxo de compra de e-commerce** não é testado automaticamente — precisa de
  navegação manual (checklist incluído no PDF).
- **Design/UX subjetivo** (clareza da oferta, copy, hierarquia visual) continua
  exigindo o olhar do analista — a ferramenta cobre apenas os pontos técnicos
  objetivos (o que já cobre boa parte dos itens do relatório-modelo).
- A ferramenta lê o HTML estático da página + o conteúdo publicado de
  qualquer container GTM encontrado (isso cobre a maioria das tags de Google
  Ads/GA4 configuradas dentro do GTM). Ainda assim, sites que renderizam
  formulários via JavaScript pesado (SPAs em React/Vue sem SSR) ou tags
  carregadas por um gerenciador diferente do GTM podem não ter tudo
  detectado — nesse caso, vale conferir manualmente com a extensão Tag
  Assistant do Google.

## Compartilhando com outros analistas

Basta enviar esta pasta inteira (ou subir num repositório Git interno). Cada
analista só precisa instalar as dependências uma vez (`pip install -r requirements.txt`).
