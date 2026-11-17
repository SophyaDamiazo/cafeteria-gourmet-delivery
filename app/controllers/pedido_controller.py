from flask import Blueprint, abort, flash, jsonify, redirect, render_template, url_for

from ..models import ErroValidacao
from ..models.pedido import STATUS_FLUXO, Pagamento, Pedido
from . import login_obrigatorio, usuario_logado

bp = Blueprint("pedidos", __name__)


def _pedido_do_usuario(pedido_id):
    pedido = Pedido.buscar(pedido_id)
    u = usuario_logado()
    if not pedido or (pedido["usuario_id"] != u["id"] and u["perfil"] != "admin"):
        abort(404)
    return pedido


@bp.route("/pedidos")
@login_obrigatorio
def meus_pedidos():
    return render_template("pedidos/lista.html", pedidos=Pedido.listar_por_usuario(usuario_logado()["id"]))


@bp.route("/pedidos/<int:pedido_id>")
@login_obrigatorio
def detalhe(pedido_id):
    pedido = _pedido_do_usuario(pedido_id)
    return render_template(
        "pedidos/detalhe.html", pedido=pedido, itens=Pedido.itens(pedido_id),
        pagamento=Pagamento.do_pedido(pedido_id), fluxo=STATUS_FLUXO,
    )


@bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@login_obrigatorio
def cancelar(pedido_id):
    try:
        Pedido.cancelar(pedido_id, usuario_id=usuario_logado()["id"])
        flash("Pedido cancelado. Se o pagamento já tinha sido aprovado, ele será estornado.", "sucesso")
    except ErroValidacao as e:
        flash(str(e), "erro")
    return redirect(url_for("pedidos.detalhe", pedido_id=pedido_id))


@bp.route("/api/pedidos/<int:pedido_id>/status")
@login_obrigatorio
def status_json(pedido_id):
    """Usado pelo JavaScript da pagina de acompanhamento para atualizar o status sem recarregar."""
    pedido = _pedido_do_usuario(pedido_id)
    return jsonify(id=pedido["id"], status=pedido["status"], atualizado_em=pedido["atualizado_em"])
