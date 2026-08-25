"""
Conexao e operacoes com o banco de dados do KAIRUS.
SQLite local (desenvolvimento) ou PostgreSQL (producao no Render).
"""

import sqlite3
import os
import dj_database_url
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


# Caminho do banco de dados local
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "kairus.db"


# Detecta ambiente: PostgreSQL (producao) ou SQLite (local)
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)


def get_connection():
    """Retorna uma conexao com o banco (Postgres ou SQLite)."""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def _execute(conn, query, params=(), fetchone=False, fetchall=False, commit=True):
    """Executa uma query abstraindo Postgres vs SQLite."""
    cursor = conn.cursor(cursor_factory=RealDictCursor if USE_POSTGRES else None)
    cursor.execute(query, params)
    if commit:
        conn.commit()
    if fetchone:
        row = cursor.fetchone()
        if USE_POSTGRES and row:
            return dict(row)
        elif row:
            return dict(row)
        return None
    if fetchall:
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    return cursor.lastrowid


def init_db():
    """Cria as tabelas se nao existirem."""
    conn = get_connection()

    # PostgreSQL usa NOW(), SQLite usa CURRENT_TIMESTAMP
    timestamp = "NOW()" if USE_POSTGRES else "CURRENT_TIMESTAMP"
    id_type = "SERIAL" if USE_POSTGRES else "INTEGER"
    text_type = "TEXT"
    fk = "" if USE_POSTGRES else ""

    queries = []

    queries.append(f"""
        CREATE TABLE {"IF NOT EXISTS " if not USE_POSTGRES else ""}users (
            id {id_type} PRIMARY KEY,
            username {text_type} UNIQUE NOT NULL,
            password_hash {text_type} NOT NULL,
            created_at TIMESTAMP DEFAULT {timestamp}
        )
    """)

    queries.append(f"""
        CREATE TABLE {"IF NOT EXISTS " if not USE_POSTGRES else ""}conversations (
            id {text_type} PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title {text_type} DEFAULT 'Nova conversa',
            created_at TIMESTAMP DEFAULT {timestamp},
            updated_at TIMESTAMP DEFAULT {timestamp},
            message_count INTEGER DEFAULT 0
        )
    """)

    queries.append(f"""
        CREATE TABLE {"IF NOT EXISTS " if not USE_POSTGRES else ""}messages (
            id {id_type} PRIMARY KEY,
            conversation_id {text_type} NOT NULL,
            role {text_type} NOT NULL,
            content {text_type} NOT NULL,
            intent {text_type} DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT {timestamp}
        )
    """)

    queries.append(f"""
        CREATE TABLE {"IF NOT EXISTS " if not USE_POSTGRES else ""}user_info (
            conversation_id {text_type} NOT NULL,
            key {text_type} NOT NULL,
            value {text_type} NOT NULL,
            PRIMARY KEY (conversation_id, key)
        )
    """)

    for query in queries:
        conn.cursor().execute(query)
        conn.commit()

    conn.close()


# =========================
# USERS
# =========================

