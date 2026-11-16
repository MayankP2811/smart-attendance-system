"""Shared test fixtures.

Database tests need a MySQL or MariaDB server. They use the DB_* settings
from .env (or the environment) and create a throw-away database called
sa_test_<random>, which is dropped afterwards. If no server is reachable,
those tests are skipped and the rest still run.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from device.config import load_settings  # noqa: E402


def split_sql(text: str) -> list[str]:
    """Split a .sql file into statements (handles quotes and -- comments)."""
    out, buf, quote, i = [], [], None, 0
    while i < len(text):
        c = text[i]
        if quote:
            buf.append(c)
            if c == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 1
            elif c == quote:
                if i + 1 < len(text) and text[i + 1] == quote:  # '' inside a string
                    buf.append(text[i + 1])
                    i += 1
                else:
                    quote = None
        elif c in ("'", '"', "`"):
            quote = c
            buf.append(c)
        elif c == "-" and text[i:i + 2] == "--":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        elif c == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
        else:
            buf.append(c)
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    return out


def run_sql_file(conn, path: Path) -> None:
    cur = conn.cursor()
    for stmt in split_sql(path.read_text(encoding="utf-8")):
        cur.execute(stmt)
    conn.commit()
    cur.close()


def _server_connection(settings):
    import mysql.connector

    return mysql.connector.connect(host=settings.db_host, port=settings.db_port, user=settings.db_user,
                                   password=settings.db_password, charset="utf8mb4", connection_timeout=3)


@pytest.fixture(scope="session")
def db_server():
    settings = load_settings()
    try:
        conn = _server_connection(settings)
    except Exception as exc:  # no database server: skip DB tests
        pytest.skip(f"No MySQL/MariaDB server for tests ({exc})")
    conn.close()
    return settings


def make_database(settings, with_demo: bool = True) -> str:
    name = "sa_test_" + secrets.token_hex(4)
    conn = _server_connection(settings)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4")
    cur.execute(f"USE `{name}`")
    cur.close()
    run_sql_file(conn, ROOT / "database" / "schema.sql")
    if with_demo:
        run_sql_file(conn, ROOT / "database" / "demo_data.sql")
    conn.close()
    return name


def drop_database(settings, name: str) -> None:
    conn = _server_connection(settings)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS `{name}`")
    conn.commit()
    conn.close()


@pytest.fixture
def demo_db(db_server, monkeypatch):
    """A fresh database with the schema and demo data. Yields settings pointing at it."""
    name = make_database(db_server)
    monkeypatch.setenv("DB_NAME", name)
    settings = load_settings()
    yield settings
    drop_database(db_server, name)


@pytest.fixture
def empty_db(db_server, monkeypatch):
    name = make_database(db_server, with_demo=False)
    monkeypatch.setenv("DB_NAME", name)
    settings = load_settings()
    yield settings
    drop_database(db_server, name)


def pytest_configure(config):
    config.addinivalue_line("markers", "face: needs the real face_recognition library and FACE_TEST_DIR photos")
    os.environ.setdefault("SAVE_CAPTURES", "0")
