from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..models import ErroValidacao
from ..models.pedido import CANCELADO, STATUS_FLUXO, Pedido
from ..models.produto import Categoria, Produto
from . import admin_obrigatorio

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/pedidos")
@admin_obrigatorio
def pedidos():
    status = request.args.get("status") or None
    return render_template(
        "admin/pedidos.html", pedidos=Pedido.listar_todos(status), status_atual=status,
        todos_status=STATUS_FLUXO + [CANCELADO], proximo=Pedido.proximo_status,
    )


@bp.route("/pedidos/<int:pedido_id>/avancar", methods=["POST"])
@admin_obrigatorio
def avancar(pedido_id):
    try:
        novo = Pedido.avancar_status(pedido_id)
        flash(f"Pedido #{pedido_id} agora está '{novo}'.", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(request.referrer or url_for("admin.pedidos"))


@bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@admin_obrigatorio
def cancelar(pedido_id):
    try:
        Pedido.cancelar(pedido_id)
        flash(f"Pedido #{pedido_id} cancelado.", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(request.referrer or url_for("admin.pedidos"))


@bp.route("/produtos")
@admin_obrigatorio
def produtos():
    return render_template("admin/produtos.html", produtos=Produto.listar(apenas_ativos=False))


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_obrigatorio
def novo_produto():
    if request.method == "POST":
        f = request.form
        try:
            Produto.criar(f.get("nome"), f.get("descricao"), f.get("preco"), f.get("categoria_id", type=int))
            flash("Produto cadastrado.", "sucesso")
            return redirect(url_for("admin.produtos"))
        except ErroValidacao as e:
            flash(str(e), "erro")
            return render_template("admin/produto_form.html", produto=f, categorias=Categoria.listar(), novo=True), 400
    return render_template("admin/produto_form.html", produto={}, categorias=Categoria.listar(), novo=True)


@bp.route("/produtos/<int:produto_id>/editar", methods=["GET", "POST"])
@admin_obrigatorio
def editar_produto(produto_id):
    produto = Produto.buscar_por_id(produto_id)
    if not produto:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            Produto.atualizar(produto_id, f.get("nome"), f.get("descricao"), f.get("preco"), f.get("categoria_id", type=int))
            flash("Produto atualizado.", "sucesso")
            return redirect(url_for("admin.produtos"))
        except ErroValidacao as e:
            flash(str(e), "erro")
            return render_template("admin/produto_form.html", produto=f, categorias=Categoria.listar(), novo=False), 400
    return render_template("admin/produto_form.html", produto=produto, categorias=Categoria.listar(), novo=False)


@bp.route("/produtos/<int:produto_id>/ativar", methods=["POST"])
@admin_obrigatorio
def alternar_produto(produto_id):
    Produto.alternar_ativo(produto_id)
    flash("Disponibilidade do produto atualizada.", "sucesso")
    return redirect(url_for("admin.produtos"))