def create_user(username: str, password_hash: str) -> int | None:
    """Cria um novo usuario. Retorna o ID ou None se ja existir."""
    conn = get_connection()

    try:
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, password_hash)
            )
            conn.commit()
            return cursor.fetchone()[0]
        else:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Retorna um usuario pelo username."""
    conn = get_connection()
    if USE_POSTGRES:
        row = _execute(conn, "SELECT * FROM users WHERE username = %s", (username,), fetchone=True)
    else:
        row = _execute(conn, "SELECT * FROM users WHERE username = ?", (username,), fetchone=True)
    conn.close()
    return row


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    if USE_POSTGRES:
        row = _execute(conn, "SELECT * FROM users WHERE id = %s", (user_id,), fetchone=True)
    else:
        row = _execute(conn, "SELECT * FROM users WHERE id = ?", (user_id,), fetchone=True)
    conn.close()
    return row


# =========================
# CONVERSATIONS
# =========================

def create_conversation(conv_id: str, user_id: int = 1, title: str = "Nova conversa") -> dict:
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn,
            "INSERT INTO conversations (id, user_id, title) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (conv_id, user_id, title))
    else:
        _execute(conn,
            "INSERT OR IGNORE INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conv_id, user_id, title))
    conn.close()
    return {"id": conv_id, "title": title, "user_id": user_id}


def get_conversation(conv_id: str) -> dict | None:
    conn = get_connection()
    if USE_POSTGRES:
        row = _execute(conn, "SELECT * FROM conversations WHERE id = %s", (conv_id,), fetchone=True)
    else:
        row = _execute(conn, "SELECT * FROM conversations WHERE id = ?", (conv_id,), fetchone=True)
    conn.close()
    return row


def list_conversations(user_id: int, limit: int = 20) -> list:
    conn = get_connection()
    if USE_POSTGRES:
        rows = _execute(conn,
            "SELECT * FROM conversations WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s",
            (user_id, limit), fetchall=True)
    else:
        rows = _execute(conn,
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit), fetchall=True)
    conn.close()
    return rows


def update_conversation_title(conv_id: str, title: str):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn, "UPDATE conversations SET title = %s, updated_at = NOW() WHERE id = %s", (title, conv_id))
    else:
        _execute(conn, "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title, conv_id))
    conn.close()


def update_message_count(conv_id: str, count: int):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn, "UPDATE conversations SET message_count = %s, updated_at = NOW() WHERE id = %s", (count, conv_id))
    else:
        _execute(conn, "UPDATE conversations SET message_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (count, conv_id))
    conn.close()


def delete_conversation(conv_id: str):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn, "DELETE FROM messages WHERE conversation_id = %s", (conv_id,))
        _execute(conn, "DELETE FROM user_info WHERE conversation_id = %s", (conv_id,))
        _execute(conn, "DELETE FROM conversations WHERE id = %s", (conv_id,))
    else:
        _execute(conn, "DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        _execute(conn, "DELETE FROM user_info WHERE conversation_id = ?", (conv_id,))
        _execute(conn, "DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.close()


# =========================
# MESSAGES
# =========================

def save_message(conv_id: str, role: str, content: str, intent: str = "unknown"):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn,
            "INSERT INTO messages (conversation_id, role, content, intent) VALUES (%s, %s, %s, %s)",
            (conv_id, role, content, intent))
    else:
        _execute(conn,
            "INSERT INTO messages (conversation_id, role, content, intent) VALUES (?, ?, ?, ?)",
            (conv_id, role, content, intent))
    conn.close()


def get_messages(conv_id: str, limit: int = 50) -> list:
    conn = get_connection()
    if USE_POSTGRES:
        rows = _execute(conn,
            "SELECT * FROM messages WHERE conversation_id = %s ORDER BY id ASC LIMIT %s",
            (conv_id, limit), fetchall=True)
    else:
        rows = _execute(conn,
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC LIMIT ?",
            (conv_id, limit), fetchall=True)
    conn.close()
    return rows


def get_message_count(conv_id: str) -> int:
    conn = get_connection()
    if USE_POSTGRES:
        row = _execute(conn, "SELECT COUNT(*) FROM messages WHERE conversation_id = %s", (conv_id,), fetchone=True)
    else:
        row = _execute(conn, "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conv_id,), fetchone=True)
    conn.close()
    return row["COUNT(*)"] if row else 0


# =========================
# USER INFO
# =========================

def save_user_info(conv_id: str, key: str, value: str):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn,
            """INSERT INTO user_info (conversation_id, key, value) VALUES (%s, %s, %s)
               ON CONFLICT (conversation_id, key) DO UPDATE SET value = EXCLUDED.value""",
            (conv_id, key, value))
    else:
        _execute(conn,
            "INSERT OR REPLACE INTO user_info (conversation_id, key, value) VALUES (?, ?, ?)",
            (conv_id, key, value))
    conn.close()


def get_user_info(conv_id: str) -> dict:
    conn = get_connection()
    if USE_POSTGRES:
        rows = _execute(conn,
            "SELECT key, value FROM user_info WHERE conversation_id = %s",
            (conv_id,), fetchall=True)
    else:
        rows = _execute(conn,
            "SELECT key, value FROM user_info WHERE conversation_id = ?",
            (conv_id,), fetchall=True)
    conn.close()
    return {row["key"]: row["value"] for row in rows}