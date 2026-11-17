from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from ..models.usuario import Usuario


def usuario_logado():
    if "usuario" not in g:
        uid = session.get("usuario_id")
        g.usuario = Usuario.buscar_por_id(uid) if uid else None
    return g.usuario


def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if usuario_logado() is None:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def admin_obrigatorio(view):
    @wraps(view)
    @login_obrigatorio
    def wrapper(*args, **kwargs):
        if usuario_logado()["perfil"] != "admin":
            flash("Acesso restrito à equipe da cafeteria.", "erro")
            return redirect(url_for("loja.catalogo"))
        return view(*args, **kwargs)
    return wrapper
