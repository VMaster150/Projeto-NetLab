
from config import db


class Conexao(db.Model):
    __tablename__ = "conexoes"

    id = db.Column(db.Integer, primary_key=True)

    interface_origem_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces_equipamento.id"),
        nullable=False,
        unique=True
    )

    interface_destino_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces_equipamento.id"),
        nullable=False,
        unique=True
    )

    tipo_cabo = db.Column(
        db.String(50),
        nullable=False,
        default="Ethernet"
    )

    descricao = db.Column(
        db.String(250),
        nullable=True
    )

    interface_origem = db.relationship(
        "InterfaceEquipamento",
        foreign_keys=[interface_origem_id]
    )

    interface_destino = db.relationship(
        "InterfaceEquipamento",
        foreign_keys=[interface_destino_id]
    )

    def __repr__(self):
        return f"<Conexao {self.id}>"
