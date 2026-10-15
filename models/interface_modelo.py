
from config import db


class InterfaceModelo(db.Model):
    __tablename__ = "interfaces_modelo"

    id = db.Column(db.Integer,primary_key=True)
    modelo_id = db.Column(db.Integer,db.ForeignKey("modelos_equipamento.id"),nullable=False)
    nome = db.Column(db.String(100),nullable=False)
    tipo = db.Column(db.String(100),nullable=False)
    habilitada = db.Column(db.Boolean,nullable=False,default=True)
    gerenciamento = db.Column(db.Boolean,nullable=False,default=False)
    modelo = db.relationship("ModeloEquipamento",back_populates="interfaces")

    def __repr__(self):
        return f"<InterfaceModelo {self.nome}>"
