"""Testes unitarios das regras de negocio (camada Model)."""
import pytest

from app.models import ErroValidacao
from app.models.pedido import Pagamento, Pedido, cartao_valido
from app.models.produto import Produto
from app.models.usuario import Usuario


def test_cadastro_usuario_valido(app):
    with app.app_context():
        uid = Usuario.criar("Maria Silva", "Maria@Email.com", "segredo1", "(11) 98888-7777", "Rua A, 123 - Centro")
        u = Usuario.buscar_por_id(uid)
        assert u["email"] == "maria@email.com"  # e-mail normalizado
        assert u["senha_hash"] != "segredo1"    # senha nunca em texto puro
        assert u["perfil"] == "cliente"


def test_cadastro_email_duplicado(app):
    with app.app_context():
        with pytest.raises(ErroValidacao, match="já está cadastrado"):
            Usuario.criar("Outro Cliente", "cliente@teste.com", "123456", "11999999999", "Rua B, 456 - Centro")


@pytest.mark.parametrize("campo,valor,msg", [
    ("nome", "A", "nome"),
    ("email", "email-invalido", "e-mail"),
    ("senha", "123", "senha"),
    ("telefone", "123", "telefone"),
    ("endereco", "Rua", "endereço"),
])
def test_cadastro_campos_invalidos(app, campo, valor, msg):
    dados = {"nome": "Joao Souza", "email": "joao@x.com", "senha": "123456",
             "telefone": "11999998888", "endereco": "Rua C, 789 - Centro"}
    dados[campo] = valor
    with app.app_context():
        with pytest.raises(ErroValidacao, match=msg):
            Usuario.criar(**dados)


def test_autenticacao(app):
    with app.app_context():
        assert Usuario.autenticar("cliente@teste.com", "123456") is not None
        assert Usuario.autenticar("cliente@teste.com", "errada") is None
        assert Usuario.autenticar("naoexiste@x.com", "123456") is None


def test_catalogo_filtros(app):
    with app.app_context():
        assert len(Produto.listar()) == 10
        assert all(p["categoria_id"] == 1 for p in Produto.listar(categoria_id=1))
        assert [p["nome"] for p in Produto.listar(busca="brownie")] == ["Brownie"]


def test_produto_inativo_nao_aparece(app):
    with app.app_context():
        Produto.alternar_ativo(1)
        assert 1 not in [p["id"] for p in Produto.listar()]
        assert 1 in [p["id"] for p in Produto.listar(apenas_ativos=False)]


def test_produto_preco_invalido(app):
    with app.app_context():
        with pytest.raises(ErroValidacao):
            Produto.criar("Chá", "", "-5", 1)
        with pytest.raises(ErroValidacao):
            Produto.criar("Chá", "", "abc", 1)
        pid = Produto.criar("Chá Verde", "Chá gelado", "8,50", 2)
        assert Produto.buscar_por_id(pid)["preco"] == 8.5


def test_luhn():
    assert cartao_valido("4111 1111 1111 1111")
    assert not cartao_valido("4111 1111 1111 1112")
    assert not cartao_valido("123")


def test_pagamento_cartao_guarda_so_final():
    reg = Pagamento.processar("Cartao", 20.0, {"cartao_numero": "4111111111111111",
                                               "cartao_validade": "12/30", "cartao_cvv": "123"})
    assert reg["status"] == "Aprovado" and reg["cartao_final"] == "1111"
    assert "4111111111111111" not in str(reg)


def test_pagamento_dinheiro_troco_menor_que_total():
    with pytest.raises(ErroValidacao, match="troco"):
        Pagamento.processar("Dinheiro", 50.0, {"troco_para": "20"})


def _itens(app, *pares):
    return [{"produto": Produto.buscar_por_id(pid), "quantidade": q} for pid, q in pares]


def test_criar_pedido_calcula_total(app):
    with app.app_context():
        itens = _itens(app, (1, 2), (7, 1))  # 2x Espresso 7,50 + 1x Brownie 11,00
        pid = Pedido.criar(2, itens, "Av. Paulista, 1000", "PIX", {}, taxa_entrega=5.0)
        p = Pedido.buscar(pid)
        assert p["valor_total"] == 31.0
        assert p["status"] == "Recebido"
        assert len(Pedido.itens(pid)) == 2
        assert Pagamento.do_pedido(pid)["status"] == "Aprovado"


def test_pedido_vazio_nao_e_criado(app):
    with app.app_context():
        with pytest.raises(ErroValidacao, match="vazio"):
            Pedido.criar(2, [], "Av. Paulista, 1000", "PIX", {})


def test_fluxo_de_status_e_pagamento_na_entrega(app):
    with app.app_context():
        pid = Pedido.criar(2, _itens(app, (2, 1)), "Av. Paulista, 1000", "Dinheiro", {"troco_para": "50"})
        assert Pagamento.do_pedido(pid)["status"] == "Pendente"
        assert Pedido.avancar_status(pid) == "Em preparo"
        assert Pedido.avancar_status(pid) == "Saiu para entrega"
        assert Pedido.avancar_status(pid) == "Entregue"
        assert Pagamento.do_pedido(pid)["status"] == "Aprovado"
        with pytest.raises(ErroValidacao):
            Pedido.avancar_status(pid)


def test_cliente_so_cancela_pedido_recebido(app):
    with app.app_context():
        pid = Pedido.criar(2, _itens(app, (1, 1)), "Av. Paulista, 1000", "PIX", {})
        Pedido.avancar_status(pid)  # Em preparo
        with pytest.raises(ErroValidacao, match="Não é possível cancelar"):
            Pedido.cancelar(pid, usuario_id=2)
        Pedido.cancelar(pid)  # admin ainda pode
        assert Pedido.buscar(pid)["status"] == "Cancelado"
        assert Pagamento.do_pedido(pid)["status"] == "Estornado"


def test_cliente_nao_cancela_pedido_de_outro(app):
    with app.app_context():
        pid = Pedido.criar(2, _itens(app, (1, 1)), "Av. Paulista, 1000", "PIX", {})
        with pytest.raises(ErroValidacao, match="não encontrado"):
            Pedido.cancelar(pid, usuario_id=999)
