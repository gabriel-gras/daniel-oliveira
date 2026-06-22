import sqlite3
from pathlib import Path

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


def init_db() -> None:
    """
    Inicializa o banco de dados, criando as tabelas 'jogos' e 'precos'
    caso ainda não existam (conforme Spec 02).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela jogos: nome canônico + capa (thumbnail)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            capa_url TEXT
        )
        """
    )

    # Tabela precos: registros diários de cada oferta
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
    # Permite rodar `python src/database.py` para criar o banco manualmente
    init_db()