# -*- coding: utf-8 -*-
"""
database.py — Inicialização e helpers do banco SQLite.

Gerencia a conexão com o banco de dados e criação da tabela 'campanhas'.
"""

import sqlite3
import os

# Caminho do banco de dados (mesmo diretório do projeto)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def get_db():
    """
    Abre e retorna uma conexão com o banco SQLite.
    Configura Row factory para acesso por nome de coluna.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome: row['coluna']
    conn.execute("PRAGMA journal_mode=WAL")  # Melhor performance de escrita
    return conn


def close_db(conn):
    """Fecha a conexão com o banco."""
    if conn:
        conn.close()


def init_db():
    """
    Cria a tabela 'campanhas' se não existir e executa migrações necessárias.
    Chamada uma vez na inicialização do app.
    """
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS campanhas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_campanha TEXT,
            nome_campanha TEXT NOT NULL,
            publico_alvo TEXT NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE NOT NULL,
            valor_gasto REAL NOT NULL,
            visualizacoes INTEGER NOT NULL,
            conversas_iniciadas INTEGER NOT NULL,
            link_anuncio TEXT,
            observacoes TEXT
        )
    ''')
    conn.commit()

    # Migração: adiciona coluna codigo_campanha se não existir (banco legado)
    colunas = [row[1] for row in conn.execute("PRAGMA table_info(campanhas)").fetchall()]
    if 'codigo_campanha' not in colunas:
        conn.execute("ALTER TABLE campanhas ADD COLUMN codigo_campanha TEXT")
        conn.commit()
        print("[DB] Migração: coluna 'codigo_campanha' adicionada.")

    # Migração: adiciona coluna link_anuncio se não existir (banco legado)
    if 'link_anuncio' not in colunas:
        conn.execute("ALTER TABLE campanhas ADD COLUMN link_anuncio TEXT")
        conn.commit()
        print("[DB] Migração: coluna 'link_anuncio' adicionada.")

    # Migração: remove coluna entregas de campanhas (não é mais usada)
    if 'entregas' in colunas:
        try:
            conn.execute("ALTER TABLE campanhas DROP COLUMN entregas")
            conn.commit()
            print("[DB] Migração: coluna 'entregas' removida de campanhas.")
        except Exception as e:
            print(f"[DB] Aviso: não foi possível remover coluna 'entregas': {e}")

    # Migração: normaliza públicos antigos (Fagundes/Ararica, Ararica e região -> Araricá +6km)
    conn.execute('''
        UPDATE campanhas SET publico_alvo = REPLACE(
            REPLACE(
                REPLACE(publico_alvo, 'Fagundes/Ararica', 'Araricá +6km'),
                'Ararica e região', 'Araricá +6km'
            ),
            'Araricá e região', 'Araricá +6km'
        )
    ''')
    conn.commit()
    print("[DB] Migração: públicos-alvo normalizados.")

    # Cria tabela de entregas diárias (independente de campanhas)
    conn.execute('''\
        CREATE TABLE IF NOT EXISTS entregas_diarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL UNIQUE,
            quantidade INTEGER NOT NULL DEFAULT 0,
            observacoes TEXT
        )
    ''')
    conn.commit()

    close_db(conn)
    print(f"[DB] Banco inicializado em: {DATABASE_PATH}")


if __name__ == '__main__':
    init_db()
    print("[DB] Tabela 'campanhas' criada/verificada com sucesso.")
