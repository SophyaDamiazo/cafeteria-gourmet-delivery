-- Versao SQLite do mesmo projeto fisico (usada para rodar a aplicacao sem instalar servidor).
-- Estrutura equivalente a schema_mysql.sql.
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS pagamento;
DROP TABLE IF EXISTS item_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS categoria;
DROP TABLE IF EXISTS usuario;

CREATE TABLE usuario (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    telefone    TEXT NOT NULL,
    endereco    TEXT NOT NULL,
    perfil      TEXT NOT NULL DEFAULT 'cliente' CHECK (perfil IN ('cliente','admin')),
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE categoria (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nome   TEXT NOT NULL UNIQUE,
    icone  TEXT NOT NULL DEFAULT '☕'
);

CREATE TABLE produto (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id),
    nome          TEXT NOT NULL,
    descricao     TEXT NOT NULL DEFAULT '',
    preco         REAL NOT NULL CHECK (preco > 0),
    ativo         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE pedido (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id        INTEGER NOT NULL REFERENCES usuario(id),
    data_pedido       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    status            TEXT NOT NULL DEFAULT 'Recebido'
                      CHECK (status IN ('Recebido','Em preparo','Saiu para entrega','Entregue','Cancelado')),
    endereco_entrega  TEXT NOT NULL,
    observacao        TEXT NOT NULL DEFAULT '',
    taxa_entrega      REAL NOT NULL DEFAULT 0,
    valor_total       REAL NOT NULL CHECK (valor_total >= 0),
    atualizado_em     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX ix_pedido_usuario ON pedido(usuario_id);
CREATE INDEX ix_pedido_status  ON pedido(status);

CREATE TABLE item_pedido (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    produto_id      INTEGER NOT NULL REFERENCES produto(id),
    quantidade      INTEGER NOT NULL CHECK (quantidade BETWEEN 1 AND 50),
    preco_unitario  REAL NOT NULL
);

CREATE TABLE pagamento (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id         INTEGER NOT NULL UNIQUE REFERENCES pedido(id) ON DELETE CASCADE,
    forma             TEXT NOT NULL CHECK (forma IN ('PIX','Cartao','Dinheiro')),
    status            TEXT NOT NULL DEFAULT 'Pendente' CHECK (status IN ('Pendente','Aprovado','Estornado')),
    valor             REAL NOT NULL,
    codigo_transacao  TEXT,
    cartao_final      TEXT,
    troco_para        REAL,
    data_pagamento    TEXT
);

INSERT INTO categoria (nome, icone) VALUES
  ('Cafes', '☕'), ('Bebidas geladas', '🥤'), ('Doces', '🍰'), ('Salgados', '🥐');

INSERT INTO produto (categoria_id, nome, descricao, preco) VALUES
  (1, 'Espresso', 'Café especial 100% arábica, extração curta e encorpada.', 7.50),
  (1, 'Cappuccino', 'Espresso, leite vaporizado e espuma cremosa com canela.', 12.90),
  (1, 'Latte de Baunilha', 'Espresso com leite vaporizado e xarope de baunilha.', 14.50),
  (1, 'Mocha', 'Espresso, chocolate belga e leite vaporizado.', 15.90),
  (2, 'Cold Brew', 'Café extraído a frio por 18 horas, servido com gelo.', 13.90),
  (2, 'Frappé de Caramelo', 'Café batido com gelo, leite e calda de caramelo.', 18.90),
  (3, 'Brownie', 'Brownie de chocolate meio amargo com nozes.', 11.00),
  (3, 'Cheesecake de Frutas Vermelhas', 'Fatia de cheesecake com calda artesanal.', 16.50),
  (4, 'Croissant', 'Croissant amanteigado folhado.', 9.90),
  (4, 'Pão de Queijo (6 un.)', 'Pão de queijo mineiro quentinho.', 10.50);
