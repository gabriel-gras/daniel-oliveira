"""
src/scrapers.py

Rotinas de extração de preços de jogos nas 4 lojas de PC suportadas:
Steam, GOG, Epic Games e Nuuvem.

Conforme Spec 01 (docs/specs/01-scraping-pc.md):
- Sem Playwright/Selenium - apenas `requests` + `BeautifulSoup4`.
- Saída sempre normalizada no formato:
  {"jogo": str, "capa": str | None, "loja": str, "preco": float, "url_compra": str}
"""

import logging
import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

TIMEOUT = 10


def _normalizar(
    jogo: str,
    capa: Optional[str],
    loja: str,
    preco: float,
    url_compra: Optional[str],
) -> Dict[str, Any]:
    return {
        "jogo": jogo,
        "capa": capa,
        "loja": loja,
        "preco": round(float(preco), 2),
        "url_compra": url_compra,
    }


# ---------------------------------------------------------------------------
# STEAM
# ---------------------------------------------------------------------------
def scrape_steam(termo: str) -> List[Dict[str, Any]]:
    """
    Busca jogos na Steam via API pública de busca da loja.
    Endpoint: store.steampowered.com/api/storesearch
    """

    url = "https://store.steampowered.com/api/storesearch/"
    params = {"term": termo, "l": "portuguese", "cc": "BR"}
    resultados: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        dados = resp.json()
        for item in dados.get("items", []):
            nome = item.get("name")
            app_id = item.get("id")
            price_info = item.get("price")
            if not nome or not price_info:
                continue
            preco_centavos = price_info.get("final")
            if preco_centavos is None:
                continue
            preco = preco_centavos / 100
            link = f"https://store.steampowered.com/app/{app_id}"
            # Capa: header.jpg é o asset padrão da Steam para cada app_id,
            # não requer chamada extra à API.
            capa = (
                f"https://shared.akamai.steamstatic.com/store_item_assets/"
                f"steam/apps/{app_id}/header.jpg"
                if app_id
                else None
            )
            resultados.append(_normalizar(nome, capa, "Steam", preco, link))
    except (requests.RequestException, ValueError, KeyError):
        pass
    return resultados


# ---------------------------------------------------------------------------
# GOG
# ---------------------------------------------------------------------------
def scrape_gog(termo: str) -> List[Dict[str, Any]]:
    """
    Busca jogos na GOG em duas etapas:

    1. catalog.gog.com com 'query=like:{termo}' (SEM countryCode/currencyCode/
       locale -- confirmado que esses params zeram os resultados quando
       combinados com 'like:') para localizar o(s) produto(s) e seus IDs.
    2. api.gog.com/products/{id}/prices?countryCode=BR para obter o preço
       REAL publicado pela GOG em BRL para cada produto encontrado -- nada
       de conversão por câmbio, é o valor exato que aparece na loja.
    """
    url_busca = "https://catalog.gog.com/v1/catalog"
    params_busca = {"query": f"like:{termo}", "limit": 10}
    headers = {
        **HEADERS,
        "Referer": "https://www.gog.com/",
        "Accept": "application/json",
    }

    resultados: List[Dict[str, Any]] = []

    try:
        resp = requests.get(url_busca, headers=headers, params=params_busca, timeout=TIMEOUT)
        resp.raise_for_status()
        produtos = resp.json().get("products", [])

        for produto in produtos:
            nome = produto.get("title")
            id_produto = produto.get("id")
            slug = produto.get("slug")

            if not nome or not id_produto:
                continue

            preco = _obter_preco_brl_gog(id_produto)
            if preco is None:
                # Sem preço confiável em BRL para esse produto -- melhor
                # omitir a oferta do que salvar um valor aproximado/errado.
                continue

            capa = _construir_capa_gog(produto)
            link = f"https://www.gog.com/game/{slug}" if slug else None
            resultados.append(_normalizar(nome.strip(), capa, "GOG", preco, link))

    except Exception as e:
        logger.warning(f"[GOG] Falha ao buscar catálogo: {e}")

    return resultados


