
from config import db


class Equipamento(db.Model):
    __tablename__ = "equipamentos"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    tipo = db.Column(
        db.String(50),
        nullable=False
    )

    regiao_id = db.Column(
        db.Integer,
        db.ForeignKey("regioes.id"),
        nullable=False
    )

    fabricante_id = db.Column(
        db.Integer,
        db.ForeignKey("fabricantes.id"),
        nullable=True
    )

    modelo_id = db.Column(
        db.Integer,
        db.ForeignKey("modelos_equipamento.id"),
        nullable=True
    )

    regiao = db.relationship("Regiao")
    fabricante = db.relationship("Fabricante")
    modelo = db.relationship("ModeloEquipamento")

    def __repr__(self):
        return f"<Equipamento {self.nome}>"
