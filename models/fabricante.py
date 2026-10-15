from config import db


class Fabricante(db.Model):
    __tablename__ = 'fabricantes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

    modelos = db.relationship("ModeloEquipamento", back_populates="fabricante")

    def __repr__(self):
        return f"<Fabricante {self.nome}>"