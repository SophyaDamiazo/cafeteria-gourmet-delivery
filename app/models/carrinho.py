from flask import session

from . import ErroValidacao
from .produto import Produto

QTD_MAXIMA = 50


class Carrinho:
    """Carrinho de compras guardado na sessao do usuario: {produto_id: quantidade}."""

    def __init__(self):
        self._itens = session.get("carrinho", {})

    def _salvar(self):
        session["carrinho"] = self._itens
        session.modified = True

    def adicionar(self, produto_id, quantidade=1):
        produto = Produto.buscar_por_id(produto_id)
        if not produto or not produto["ativo"]:
            raise ErroValidacao("Produto indisponível.")
        chave = str(produto_id)
        nova = self._itens.get(chave, 0) + int(quantidade)
        if nova > QTD_MAXIMA:
            raise ErroValidacao(f"Quantidade máxima por item é {QTD_MAXIMA}.")
        self._itens[chave] = nova
        self._salvar()
        return produto

    def atualizar(self, produto_id, quantidade):
        quantidade = int(quantidade)
        chave = str(produto_id)
        if quantidade <= 0:
            self._itens.pop(chave, None)
        elif quantidade > QTD_MAXIMA:
            raise ErroValidacao(f"Quantidade máxima por item é {QTD_MAXIMA}.")
        else:
            self._itens[chave] = quantidade
        self._salvar()

    def remover(self, produto_id):
        self._itens.pop(str(produto_id), None)
        self._salvar()

    def limpar(self):
        self._itens = {}
        self._salvar()

    def quantidade_total(self):
        return sum(self._itens.values())

    def itens(self):
        """Lista de itens com dados atuais do banco (preco nunca vem do navegador)."""
        resultado = []
        for chave, qtd in list(self._itens.items()):
            produto = Produto.buscar_por_id(int(chave))
            if not produto or not produto["ativo"]:
                self._itens.pop(chave)  # produto saiu do cardapio
                self._salvar()
                continue
            resultado.append({"produto": produto, "quantidade": qtd, "subtotal": round(produto["preco"] * qtd, 2)})
        return resultado

    def subtotal(self):
        return round(sum(i["subtotal"] for i in self.itens()), 2)

    def vazio(self):
        return not self._itens
