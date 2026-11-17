from ..db import get_db
from . import ErroValidacao


class Categoria:
    @staticmethod
    def listar():
        return get_db().execute("SELECT * FROM categoria ORDER BY id").fetchall()


class Produto:
    """Item do cardapio."""

    BASE_SQL = (
        "SELECT p.*, c.nome AS categoria_nome, c.icone AS icone "
        "FROM produto p JOIN categoria c ON c.id = p.categoria_id "
    )

    @classmethod
    def listar(cls, categoria_id=None, busca=None, apenas_ativos=True):
        sql, params, filtros = cls.BASE_SQL, [], []
        if apenas_ativos:
            filtros.append("p.ativo = 1")
        if categoria_id:
            filtros.append("p.categoria_id = ?")
            params.append(categoria_id)
        if busca:
            filtros.append("(p.nome LIKE ? OR p.descricao LIKE ?)")
            params += [f"%{busca}%", f"%{busca}%"]
        if filtros:
            sql += "WHERE " + " AND ".join(filtros)
        sql += " ORDER BY p.categoria_id, p.nome"
        return get_db().execute(sql, params).fetchall()

    @classmethod
    def buscar_por_id(cls, produto_id):
        return get_db().execute(cls.BASE_SQL + "WHERE p.id = ?", (produto_id,)).fetchone()

    @staticmethod
    def _validar(nome, preco, categoria_id):
        if len((nome or "").strip()) < 2:
            raise ErroValidacao("Informe o nome do produto.")
        try:
            preco = round(float(str(preco).replace(",", ".")), 2)
        except (TypeError, ValueError):
            raise ErroValidacao("Preço inválido.")
        if preco <= 0:
            raise ErroValidacao("O preço deve ser maior que zero.")
        if not get_db().execute("SELECT 1 FROM categoria WHERE id = ?", (categoria_id,)).fetchone():
            raise ErroValidacao("Categoria inválida.")
        return preco

    @classmethod
    def criar(cls, nome, descricao, preco, categoria_id):
        preco = cls._validar(nome, preco, categoria_id)
        db = get_db()
        cur = db.execute(
            "INSERT INTO produto (categoria_id, nome, descricao, preco) VALUES (?, ?, ?, ?)",
            (categoria_id, nome.strip(), (descricao or "").strip(), preco),
        )
        db.commit()
        return cur.lastrowid

    @classmethod
    def atualizar(cls, produto_id, nome, descricao, preco, categoria_id):
        preco = cls._validar(nome, preco, categoria_id)
        db = get_db()
        db.execute(
            "UPDATE produto SET categoria_id = ?, nome = ?, descricao = ?, preco = ? WHERE id = ?",
            (categoria_id, nome.strip(), (descricao or "").strip(), preco, produto_id),
        )
        db.commit()

    @staticmethod
    def alternar_ativo(produto_id):
        db = get_db()
        db.execute("UPDATE produto SET ativo = 1 - ativo WHERE id = ?", (produto_id,))
        db.commit()
