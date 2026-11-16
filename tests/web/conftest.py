"""Starts the PHP website (php -S) on a free port against a fresh test database."""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests

from tests.conftest import drop_database, make_database

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "Demo@123"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def site(db_server, tmp_path_factory):
    if not shutil.which("php"):
        pytest.skip("php is not installed")
    name = make_database(db_server)
    env_file = tmp_path_factory.mktemp("env") / ".env"
    env_file.write_text(
        f"DB_HOST={db_server.db_host}\nDB_PORT={db_server.db_port}\nDB_NAME={name}\n"
        f"DB_USER={db_server.db_user}\nDB_PASSWORD={db_server.db_password}\nAPP_TIMEZONE=Asia/Kolkata\nAPP_DEBUG=0\n"
    )
    port = free_port()
    env = {k: v for k, v in os.environ.items() if not k.startswith("DB_")}
    env["APP_ENV_FILE"] = str(env_file)
    proc = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}", "-t", "web", "web/router.php"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}/"
    for _ in range(50):
        try:
            requests.get(base + "login.php", timeout=1)
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    yield {"base": base, "db": name, "env_file": env_file, "settings": db_server}
    proc.terminate()
    proc.wait(5)
    drop_database(db_server, name)


def csrf_of(html: str) -> str:
    m = re.search(r'name="csrf" value="([0-9a-f]+)"', html) or re.search(r'data-csrf="([0-9a-f]+)"', html)
    assert m, "no CSRF token on the page"
    return m.group(1)


class Client(requests.Session):
    def __init__(self, base):
        super().__init__()
        self.base = base

    def page(self, path, **kw):
        kw.setdefault("allow_redirects", False)
        return self.get(self.base + path, **kw)

    def post_form(self, path, data, token_from=None, **kw):
        kw.setdefault("allow_redirects", False)
        if token_from is not None:
            data = {**data, "csrf": csrf_of(self.get(self.base + token_from).text)}
        return self.post(self.base + path, data=data, **kw)

    def login(self, email, role, password=PASSWORD):
        r = self.post_form("login.php", {"email": email, "password": password, "role": role}, token_from="login.php")
        return r


@pytest.fixture
def client(site):
    return Client(site["base"])


@pytest.fixture
def student(site):
    c = Client(site["base"])
    assert c.login("aarav.sharma@example.com", "student").status_code == 302
    return c


@pytest.fixture
def faculty(site):
    c = Client(site["base"])
    assert c.login("priya.deshmukh@example.com", "faculty").status_code == 302
    return c
