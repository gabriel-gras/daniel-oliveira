"""
src/atualizar_precos.py

Orquestrador (Passo 3 do plano 02): recebe o nome de um jogo, chama os 4
scrapers (Steam, GOG, Epic Games, Nuuvem) em paralelo, e salva os
resultados normalizados no banco de dados SQLite via src/database.py.
"""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from database import get_connection, init_db, inserir_ou_obter_jogo, inserir_preco
from scrapers import scrape_epic, scrape_gog, scrape_nuuvem, scrape_steam

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCRAPERS = {
    "Steam": scrape_steam,
    "GOG": scrape_gog,
    "Epic Games": scrape_epic,
    "Nuuvem": scrape_nuuvem,
}


def buscar_em_todas_as_lojas(termo: str) -> List[Dict[str, Any]]:
    """
    Executa os 4 scrapers em paralelo (threads de I/O) e consolida os
    resultados. Falha em uma loja não impede as demais — cada scraper já
    trata seus próprios erros internamente e retorna lista vazia se falhar.
    """
    resultados: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futuros = {executor.submit(func, termo): loja for loja, func in SCRAPERS.items()}

        for futuro in as_completed(futuros):
            loja = futuros[futuro]
            try:
                ofertas = futuro.result()
                logger.info(f"[{loja}] {len(ofertas)} resultado(s) para '{termo}'.")
                resultados.extend(ofertas)
            except Exception as e:
                # Rede de segurança extra; os scrapers já tratam suas exceções,
                # mas isso evita que um erro inesperado quebre o orquestrador.
                logger.error(f"[{loja}] Erro inesperado: {e}")

    return resultados


def salvar_resultados(resultados: List[Dict[str, Any]]) -> int:
    """
    Salva os resultados normalizados no banco de dados.

    Para cada oferta: garante que o jogo existe na tabela 'jogos' (usando o
    nome retornado pela própria loja, e a capa, se disponível) e insere o
    preço do dia na tabela 'precos'.

    Nota: cada loja pode formatar o nome do jogo de forma levemente
    diferente (ex.: "Hollow Knight" vs "Hollow Knight: Voidheart Edition").
    Nesta fase simples, cada nome distinto gera/usa seu próprio registro em
    'jogos'. Uma etapa de matching/normalização de nomes entre lojas pode
    ser tratada em uma fase futura, se necessário.
    """
    conn = get_connection()
    total_salvo = 0

    try:
        for oferta in resultados:
            id_jogo = inserir_ou_obter_jogo(
                conn,
                nome=oferta["jogo"],
                capa_url=oferta.get("capa"),
            )
            inserir_preco(
                conn,
                id_jogo=id_jogo,
                loja=oferta["loja"],
                preco=oferta["preco"],
                url_compra=oferta.get("url_compra"),
            )
            total_salvo += 1
    finally:
        conn.close()

    return total_salvo


def atualizar_precos(termo: str) -> None:
    logger.info(f"Iniciando busca de preços para: '{termo}'")
    resultados = buscar_em_todas_as_lojas(termo)

    if not resultados:
        logger.warning("Nenhum resultado encontrado em nenhuma loja.")
        return

    total = salvar_resultados(resultados)
    logger.info(f"{total} oferta(s) salva(s) no banco de dados para '{termo}'.")


if __name__ == "__main__":
    init_db()  # garante que as tabelas existem antes de salvar

    if len(sys.argv) < 2:
        print('Uso: python src/atualizar_precos.py "nome do jogo"')
        sys.exit(1)

    termo_busca = " ".join(sys.argv[1:])
    atualizar_precos(termo_busca)
