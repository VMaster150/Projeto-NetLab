from flask import *
from config import db

from rotas.conexoes import bp_conexoes

from rotas.regioes import bp_regioes
from rotas.equipamentos import bp_equipamentos
from rotas.fabricantes import bp_fabricantes
from rotas.modelos import bp_modelos
from rotas.sistema import bp_sistema
from rotas.login import bp_login, exigir_login

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-temporaria-netlab'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:4548@localhost:5432/netlab')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

app.before_request(exigir_login)

app.register_blueprint(bp_regioes)
app.register_blueprint(bp_equipamentos)
app.register_blueprint(bp_fabricantes)
app.register_blueprint(bp_modelos)
app.register_blueprint(bp_conexoes)
app.register_blueprint(bp_sistema)
app.register_blueprint(bp_login)

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