def _construir_capa_gog(produto: Dict[str, Any]) -> Optional[str]:
    """
    Monta a URL da capa a partir do campo de imagem base retornado pelo
    catalog.gog.com. O catálogo normalmente expõe a imagem em
    'coverHorizontal' ou 'cover', como URL protocol-relative (//...) e SEM
    extensão/sufixo de formatação -- a GOG espera que o sufixo de tamanho
    seja anexado pelo cliente.

    Se nenhum campo de imagem for encontrado, retorna None (melhor omitir
    a capa do que linkar uma imagem quebrada).
    """
    bruta = (
        produto.get("coverHorizontal")
        or produto.get("cover")
        or produto.get("image")
    )
    if not bruta:
        return None

    if bruta.startswith("//"):
        bruta = f"https:{bruta}"

    # Se a URL já vier com extensão de imagem, usamos como está.
    # Caso contrário, anexamos o sufixo de formatação padrão da GOG.
    if not re.search(r"\.(jpg|jpeg|png|webp)(\?.*)?$", bruta, re.IGNORECASE):
        bruta = f"{bruta}_product_card_v2_mobile_slider_639.jpg"

    return bruta


def _obter_preco_brl_gog(id_produto: str) -> Optional[float]:
    """
    Consulta o preço real em BRL publicado pela GOG para um produto
    específico. Retorna None se a chamada falhar ou não houver BRL
    disponível para esse produto (alguns IDs não têm preço listado).

    Formato de resposta confirmado em produção (2026-06-29):
        {"_embedded": {"prices": [
            {"currency": {"code": "BRL"}, "finalPrice": "7985 BRL", ...},
            {"currency": {"code": "USD"}, "finalPrice": "1635 USD", ...}
        ]}}

    Atenção: aqui o valor vem como STRING DE CENTAVOS + sufixo de moeda
    (ex.: "7985 BRL" = R$ 79,85) -- formato diferente do catalog.gog.com,
    que usa string decimal (ex.: "79.85"). Não confundir os dois.
    """
    try:
        resp = requests.get(
            f"https://api.gog.com/products/{id_produto}/prices",
            params={"countryCode": "BR"},
            headers={"Accept": "application/json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()

        precos = resp.json().get("_embedded", {}).get("prices", [])
        preco_brl = next(
            (p for p in precos if p.get("currency", {}).get("code") == "BRL"),
            None,
        )

        if not preco_brl or "finalPrice" not in preco_brl:
            return None

        valor_centavos_str = preco_brl["finalPrice"].split(" ")[0]
        return float(valor_centavos_str) / 100

    except Exception as e:
        logger.warning(f"[GOG] Falha ao obter preço BRL do produto {id_produto}: {e}")
        return None


# ---------------------------------------------------------------------------
# EPIC GAMES
# ---------------------------------------------------------------------------
def scrape_epic(termo: str) -> List[Dict[str, Any]]:
    """
    Busca jogos na Epic Games Store via GraphQL (searchStoreQuery).
    Conforme Spec 01: sem ferramentas de browser; em caso de bloqueio/erro
    a função degrada graciosamente e retorna lista vazia (fallback simples).
    """
    url = "https://store.epicgames.com/graphql"
    headers_epic = {
        **HEADERS,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://store.epicgames.com/pt-BR/browse",
        "Origin": "https://store.epicgames.com",
    }
    # Adicionado keyImages{type url} ao query original para conseguir a capa
    # sem precisar de uma segunda chamada.
    query_string = (
        "query searchStoreQuery($keywords:String,$country:String!,$locale:String){"
        "Catalog{searchStore(keywords:$keywords,country:$country,locale:$locale,count:10){"
        "elements{title productSlug urlSlug keyImages{type url} "
        "price(country:$country){totalPrice{discountPrice}}}}}}"
    )
    payload = {
        "operationName": "searchStoreQuery",
        "query": query_string,
        "variables": {"keywords": termo, "country": "BR", "locale": "pt-BR"},
    }
    resultados: List[Dict[str, Any]] = []
    try:
        resp = requests.post(url, headers=headers_epic, json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            dados = resp.json()
            elementos = dados.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
            for item in elementos:
                nome = item.get("title")
                price_block = item.get("price", {}).get("totalPrice", {})
                preco_centavos = price_block.get("discountPrice")
                if not nome or preco_centavos is None:
                    continue
                preco = preco_centavos / 100
                slug = item.get("urlSlug") or item.get("productSlug")
                link = f"https://store.epicgames.com/pt-BR/p/{slug}" if slug else None
                capa = _extrair_capa_epic(item)
                resultados.append(_normalizar(nome, capa, "Epic Games", preco, link))
    except Exception:
        pass
    return resultados


def _extrair_capa_epic(item: Dict[str, Any]) -> Optional[str]:
    """
    Procura em keyImages pela imagem mais adequada para exibição em lista/
    card, na ordem de preferência OfferImageWide > Thumbnail. Retorna None
    se nenhuma das duas estiver presente.
    """
    imagens = item.get("keyImages", []) or []
    for tipo_preferido in ("OfferImageWide", "Thumbnail"):
        for img in imagens:
            if img.get("type") == tipo_preferido and img.get("url"):
                return img["url"]
    return None


# ---------------------------------------------------------------------------
# NUUVEM
# ---------------------------------------------------------------------------
def scrape_nuuvem(termo: str) -> List[Dict[str, Any]]:
    """
    Busca jogos na Nuuvem via parsing direto do HTML da página de busca
    (não há API pública documentada, conforme Spec 01).

    Atenção: por ser parsing de HTML, os seletores CSS abaixo são os mais
    estáveis observados no layout atual do site, mas podem precisar de
    ajuste caso a Nuuvem mude o front-end.
    """

    locale = "br-pt"
    termo_url = termo.replace(" ", "%20")
    url = f"https://www.nuuvem.com/{locale}/catalog/page/1/search/{termo_url}"
    resultados: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links_produto = soup.select('a[href*="/item/"], a[href*="/bundle/"]')
        for link_tag in links_produto:
            nome = link_tag.get("title") or link_tag.get_text(strip=True)
            if not nome:
                continue
            href = link_tag.get("href")
            if href and href.startswith("/"):
                href = f"https://www.nuuvem.com{href}"
            preco = _extrair_preco_brl(link_tag.get_text(" ", strip=True))
            if preco is None:
                continue
            capa = _extrair_capa_nuuvem(link_tag)
            resultados.append(_normalizar(nome.strip(), capa, "Nuuvem", preco, href))
    except Exception:
        pass
    return resultados


def _extrair_capa_nuuvem(link_tag) -> Optional[str]:
    """
    Procura uma tag <img> dentro do próprio link de produto (caso o card
    inteiro seja o <a>) ou, como fallback, dentro do elemento pai (caso a
    imagem esteja num elemento irmão dentro do mesmo card). Prioriza
    'data-src' (lazy-load) sobre 'src', já que muitos cards na Nuuvem
    carregam a imagem via lazy-loading.
    """
    img_tag = link_tag.find("img")
    if img_tag is None and link_tag.parent is not None:
        img_tag = link_tag.parent.find("img")
    if img_tag is None:
        return None

    capa = img_tag.get("data-src") or img_tag.get("src")
    if not capa:
        return None
    if capa.startswith("//"):
        capa = f"https:{capa}"
    return capa


def _extrair_preco_brl(texto: str) -> Optional[float]:
    """
    Converte texto de preço no formato brasileiro (ex.: 'R$ 79,90')
    para float (79.90). Retorna None se não conseguir extrair um número.
    """

    matches = re.findall(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})", texto)
    if not matches:
        return None
    valor = matches[-1]
    valor = valor.replace(".", "").replace(",", ".") if "." in valor else valor.replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None