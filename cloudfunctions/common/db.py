from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional

import pymysql
from pymysql.cursors import DictCursor

from .config import settings


def get_connection():
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=6,
    )


@contextmanager
def cursor_ctx():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(cursor, query: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    cursor.execute(query, params or ())
    return cursor.fetchone()


def fetch_all(cursor, query: str, params: Optional[Iterable[Any]] = None):
    cursor.execute(query, params or ())
    return cursor.fetchall()


def execute(cursor, query: str, params: Optional[Iterable[Any]] = None) -> int:
    return cursor.execute(query, params or ())

