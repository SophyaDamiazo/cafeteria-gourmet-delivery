-- =====================================================================
-- Cafeteria Gourmet Delivery - Projeto Fisico do Banco de Dados (MySQL 8)
-- PIT-II Sistemas de Informacao - Sophya Damiazo (RGM 40917932)
-- =====================================================================
-- Mapeamento classe -> tabela:
--   Usuario -> usuario | Categoria -> categoria | Produto -> produto
--   Pedido -> pedido   | ItemPedido -> item_pedido | Pagamento -> pagamento
-- Associacoes 1:N viram chaves estrangeiras; a composicao Pedido<>ItemPedido
-- usa ON DELETE CASCADE (o item nao existe sem o pedido).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS cafeteria_delivery
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cafeteria_delivery;

CREATE TABLE usuario (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nome         VARCHAR(100)  NOT NULL,
    email        VARCHAR(120)  NOT NULL,
    senha_hash   VARCHAR(255)  NOT NULL,
    telefone     VARCHAR(20)   NOT NULL,
    endereco     VARCHAR(255)  NOT NULL,
    perfil       ENUM('cliente','admin') NOT NULL DEFAULT 'cliente',
    criado_em    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuario_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE categoria (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    nome   VARCHAR(60) NOT NULL,
    icone  VARCHAR(10) NOT NULL DEFAULT '☕',
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE=InnoDB;

CREATE TABLE produto (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id  INT           NOT NULL,
    nome          VARCHAR(100)  NOT NULL,
    descricao     VARCHAR(500)  NOT NULL DEFAULT '',
    preco         DECIMAL(10,2) NOT NULL,
    ativo         TINYINT(1)    NOT NULL DEFAULT 1,
    CONSTRAINT fk_produto_categoria FOREIGN KEY (categoria_id) REFERENCES categoria(id),
    CONSTRAINT ck_produto_preco CHECK (preco > 0)
) ENGINE=InnoDB;

CREATE TABLE pedido (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id        INT           NOT NULL,
    data_pedido       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status            ENUM('Recebido','Em preparo','Saiu para entrega','Entregue','Cancelado')
                      NOT NULL DEFAULT 'Recebido',
    endereco_entrega  VARCHAR(255)  NOT NULL,
    observacao        VARCHAR(255)  NOT NULL DEFAULT '',
    taxa_entrega      DECIMAL(10,2) NOT NULL DEFAULT 0,
    valor_total       DECIMAL(10,2) NOT NULL,
    atualizado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_pedido_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    CONSTRAINT ck_pedido_total CHECK (valor_total >= 0)
) ENGINE=InnoDB;

CREATE INDEX ix_pedido_usuario ON pedido(usuario_id);
CREATE INDEX ix_pedido_status  ON pedido(status);

CREATE TABLE item_pedido (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id       INT           NOT NULL,
    produto_id      INT           NOT NULL,
    quantidade      INT           NOT NULL,
    preco_unitario  DECIMAL(10,2) NOT NULL,   -- preco "congelado" no momento da compra
    CONSTRAINT fk_item_pedido  FOREIGN KEY (pedido_id)  REFERENCES pedido(id) ON DELETE CASCADE,
    CONSTRAINT fk_item_produto FOREIGN KEY (produto_id) REFERENCES produto(id),
    CONSTRAINT ck_item_qtd CHECK (quantidade BETWEEN 1 AND 50)
) ENGINE=InnoDB;

CREATE TABLE pagamento (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id          INT           NOT NULL,
    forma              ENUM('PIX','Cartao','Dinheiro') NOT NULL,
    status             ENUM('Pendente','Aprovado','Estornado') NOT NULL DEFAULT 'Pendente',
    valor              DECIMAL(10,2) NOT NULL,
    codigo_transacao   VARCHAR(60)   NULL,
    cartao_final       CHAR(4)       NULL,   -- nunca armazenamos o numero completo do cartao
    troco_para         DECIMAL(10,2) NULL,
    data_pagamento     DATETIME      NULL,
    CONSTRAINT uq_pagamento_pedido UNIQUE (pedido_id),          -- relacao 1:1 com pedido
    CONSTRAINT fk_pagamento_pedido FOREIGN KEY (pedido_id) REFERENCES pedido(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Dados iniciais (cardapio)
INSERT INTO categoria (nome, icone) VALUES
  ('Cafes', '☕'), ('Bebidas geladas', '🥤'), ('Doces', '🍰'), ('Salgados', '🥐');

INSERT INTO produto (categoria_id, nome, descricao, preco) VALUES
  (1, 'Espresso', 'Cafe especial 100% arabica, extracao curta e encorpada.', 7.50),
  (1, 'Cappuccino', 'Espresso, leite vaporizado e espuma cremosa com canela.', 12.90),
  (1, 'Latte de Baunilha', 'Espresso com leite vaporizado e xarope de baunilha.', 14.50),
  (1, 'Mocha', 'Espresso, chocolate belga e leite vaporizado.', 15.90),
  (2, 'Cold Brew', 'Cafe extraido a frio por 18 horas, servido com gelo.', 13.90),
  (2, 'Frappe de Caramelo', 'Cafe batido com gelo, leite e calda de caramelo.', 18.90),
  (3, 'Brownie', 'Brownie de chocolate meio amargo com nozes.', 11.00),
  (3, 'Cheesecake de Frutas Vermelhas', 'Fatia de cheesecake com calda artesanal.', 16.50),
  (4, 'Croissant', 'Croissant amanteigado folhado.', 9.90),
  (4, 'Pao de Queijo (6 un.)', 'Pao de queijo mineiro quentinho.', 10.50);
-- Os usuarios iniciais (admin e cliente de teste) sao criados pela aplicacao,
-- pois a senha precisa ser gravada com hash (werkzeug/pbkdf2).
