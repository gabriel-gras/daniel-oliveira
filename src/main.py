from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from src.database import get_connection, init_db
from src.models import Jogo, Oferta, HistoricoPreco, PrecosResponse

app = FastAPI(
    title="GamePrice Comparator API",
    description="API leve para comparação de preços de jogos de PC.",
    version="0.1.0",
)


@app.on_event("startup")
def startup_event():
    """Garante que as tabelas existam ao iniciar a aplicação."""
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "GamePrice Comparator API"}


@app.get("/api/search", response_model=List[Jogo])
def search_jogo(q: str = Query(..., min_length=1, description="Nome do jogo a buscar")):
    """
    Busca jogos pelo nome (busca parcial, case-insensitive).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, capa_url FROM jogos WHERE nome LIKE ? COLLATE NOCASE",
        (f"%{q}%",),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        # Por enquanto, sem dados no banco, retornamos um exemplo fictício
        # apenas para validar a rota durante o desenvolvimento inicial.
        return [Jogo(id=0, nome=f"[MOCK] Resultado para '{q}'", capa_url=None)]

    return [Jogo(id=row["id"], nome=row["nome"], capa_url=row["capa_url"]) for row in rows]


@app.get("/api/prices/{id_jogo}", response_model=PrecosResponse)
def get_prices(id_jogo: int):
    """
    Retorna as ofertas atuais (tabela comparativa) e o histórico de preços
    (gráfico) para um jogo específico.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, capa_url FROM jogos WHERE id = ?", (id_jogo,))
    jogo_row = cursor.fetchone()

    if not jogo_row:
        conn.close()
        # Mock temporário enquanto não há dados reais no banco
        jogo_mock = Jogo(id=id_jogo, nome="[MOCK] Jogo não encontrado", capa_url=None)
        return PrecosResponse(jogo=jogo_mock, ofertas_atuais=[], historico=[])

    jogo = Jogo(id=jogo_row["id"], nome=jogo_row["nome"], capa_url=jogo_row["capa_url"])

    # Ofertas atuais: pega o preço mais recente de cada loja
    cursor.execute(
        """
        SELECT id, id_jogo, loja, preco, data_captura, url_compra
        FROM precos
        WHERE id_jogo = ?
        ORDER BY data_captura DESC
        """,
        (id_jogo,),
    )
    todas_linhas = cursor.fetchall()
    conn.close()

    ofertas_atuais = []
    lojas_vistas = set()
    historico: List[HistoricoPreco] = []

    for row in todas_linhas:
        historico.append(
            HistoricoPreco(
                data_captura=row["data_captura"],
                preco=row["preco"],
                loja=row["loja"],
            )
        )
        if row["loja"] not in lojas_vistas:
            lojas_vistas.add(row["loja"])
            ofertas_atuais.append(
                Oferta(
                    id=row["id"],
                    id_jogo=row["id_jogo"],
                    loja=row["loja"],
                    preco=row["preco"],
                    data_captura=row["data_captura"],
                    url_compra=row["url_compra"],
                )
            )

    return PrecosResponse(jogo=jogo, ofertas_atuais=ofertas_atuais, historico=historico)