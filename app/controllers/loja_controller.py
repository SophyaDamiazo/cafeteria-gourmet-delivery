from flask import Blueprint, render_template, request

from ..models.produto import Categoria, Produto
from . import usuario_logado

bp = Blueprint("loja", __name__)


@bp.app_context_processor
def injetar_usuario():
    return {"usuario": usuario_logado()}


@bp.route("/")
def catalogo():
    categoria_id = request.args.get("categoria", type=int)
    busca = request.args.get("q", "").strip()
    return render_template(
        "loja/catalogo.html",
        produtos=Produto.listar(categoria_id=categoria_id, busca=busca),
        categorias=Categoria.listar(),
        categoria_atual=categoria_id,
        busca=busca,
    )
