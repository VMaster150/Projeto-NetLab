from flask import *

from config import db

bp_login = Blueprint("login", __name__)


USUARIO_PADRAO = "admin"
SENHA_PADRAO = "netlab"

def exigir_login():
    if request.endpoint in ("login.login", "login.logout", "static"):
        return None

    if not session.get("usuario"):
        return redirect(url_for("login.login", next=request.path))


@bp_login.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario"):
        return redirect(url_for("sistema.index"))

    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")

        if usuario == USUARIO_PADRAO and senha == SENHA_PADRAO:
            session["usuario"] = usuario

            destino = (
                request.form.get("next")
                or request.args.get("next")
                or url_for("sistema.index")
            )

            if not destino.startswith("/") or destino.startswith("//"):
                destino = url_for("sistema.index")

            return redirect(destino)

        erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)


@bp_login.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login.login"))