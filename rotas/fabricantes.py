from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from config import db
from models.fabricante import Fabricante


bp_fabricantes = Blueprint("fabricantes", __name__)


@bp_fabricantes.route("/fabricantes", methods=["GET", "POST"])
def fabricantes():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()

        if not nome:
            flash("O nome do fabricante é obrigatório.", "erro")
            return redirect(url_for("fabricantes.fabricantes"))

        if Fabricante.query.filter_by(nome=nome).first():
            flash("Já existe um fabricante com esse nome.", "erro")
            return redirect(url_for("fabricantes.fabricantes"))

        novo_fabricante = Fabricante(nome=nome)

        try:
            db.session.add(novo_fabricante)
            db.session.commit()
            flash("Fabricante cadastrado com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao cadastrar fabricante")
            flash("Não foi possível cadastrar o fabricante.", "erro")

        return redirect(url_for("fabricantes.fabricantes"))

    fabricantes_cadastrados = (
        Fabricante.query
        .order_by(Fabricante.nome)
        .all()
    )

    return render_template(
        "fabricantes.html",
        fabricantes=fabricantes_cadastrados
    )


@bp_fabricantes.route(
    "/fabricantes/<int:id>/editar",
    methods=["GET", "POST"]
)
def editar_fabricante(id):

    fabricante = db.session.get(Fabricante, id)

    if fabricante is None:
        flash("Fabricante não encontrado.", "erro")
        return redirect(url_for("fabricantes.fabricantes"))

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()

        if not nome:
            flash("O nome do fabricante é obrigatório.", "erro")
        elif Fabricante.query.filter(
            Fabricante.nome == nome,
            Fabricante.id != id
        ).first():
            flash("Já existe outro fabricante com esse nome.", "erro")
        else:
            try:
                fabricante.nome = nome
                db.session.commit()
                flash("Fabricante atualizado com sucesso!", "sucesso")
                return redirect(url_for("fabricantes.fabricantes"))
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Erro ao editar fabricante")
                flash("Não foi possível atualizar o fabricante.", "erro")

    return render_template(
        "editar_fabricante.html",
        fabricante=fabricante
    )


@bp_fabricantes.route(
    "/fabricantes/<int:id>/excluir",
    methods=["POST"]
)
def excluir_fabricante(id):

    fabricante = db.session.get(Fabricante, id)

    if fabricante is None:
        flash("Fabricante não encontrado.", "erro")
        return redirect(url_for("fabricantes.fabricantes"))

    if fabricante.modelos:
        flash(
            "Não é possível excluir: existem modelos vinculados "
            "a este fabricante.",
            "erro"
        )
        return redirect(url_for("fabricantes.fabricantes"))

    try:
        db.session.delete(fabricante)
        db.session.commit()
        flash("Fabricante excluído com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir fabricante")
        flash("Não foi possível excluir o fabricante.", "erro")

    return redirect(url_for("fabricantes.fabricantes"))
