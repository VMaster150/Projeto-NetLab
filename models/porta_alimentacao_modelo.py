
from config import db


class PortaAlimentacaoModelo(db.Model):
    __tablename__ = "portas_alimentacao_modelo"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    modelo_id = db.Column(
        db.Integer,
        db.ForeignKey("modelos_equipamento.id"),
        nullable=False
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    tipo = db.Column(
        db.String(100),
        nullable=False
    )

    descricao = db.Column(
        db.String(500),
        nullable=True
    )

    modelo = db.relationship(
        "ModeloEquipamento",
        back_populates="portas_alimentacao"
    )

    def __repr__(self):
        return f"<PortaAlimentacaoModelo {self.nome}>"
