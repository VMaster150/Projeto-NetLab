
from config import db


class Regiao(db.Model):
    __tablename__ = "regioes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    descricao = db.Column(
        db.String(1000),
        nullable=True
    )

    regiao_pai_id = db.Column(
        db.Integer,
        db.ForeignKey("regioes.id"),
        nullable=True
    )

    regiao_pai = db.relationship(
        "Regiao",
        remote_side=[id],
        back_populates="subregioes"
    )

    subregioes = db.relationship(
        "Regiao",
        back_populates="regiao_pai"
    )

    def __repr__(self):
        return f"<Regiao {self.nome}>"
