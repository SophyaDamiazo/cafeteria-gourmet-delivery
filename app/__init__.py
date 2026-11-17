"""Fabrica da aplicacao Flask - Cafeteria Gourmet Delivery (padrao MVC).

Model      -> app/models       (regras de negocio, validacao e acesso ao banco)
View       -> app/templates    (HTML/Jinja2) + app/static (CSS/JS)
Controller -> app/controllers  (rotas: recebem a requisicao e decidem o que fazer)
"""
import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao"),
        DATABASE=os.path.join(app.instance_path, "cafeteria.sqlite"),
        TAXA_ENTREGA=5.00,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .controllers import admin_controller, auth_controller, carrinho_controller, loja_controller, pedido_controller

    app.register_blueprint(loja_controller.bp)
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(carrinho_controller.bp)
    app.register_blueprint(pedido_controller.bp)
    app.register_blueprint(admin_controller.bp)

    @app.template_filter("moeda")
    def moeda(valor):
        return "R$ " + f"{float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.context_processor
    def injetar_carrinho():
        from .models.carrinho import Carrinho

        return {"qtd_carrinho": Carrinho().quantidade_total()}

    return app
