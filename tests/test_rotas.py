"""Testes de integracao: fluxo completo pelas rotas (Controller + View)."""
from conftest import login


def test_catalogo_publico(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Cappuccino" in r.get_data(as_text=True)


def test_busca_sem_resultado(client):
    r = client.get("/?q=pizza")
    assert "Nenhum produto encontrado" in r.get_data(as_text=True)


def test_cadastro_e_login(client):
    r = client.post("/cadastro", data={
        "nome": "Ana Teste", "email": "ana@teste.com", "telefone": "(11) 97777-6666",
        "endereco": "Rua das Flores, 10 - Jardim", "senha": "abcdef", "confirmar_senha": "abcdef",
    }, follow_redirects=True)
    assert "Cadastro realizado" in r.get_data(as_text=True)
    client.get("/logout")
    r = login(client, "ana@teste.com", "abcdef")
    assert r.status_code == 302


def test_cadastro_senhas_diferentes(client):
    r = client.post("/cadastro", data={
        "nome": "Ana Teste", "email": "ana@teste.com", "telefone": "11977776666",
        "endereco": "Rua das Flores, 10", "senha": "abcdef", "confirmar_senha": "xxxxxx",
    })
    assert r.status_code == 400
    assert "não conferem" in r.get_data(as_text=True)


def test_login_invalido(client):
    r = login(client, "cliente@teste.com", "errada")
    assert r.status_code == 401
    assert "incorretos" in r.get_data(as_text=True)


def test_checkout_exige_login(client):
    client.post("/carrinho/adicionar/1", data={"quantidade": 1})
    r = client.get("/checkout")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_carrinho_preservado_apos_login(client):
    client.post("/carrinho/adicionar/2", data={"quantidade": 3})
    login(client)
    r = client.get("/carrinho")
    assert "Cappuccino" in r.get_data(as_text=True)


def test_fluxo_compra_completo(cliente_logado, admin_logado):
    c = cliente_logado
    c.post("/carrinho/adicionar/2", data={"quantidade": 2})   # 2x Cappuccino 12,90
    c.post("/carrinho/adicionar/9", data={"quantidade": 1})   # 1x Croissant 9,90
    r = c.get("/carrinho")
    assert "R$ 40,70" in r.get_data(as_text=True)  # 25,80 + 9,90 + 5,00 taxa

    r = c.post("/checkout", data={"endereco": "Av. Paulista, 1000", "forma_pagamento": "PIX"})
    assert r.status_code == 302
    pedido_url = r.headers["Location"]
    pagina = c.get(pedido_url).get_data(as_text=True)
    assert "Recebido" in pagina and "PIX-" in pagina

    pedido_id = pedido_url.rstrip("/").split("/")[-1]
    assert c.get(f"/api/pedidos/{pedido_id}/status").get_json()["status"] == "Recebido"

    admin_logado.post(f"/admin/pedidos/{pedido_id}/avancar")
    assert c.get(f"/api/pedidos/{pedido_id}/status").get_json()["status"] == "Em preparo"

    # carrinho foi esvaziado
    assert "carrinho está vazio" in c.get("/carrinho").get_data(as_text=True)


def test_checkout_cartao_invalido(cliente_logado):
    c = cliente_logado
    c.post("/carrinho/adicionar/1")
    r = c.post("/checkout", data={"endereco": "Av. Paulista, 1000", "forma_pagamento": "Cartao",
                                  "cartao_numero": "1234 5678 9012 3456", "cartao_validade": "12/30", "cartao_cvv": "123"})
    assert r.status_code == 400
    assert "cartão inválido" in r.get_data(as_text=True)


def test_preco_vem_do_banco_nao_do_formulario(cliente_logado):
    c = cliente_logado
    c.post("/carrinho/adicionar/1", data={"quantidade": 1, "preco": "0.01"})
    r = c.get("/carrinho").get_data(as_text=True)
    assert "R$ 7,50" in r


def test_cliente_nao_ve_pedido_de_outro(app, cliente_logado):
    c = cliente_logado
    c.post("/carrinho/adicionar/1")
    pedido_url = c.post("/checkout", data={"endereco": "Av. Paulista, 1000", "forma_pagamento": "PIX"}).headers["Location"]
    outro = app.test_client()
    outro.post("/cadastro", data={"nome": "Intruso Silva", "email": "intruso@x.com", "telefone": "11966665555",
                                  "endereco": "Rua Z, 99 - Centro", "senha": "123456", "confirmar_senha": "123456"})
    assert outro.get(pedido_url).status_code == 404


def test_area_admin_bloqueada_para_cliente(cliente_logado):
    r = cliente_logado.get("/admin/pedidos")
    assert r.status_code == 302


def test_admin_cadastra_produto(admin_logado, client):
    r = admin_logado.post("/admin/produtos/novo", data={"nome": "Chai Latte", "descricao": "Chá com especiarias",
                                                        "preco": "13,50", "categoria_id": "1"})
    assert r.status_code == 302
    assert "Chai Latte" in client.get("/").get_data(as_text=True)


def test_login_nao_redireciona_para_site_externo(client):
    r = client.post("/login?next=https://site-malicioso.com", data={"email": "cliente@teste.com", "senha": "123456"})
    assert r.headers["Location"] == "/"
