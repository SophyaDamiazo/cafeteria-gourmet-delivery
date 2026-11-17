from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..models import ErroValidacao
from ..models.carrinho import Carrinho
from ..models.pedido import Pedido
from ..models.usuario import Usuario
from . import login_obrigatorio, usuario_logado

bp = Blueprint("carrinho", __name__)


@bp.route("/carrinho")
def ver():
    c = Carrinho()
    itens = c.itens()
    subtotal = c.subtotal()
    taxa = current_app.config["TAXA_ENTREGA"] if itens else 0
    return render_template("carrinho/carrinho.html", itens=itens, subtotal=subtotal, taxa=taxa, total=subtotal + taxa)


@bp.route("/carrinho/adicionar/<int:produto_id>", methods=["POST"])
def adicionar(produto_id):
    try:
        produto = Carrinho().adicionar(produto_id, request.form.get("quantidade", 1, type=int) or 1)
        flash(f"{produto['nome']} adicionado ao carrinho.", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(request.referrer or url_for("loja.catalogo"))


@bp.route("/carrinho/atualizar/<int:produto_id>", methods=["POST"])
def atualizar(produto_id):
    try:
        Carrinho().atualizar(produto_id, request.form.get("quantidade", 0, type=int))
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("carrinho.ver"))


@bp.route("/carrinho/remover/<int:produto_id>", methods=["POST"])
def remover(produto_id):
    Carrinho().remover(produto_id)
    flash("Item removido do carrinho.", "sucesso")
    return redirect(url_for("carrinho.ver"))


@bp.route("/checkout", methods=["GET", "POST"])
@login_obrigatorio
def checkout():
    c = Carrinho()
    itens = c.itens()
    if not itens:
        flash("Seu carrinho está vazio.", "aviso")
        return redirect(url_for("loja.catalogo"))
    taxa = current_app.config["TAXA_ENTREGA"]
    subtotal = c.subtotal()
    usuario = usuario_logado()

    if request.method == "POST":
        f = request.form
        try:
            pedido_id = Pedido.criar(
                usuario["id"], itens, f.get("endereco"), f.get("forma_pagamento"), f,
                observacao=f.get("observacao", ""), taxa_entrega=taxa,
            )
            if f.get("salvar_endereco"):
                Usuario.atualizar_endereco(usuario["id"], f.get("endereco"))
        except ErroValidacao as e:
            flash(str(e), "erro")
            return render_template("carrinho/checkout.html", itens=itens, subtotal=subtotal, taxa=taxa,
                                   total=subtotal + taxa, form=f), 400
        c.limpar()
        flash("Pedido realizado com sucesso! Acompanhe o status abaixo.", "sucesso")
        return redirect(url_for("pedidos.detalhe", pedido_id=pedido_id))

    return render_template("carrinho/checkout.html", itens=itens, subtotal=subtotal, taxa=taxa,
                           total=subtotal + taxa, form={"endereco": usuario["endereco"]})
