
from flask import Flask, render_template
from config import db
from models.regiao import Regiao

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:4548@localhost:5432/netlab'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route("/")
def index():
    return "NetLab funcionando!"


@app.route("/teste-banco")
def teste_banco():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Conexao com PostgreSQL realizada com sucesso!"
    except Exception as erro:
        return f"Erro ao conectar com o banco: {erro}", 500


@app.route("/regiao")
def regiao():
    return render_template("regiao.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
