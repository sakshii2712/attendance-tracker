import os
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH = os.environ.get("DATABASE_PATH", "attendance.db")


def get_db_connection():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def is_postgres():
    return DATABASE_URL is not None


def init_db():
    if is_postgres():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                total_classes INTEGER NOT NULL DEFAULT 0,
                attended_classes INTEGER NOT NULL DEFAULT 0,
                percentage REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    else:
        import sqlite3
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                total_classes INTEGER NOT NULL DEFAULT 0,
                attended_classes INTEGER NOT NULL DEFAULT 0,
                percentage REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()