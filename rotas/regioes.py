from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from config import db
from models.equipamento import Equipamento
from models.regiao import Regiao

bp_regioes = Blueprint("regioes", __name__)



@bp_regioes.route("/regiao", methods=["GET", "POST"])
def regiao():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        regiao_pai_id = request.form.get("regiao_pai_id", "").strip()

        if not nome:
            flash("O nome da região é obrigatório.", "erro")
            return redirect(url_for("regioes.regiao"))

        regiao_pai = None

        if regiao_pai_id:
            try:
                regiao_pai = db.session.get(Regiao, int(regiao_pai_id))
            except ValueError:
                regiao_pai = None

            if regiao_pai is None:
                flash("A região pai selecionada não existe.", "erro")
                return redirect(url_for("regioes.regiao"))

        nova_regiao = Regiao(
            nome=nome,
            descricao=descricao or None,
            regiao_pai=regiao_pai
        )

        try:
            db.session.add(nova_regiao)
            db.session.commit()
            flash("Região cadastrada com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao cadastrar região")
            flash("Não foi possível cadastrar a região.", "erro")

        return redirect(url_for("regioes.regiao"))

    filtro_regiao_id = request.args.get("filtro_regiao_id", type=int)

    todas_regioes = Regiao.query.order_by(Regiao.nome).all()

    regioes_principais = (
        Regiao.query
        .filter_by(regiao_pai_id=None)
        .order_by(Regiao.nome)
        .all()
    )

    regioes_para_selecao = []

    def organizar_regioes(lista_regioes, nivel=0):
        for item in sorted(lista_regioes, key=lambda r: r.nome.lower()):
            regioes_para_selecao.append({
                "id": item.id,
                "nome": item.nome,
                "nivel": nivel
            })

            organizar_regioes(item.subregioes, nivel + 1)

    organizar_regioes(regioes_principais)

    regioes_principais_exibidas = regioes_principais

    ids_regioes_visiveis = {
        item.id for item in todas_regioes
    }

    if filtro_regiao_id is not None:
        regiao_selecionada = db.session.get(Regiao, filtro_regiao_id)

        if regiao_selecionada is None:
            flash("A região selecionada não existe.", "erro")
            return redirect(url_for("regioes.regiao"))

        ids_regioes_visiveis = set()

        def incluir_subregioes(item):
            ids_regioes_visiveis.add(item.id)

            for filha in item.subregioes:
                incluir_subregioes(filha)

        incluir_subregioes(regiao_selecionada)

        regioes_principais_exibidas = [regiao_selecionada]



    return render_template(
        "regiao.html",
        regioes=todas_regioes,
        regioes_principais=regioes_principais_exibidas,
        regioes_para_selecao=regioes_para_selecao,
        filtro_regiao_id=filtro_regiao_id,
        ids_regioes_visiveis=ids_regioes_visiveis,
        regioes_encontradas=todas_regioes
    )



@bp_regioes.route("/regiao/<int:id>/editar", methods=["GET", "POST"])
def editar_regiao(id):
    regiao_atual = db.get_or_404(Regiao, id)
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        regiao_pai_id = request.form.get("regiao_pai_id", "").strip()
        if not nome:
            flash("O nome da região é obrigatório.", "erro")
            return redirect(url_for("regioes.editar_regiao", id=id))
        regiao_pai = None
        if regiao_pai_id:
            try:
                regiao_pai = db.session.get(
                    Regiao, int(regiao_pai_id)
                )
            except ValueError:
                regiao_pai = None

            if regiao_pai is None:
                flash("A região pai selecionada não existe.", "erro")
                return redirect(url_for("regioes.editar_regiao", id=id))


            verificar = regiao_pai

            while verificar is not None:
                if verificar.id == regiao_atual.id:
                    flash(
                        "Não é possível criar esse relacionamento, "
                        "pois ele formaria um ciclo.",
                        "erro"
                    )
                    return redirect(
                        url_for("regioes.editar_regiao", id=id)
                    )

                verificar = verificar.regiao_pai

        regiao_atual.nome = nome
        regiao_atual.descricao = descricao or None
        regiao_atual.regiao_pai = regiao_pai

        try:
            db.session.commit()
            flash("Região atualizada com sucesso!", "sucesso")
            return redirect(url_for("regioes.regiao"))
        except Exception:
            db.session.rollback()
            flash("Não foi possível atualizar a região.", "erro")
            return redirect(url_for("regioes.editar_regiao", id=id))
    todas_regioes = Regiao.query.order_by(Regiao.nome).all()
    regioes_para_selecao = []
    def organizar_regioes(lista_regioes, nivel=0):
        for item in sorted(lista_regioes, key=lambda r: r.nome.lower()):
            regioes_para_selecao.append({
                "id": item.id,
                "nome": item.nome,
                "nivel": nivel
            })
            organizar_regioes(item.subregioes, nivel + 1)
    regioes_principais = (
        Regiao.query
        .filter_by(regiao_pai_id=None)
        .order_by(Regiao.nome)
        .all()
    )
    organizar_regioes(regioes_principais)
    return render_template(
        "editar_regiao.html",
        regiao=regiao_atual,
        regioes_para_selecao=regioes_para_selecao
    )







@bp_regioes.route("/regiao/<int:id>/excluir", methods=["POST"])
def excluir_regiao(id):
    regiao = db.session.get(Regiao, id)

    if regiao is None:
        flash("Região não encontrada.", "erro")
        return redirect(url_for("regioes.regiao"))

    if regiao.subregioes:
        flash("Não é possível excluir: esta região possui sub-regiões.", "erro")
        return redirect(url_for("regioes.regiao"))

    equipamentos_vinculados = Equipamento.query.filter_by(
        regiao_id=id
    ).first()

    if equipamentos_vinculados:
        flash(
            "Não é possível excluir: existem equipamentos nesta região.",
            "erro"
        )
        return redirect(url_for("regioes.regiao"))

    try:
        db.session.delete(regiao)
        db.session.commit()

        flash("Região excluída com sucesso!", "sucesso")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir região")
        flash("Não foi possível excluir a região.", "erro")

    return redirect(url_for("regioes.regiao"))


