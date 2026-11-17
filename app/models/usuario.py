import re
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db
from . import ErroValidacao

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Usuario:
    """Cliente ou administrador da cafeteria."""

    @staticmethod
    def validar(nome, email, senha, telefone, endereco):
        erros = []
        if len((nome or "").strip()) < 3:
            erros.append("Informe o nome completo (mínimo 3 letras).")
        if not EMAIL_RE.match((email or "").strip()):
            erros.append("Informe um e-mail válido.")
        if len(senha or "") < 6:
            erros.append("A senha deve ter pelo menos 6 caracteres.")
        if len(re.sub(r"\D", "", telefone or "")) < 10:
            erros.append("Informe um telefone com DDD.")
        if len((endereco or "").strip()) < 8:
            erros.append("Informe o endereço completo para entrega.")
        if erros:
            raise ErroValidacao(" ".join(erros))

    @classmethod
    def criar(cls, nome, email, senha, telefone, endereco, perfil="cliente"):
        cls.validar(nome, email, senha, telefone, endereco)
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO usuario (nome, email, senha_hash, telefone, endereco, perfil) VALUES (?, ?, ?, ?, ?, ?)",
                (nome.strip(), email.strip().lower(), generate_password_hash(senha),
                 telefone.strip(), endereco.strip(), perfil),
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise ErroValidacao("Este e-mail já está cadastrado. Faça login ou use outro e-mail.")
        return cur.lastrowid

    @staticmethod
    def buscar_por_id(usuario_id):
        return get_db().execute("SELECT * FROM usuario WHERE id = ?", (usuario_id,)).fetchone()

    @staticmethod
    def autenticar(email, senha):
        u = get_db().execute("SELECT * FROM usuario WHERE email = ?", ((email or "").strip().lower(),)).fetchone()
        if u and check_password_hash(u["senha_hash"], senha or ""):
            return u
        return None

    @staticmethod
    def atualizar_endereco(usuario_id, endereco):
        if len((endereco or "").strip()) < 8:
            raise ErroValidacao("Informe o endereço completo para entrega.")
        db = get_db()
        db.execute("UPDATE usuario SET endereco = ? WHERE id = ?", (endereco.strip(), usuario_id))
        db.commit()
