"""
Conexao e operacoes com o banco de dados SQLite do KAIRUS.
"""

import sqlite3
import json
import os
from pathlib import Path


# Caminho do banco de dados
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "kairus.db"


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexao com o banco de dados."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas se nao existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'Nova conversa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT DEFAULT 'unknown',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_info (
            conversation_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (conversation_id, key),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USERS
# =========================

def create_user(username: str, password_hash: str) -> int | None:
    """Cria um novo usuario. Retorna o ID ou None se ja existir."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Retorna um usuario pelo username."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    """Retorna um usuario pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


# =========================
# CONVERSATIONS
# =========================

def create_conversation(conv_id: str, user_id: int = 1, title: str = "Nova conversa") -> dict:
    """Cria uma nova conversa no banco."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
        (conv_id, user_id, title)
    )

    conn.commit()
    conn.close()

    return {"id": conv_id, "title": title, "user_id": user_id}


def get_conversation(conv_id: str) -> dict | None:
    """Retorna uma conversa pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def list_conversations(user_id: int, limit: int = 20) -> list:
    """Lista conversas recentes de um usuario."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
        (user_id, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_conversation_title(conv_id: str, title: str):
    """Atualiza o titulo da conversa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, conv_id)
    )

    conn.commit()
    conn.close()


def update_message_count(conv_id: str, count: int):
    """Atualiza a contagem de mensagens."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE conversations SET message_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (count, conv_id)
    )

    conn.commit()
    conn.close()


def delete_conversation(conv_id: str):
    """Deleta uma conversa e suas mensagens."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    cursor.execute("DELETE FROM user_info WHERE conversation_id = ?", (conv_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))

    conn.commit()
    conn.close()


# =========================
# MESSAGES
# =========================

def save_message(conv_id: str, role: str, content: str, intent: str = "unknown"):
    """Salva uma mensagem no banco."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content, intent) VALUES (?, ?, ?, ?)",
        (conv_id, role, content, intent)
    )

    conn.commit()
    conn.close()


def get_messages(conv_id: str, limit: int = 50) -> list:
    """Retorna as mensagens de uma conversa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC LIMIT ?",
        (conv_id, limit)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_message_count(conv_id: str) -> int:
    """Retorna a quantidade de mensagens de uma conversa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
        (conv_id,)
    )

    count = cursor.fetchone()[0]
    conn.close()

    return count


# =========================
# USER INFO
# =========================

def save_user_info(conv_id: str, key: str, value: str):
    """Salva uma informacao do usuario."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO user_info (conversation_id, key, value) VALUES (?, ?, ?)",
        (conv_id, key, value)
    )

    conn.commit()
    conn.close()


def get_user_info(conv_id: str) -> dict:
    """Retorna todas as informacoes do usuario de uma conversa."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT key, value FROM user_info WHERE conversation_id = ?",
        (conv_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return {row["key"]: row["value"] for row in rows}