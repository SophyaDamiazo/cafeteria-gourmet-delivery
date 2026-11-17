import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "teste.sqlite"), "SECRET_KEY": "teste"})


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email="cliente@teste.com", senha="123456"):
    return client.post("/login", data={"email": email, "senha": senha})


@pytest.fixture
def cliente_logado(client):
    login(client)
    return client


@pytest.fixture
def admin_logado(app):
    c = app.test_client()
    login(c, "admin@cafeteria.com", "admin123")
    return c
