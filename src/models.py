from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class Jogo(BaseModel):
    """Representa os dados básicos de um jogo (tabela 'jogos')."""
    id: int
    nome: str
    capa_url: Optional[str] = None


class Oferta(BaseModel):
    """Representa uma oferta/preço de uma loja para um jogo (tabela 'precos')."""
    id: int
    id_jogo: int
    loja: str
    preco: float
    data_captura: date
    url_compra: Optional[str] = None


class HistoricoPreco(BaseModel):
    """Ponto de dado usado para montar o gráfico de histórico de preços."""
    data_captura: date
    preco: float
    loja: str


class PrecosResponse(BaseModel):
    """
    Resposta do endpoint GET /api/prices/{id_jogo}.
    Combina as ofertas atuais (para a tabela comparativa)
    e o histórico (para o gráfico).
    """
    jogo: Jogo
    ofertas_atuais: List[Oferta]
    historico: List[HistoricoPreco]