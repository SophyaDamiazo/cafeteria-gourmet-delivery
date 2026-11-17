from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import ErroValidacao
from ..models.usuario import Usuario

bp = Blueprint("auth", __name__)


def _destino_seguro(proximo):
    # evita redirecionamento para sites externos
    return proximo if proximo and proximo.startswith("/") and not proximo.startswith("//") else url_for("loja.catalogo")


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        f = request.form
        try:
            if f.get("senha") != f.get("confirmar_senha"):
                raise ErroValidacao("As senhas não conferem.")
            uid = Usuario.criar(f.get("nome"), f.get("email"), f.get("senha"), f.get("telefone"), f.get("endereco"))
        except ErroValidacao as e:
            flash(str(e), "erro")
            return render_template("auth/cadastro.html", form=f), 400
        session.clear()
        session["usuario_id"] = uid
        flash("Cadastro realizado! Bem-vindo(a) à Cafeteria Gourmet.", "sucesso")
        return redirect(url_for("loja.catalogo"))
    return render_template("auth/cadastro.html", form={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = Usuario.autenticar(request.form.get("email"), request.form.get("senha"))
        if u is None:
            flash("E-mail ou senha incorretos.", "erro")
            return render_template("auth/login.html", email=request.form.get("email", "")), 401
        carrinho = session.get("carrinho", {})  # preserva o carrinho montado antes do login
        session.clear()
        session["usuario_id"] = u["id"]
        session["carrinho"] = carrinho
        flash(f"Olá, {u['nome'].split()[0]}!", "sucesso")
        if u["perfil"] == "admin":
            return redirect(url_for("admin.pedidos"))
        return redirect(_destino_seguro(request.args.get("next")))
    return render_template("auth/login.html", email="")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("loja.catalogo"))
