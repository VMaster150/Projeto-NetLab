from flask import *



from config import db

bp_sistema = Blueprint("sistema", __name__)

@bp_sistema.route("/")
def index():
    return render_template("index.html")


@bp_sistema.route("/teste-banco")
def teste_banco():
    try:
        db.session.execute(db.text("SELECT 1"))
        return "Conexao com PostgreSQL realizada com sucesso!"
    except Exception as erro:
        db.session.rollback()
        current_app.logger.exception("Erro ao testar conexão com PostgreSQL")
        return f"Erro ao conectar com o banco: {erro}", 500