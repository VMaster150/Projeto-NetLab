from flask import *
from config import db

from rotas.conexoes import bp_conexoes

from rotas.regioes import bp_regioes
from rotas.equipamentos import bp_equipamentos
from rotas.fabricantes import bp_fabricantes
from rotas.modelos import bp_modelos


app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave-temporaria-netlab'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:4548@localhost:5432/netlab'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(bp_regioes)
app.register_blueprint(bp_equipamentos)
app.register_blueprint(bp_fabricantes)
app.register_blueprint(bp_modelos)
app.register_blueprint(bp_conexoes)


# =========================================
# LOGIN SIMPLES
# =========================================

USUARIO_PADRAO = "admin"
SENHA_PADRAO = "netlab"


@app.before_request
def exigir_login():
    # Libera a própria tela de login e os arquivos estáticos.
    if request.endpoint in ("login", "static"):
        return None

    if not session.get("usuario"):
        return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario"):
        return redirect(url_for("index"))

    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if usuario == USUARIO_PADRAO and senha == SENHA_PADRAO:
            session["usuario"] = usuario

            destino = (
                request.form.get("next")
                or request.args.get("next")
                or url_for("index")
            )

            # Evita redirecionar para fora do próprio site.
            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("index")

            return redirect(destino)

        erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/teste-banco")
def teste_banco():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Conexao com PostgreSQL realizada com sucesso!"
    except Exception as erro:
        db.session.rollback()
        app.logger.exception("Erro ao testar conexão com PostgreSQL")
        return f"Erro ao conectar com o banco: {erro}", 500

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
