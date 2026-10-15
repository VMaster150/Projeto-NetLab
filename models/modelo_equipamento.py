from config import db


class ModeloEquipamento(db.Model):
    __tablename__ = "modelos_equipamento"

    id = db.Column(db.Integer, primary_key=True)
    fabricante_id = db.Column(db.Integer, db.ForeignKey('fabricantes.id'), nullable=False)
    modelo = db.Column(db.String(150), nullable=False, unique=True)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    altura_u = db.Column(db.Float, nullable=False, default=0.0)
    profundidade_completa = db.Column(db.Boolean,nullable=False,default=False)
    fluxo_ar = db.Column(db.String(50),nullable=True)
    peso = db.Column(db.Float,nullable=True)
    unidade_peso = db.Column(db.String(20),nullable=True)
    dados_originais = db.Column(db.JSON,nullable=True)
    fabricante = db.relationship("Fabricante",back_populates="modelos")
    interfaces = db.relationship("InterfaceModelo",back_populates="modelo",cascade="all, delete-orphan")

    portas_alimentacao = db.relationship(
        "PortaAlimentacaoModelo",
        back_populates="modelo",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<ModeloEquipamento {self.modelo}>"