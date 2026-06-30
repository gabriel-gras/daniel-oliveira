import sqlite3
from pathlib import Path
from datetime import date

# Caminho do arquivo SQLite (na raiz do projeto)
DB_PATH = Path(__file__).resolve().parent.parent / "dados.db"


def get_connection() -> sqlite3.Connection:
    """
    Cria e retorna uma conexão com o banco SQLite.
    row_factory configurado para retornar dicionários (sqlite3.Row),
    facilitando o uso direto nos endpoints/modelos.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inserir_ou_obter_jogo(conn, nome: str, capa_url: str | None = None) -> int:
    """
    Insere um jogo (se não existir) e retorna o id.

    Resiliência: se o jogo já existir mas ainda não tiver capa_url salva
    (registros antigos, ou execuções anteriores em que o scraper não achou
    a imagem), e agora recebermos uma capa válida, atualizamos o registro
    em vez de descartar a informação nova.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, capa_url FROM jogos WHERE nome = ?", (nome,))
    row = cursor.fetchone()

    if row:
        id_jogo = row["id"]
        if capa_url and not row["capa_url"]:
            cursor.execute(
                "UPDATE jogos SET capa_url = ? WHERE id = ?",
                (capa_url, id_jogo),
            )
            conn.commit()
        return id_jogo

    cursor.execute(
        "INSERT INTO jogos (nome, capa_url) VALUES (?, ?)",
        (nome, capa_url),
    )
    conn.commit()
    return cursor.lastrowid


def inserir_preco(conn, id_jogo: int, loja: str, preco: float, url_compra: str | None = None) -> int:
    """Insere um novo registro de preço (histórico) para o jogo/loja."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO precos (id_jogo, loja, preco, data_captura, url_compra)
        VALUES (?, ?, ?, ?, ?)
        """,
        (id_jogo, loja, preco, date.today().isoformat(), url_compra),
    )
    conn.commit()
    return cursor.lastrowid


def init_db() -> None:
    """
    Inicializa o banco de dados, criando as tabelas 'jogos' e 'precos'
    caso ainda não existam (conforme Spec 02).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            capa_url TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_jogo INTEGER NOT NULL,
            loja TEXT NOT NULL,
            preco REAL NOT NULL,
            data_captura TEXT NOT NULL,
            url_compra TEXT,
            FOREIGN KEY (id_jogo) REFERENCES jogos (id)
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em: {DB_PATH}")


if __name__ == "__main__":
    init_db()