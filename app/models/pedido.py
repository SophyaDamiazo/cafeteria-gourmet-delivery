import re
import secrets
from datetime import datetime

from ..db import get_db
from . import ErroValidacao

STATUS_FLUXO = ["Recebido", "Em preparo", "Saiu para entrega", "Entregue"]
CANCELADO = "Cancelado"
FORMAS_PAGAMENTO = ["PIX", "Cartao", "Dinheiro"]


def _agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def cartao_valido(numero):
    """Validacao do numero do cartao pelo algoritmo de Luhn."""
    digitos = re.sub(r"\D", "", numero or "")
    if not 13 <= len(digitos) <= 19:
        return False
    soma = 0
    for i, d in enumerate(reversed(digitos)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        soma += n
    return soma % 10 == 0


class Pagamento:
    """Pagamento simulado (nao ha integracao real com operadora)."""

    @staticmethod
    def processar(forma, valor, dados):
        """Valida os dados e devolve os campos a gravar. Nunca guarda o numero completo do cartao."""
        if forma not in FORMAS_PAGAMENTO:
            raise ErroValidacao("Escolha uma forma de pagamento.")
        reg = {"forma": forma, "valor": valor, "status": "Pendente", "codigo_transacao": None,
               "cartao_final": None, "troco_para": None, "data_pagamento": None}
        if forma == "PIX":
            reg.update(status="Aprovado", codigo_transacao="PIX-" + secrets.token_hex(6).upper(),
                       data_pagamento=_agora())
        elif forma == "Cartao":
            numero = re.sub(r"\D", "", dados.get("cartao_numero", ""))
            if not cartao_valido(numero):
                raise ErroValidacao("Número de cartão inválido.")
            if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", dados.get("cartao_validade", "").strip()):
                raise ErroValidacao("Validade do cartão deve estar no formato MM/AA.")
            if not re.fullmatch(r"\d{3,4}", dados.get("cartao_cvv", "").strip()):
                raise ErroValidacao("CVV inválido.")
            reg.update(status="Aprovado", codigo_transacao="CARD-" + secrets.token_hex(6).upper(),
                       cartao_final=numero[-4:], data_pagamento=_agora())
        else:  # Dinheiro: pago na entrega
            troco = (dados.get("troco_para") or "").strip().replace(",", ".")
            if troco:
                try:
                    troco = float(troco)
                except ValueError:
                    raise ErroValidacao("Valor de troco inválido.")
                if troco < valor:
                    raise ErroValidacao("O valor para troco deve ser maior ou igual ao total do pedido.")
                reg["troco_para"] = troco
        return reg

    @staticmethod
    def do_pedido(pedido_id):
        return get_db().execute("SELECT * FROM pagamento WHERE pedido_id = ?", (pedido_id,)).fetchone()


class Pedido:
    @staticmethod
    def criar(usuario_id, itens, endereco, forma_pagamento, dados_pagamento, observacao="", taxa_entrega=0.0):
        """Cria pedido + itens + pagamento numa unica transacao."""
        if not itens:
            raise ErroValidacao("Seu carrinho está vazio.")
        if len((endereco or "").strip()) < 8:
            raise ErroValidacao("Informe o endereço completo para entrega.")
        subtotal = round(sum(i["produto"]["preco"] * i["quantidade"] for i in itens), 2)
        total = round(subtotal + taxa_entrega, 2)
        pagamento = Pagamento.processar(forma_pagamento, total, dados_pagamento or {})

        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO pedido (usuario_id, endereco_entrega, observacao, taxa_entrega, valor_total, "
                "data_pedido, atualizado_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (usuario_id, endereco.strip(), (observacao or "").strip()[:255], taxa_entrega, total, _agora(), _agora()),
            )
            pedido_id = cur.lastrowid
            db.executemany(
                "INSERT INTO item_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, i["produto"]["id"], i["quantidade"], i["produto"]["preco"]) for i in itens],
            )
            db.execute(
                "INSERT INTO pagamento (pedido_id, forma, status, valor, codigo_transacao, cartao_final, "
                "troco_para, data_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (pedido_id, pagamento["forma"], pagamento["status"], pagamento["valor"], pagamento["codigo_transacao"],
                 pagamento["cartao_final"], pagamento["troco_para"], pagamento["data_pagamento"]),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        return pedido_id

    @staticmethod
    def buscar(pedido_id):
        return get_db().execute(
            "SELECT p.*, u.nome AS cliente_nome, u.telefone AS cliente_telefone "
            "FROM pedido p JOIN usuario u ON u.id = p.usuario_id WHERE p.id = ?",
            (pedido_id,),
        ).fetchone()

    @staticmethod
    def itens(pedido_id):
        return get_db().execute(
            "SELECT i.*, pr.nome AS produto_nome, (i.quantidade * i.preco_unitario) AS subtotal "
            "FROM item_pedido i JOIN produto pr ON pr.id = i.produto_id WHERE i.pedido_id = ?",
            (pedido_id,),
        ).fetchall()

    @staticmethod
    def listar_por_usuario(usuario_id):
        return get_db().execute(
            "SELECT * FROM pedido WHERE usuario_id = ? ORDER BY id DESC", (usuario_id,)
        ).fetchall()

    @staticmethod
    def listar_todos(status=None):
        sql = ("SELECT p.*, u.nome AS cliente_nome, pg.forma AS forma_pagamento, pg.status AS status_pagamento "
               "FROM pedido p JOIN usuario u ON u.id = p.usuario_id "
               "LEFT JOIN pagamento pg ON pg.pedido_id = p.id ")
        params = []
        if status:
            sql += "WHERE p.status = ? "
            params.append(status)
        return get_db().execute(sql + "ORDER BY p.id DESC", params).fetchall()

    @staticmethod
    def proximo_status(status_atual):
        if status_atual in STATUS_FLUXO[:-1]:
            return STATUS_FLUXO[STATUS_FLUXO.index(status_atual) + 1]
        return None

    @classmethod
    def avancar_status(cls, pedido_id):
        pedido = cls.buscar(pedido_id)
        if not pedido:
            raise ErroValidacao("Pedido não encontrado.")
        novo = cls.proximo_status(pedido["status"])
        if not novo:
            raise ErroValidacao(f"O pedido está '{pedido['status']}' e não pode avançar.")
        db = get_db()
        db.execute("UPDATE pedido SET status = ?, atualizado_em = ? WHERE id = ?", (novo, _agora(), pedido_id))
        if novo == "Entregue":  # pagamento em dinheiro e confirmado na entrega
            db.execute(
                "UPDATE pagamento SET status = 'Aprovado', data_pagamento = ? WHERE pedido_id = ? AND status = 'Pendente'",
                (_agora(), pedido_id),
            )
        db.commit()
        return novo

    @classmethod
    def cancelar(cls, pedido_id, usuario_id=None):
        """Cliente so cancela o proprio pedido enquanto 'Recebido'; admin cancela ate sair para entrega."""
        pedido = cls.buscar(pedido_id)
        if not pedido or (usuario_id is not None and pedido["usuario_id"] != usuario_id):
            raise ErroValidacao("Pedido não encontrado.")
        permitidos = ["Recebido"] if usuario_id is not None else ["Recebido", "Em preparo"]
        if pedido["status"] not in permitidos:
            raise ErroValidacao(f"Não é possível cancelar um pedido com status '{pedido['status']}'.")
        db = get_db()
        db.execute("UPDATE pedido SET status = ?, atualizado_em = ? WHERE id = ?", (CANCELADO, _agora(), pedido_id))
        db.execute("UPDATE pagamento SET status = 'Estornado' WHERE pedido_id = ? AND status = 'Aprovado'", (pedido_id,))
        db.commit()
