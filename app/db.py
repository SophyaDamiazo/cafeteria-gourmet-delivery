"""Conexao com o banco de dados (SQLite) e criacao inicial das tabelas."""
import os
import sqlite3

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "schema_sqlite.sql")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    with open(SCHEMA, encoding="utf-8") as f:
        conn.executescript(f.read())
    # usuarios iniciais (senha com hash)
    conn.executemany(
        "INSERT INTO usuario (nome, email, senha_hash, telefone, endereco, perfil) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Administrador", "admin@cafeteria.com", generate_password_hash("admin123"),
             "(11) 90000-0000", "Rua da Cafeteria, 100 - Centro", "admin"),
            ("Cliente Teste", "cliente@teste.com", generate_password_hash("123456"),
             "(11) 91111-1111", "Av. Paulista, 1000 - Bela Vista", "cliente"),
        ],
    )
    conn.commit()


@click.command("init-db")
def init_db_command():
    """Apaga e recria o banco com os dados iniciais."""
    init_db()
    click.echo("Banco de dados criado.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    # cria o banco automaticamente na primeira execucao
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db()
