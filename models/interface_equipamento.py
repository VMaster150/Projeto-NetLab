
from config import db


class InterfaceEquipamento(db.Model):
    __tablename__ = "interfaces_equipamento"

    id = db.Column(db.Integer, primary_key=True)

    equipamento_id = db.Column(
        db.Integer,
        db.ForeignKey("equipamentos.id"),
        nullable=False
    )

    interface_modelo_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces_modelo.id"),
        nullable=True
    )

    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    habilitada = db.Column(db.Boolean, nullable=False, default=True)

    equipamento = db.relationship("Equipamento")
    interface_modelo = db.relationship("InterfaceModelo")

    def __repr__(self):
        return f"<InterfaceEquipamento {self.nome}>"
