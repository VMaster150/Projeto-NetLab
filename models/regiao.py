from config import db

class Regiao(db.Model):
    __tablename__ ="regioes"


    id = db.Column(db.Integer, primary_key=True)


    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(1000), nullable=True)
    regiao_pai_id = db.Column(db.Integer, db.ForeignKey('regiao.id'), nullable=False)
    subregioes = db.relationship("Regiao", backref=db.backref("regiao_pai", remote_side=[id]))

    def __repr__(self):
        return f"<Regiao {self.nome}>"