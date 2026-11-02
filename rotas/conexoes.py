from flask import *

from config import db
from models.conexao import Conexao

from models.fabricante import Fabricante
from models.interface_equipamento import InterfaceEquipamento
from models.modelo_equipamento import ModeloEquipamento
from models.equipamento import Equipamento
from models.modelo_equipamento import ModeloEquipamento


bp_conexoes = Blueprint("conexoes", __name__)

@bp_conexoes.route("/conexoes", methods=["GET", "POST"])
def conexoes():
    if request.method == "POST":
        origem_id = request.form.get("interface_origem_id", type=int)
        destino_id = request.form.get("interface_destino_id", type=int)
        tipo_cabo = request.form.get("tipo_cabo", "Ethernet").strip()
        descricao = request.form.get("descricao", "").strip()

        if not origem_id or not destino_id:
            flash("Selecione as duas portas.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        if origem_id == destino_id:
            flash("Escolha duas portas diferentes.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        origem = db.session.get(InterfaceEquipamento, origem_id)
        destino = db.session.get(InterfaceEquipamento, destino_id)

        if origem is None or destino is None:
            flash("Uma das portas selecionadas não existe.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        if not origem.habilitada or not destino.habilitada:
            flash("As duas portas precisam estar habilitadas.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        if origem.equipamento_id == destino.equipamento_id:
            flash(
                "Selecione portas de equipamentos diferentes.",
                "erro"
            )
            return redirect(url_for("conexoes.conexoes"))

        if not tipo_cabo:
            flash("Informe o tipo de cabo.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        # Verifica se alguma das portas já está conectada.
        conexao_existente = Conexao.query.filter(
            db.or_(
                Conexao.interface_origem_id.in_([origem_id, destino_id]),
                Conexao.interface_destino_id.in_([origem_id, destino_id])
            )
        ).first()

        if conexao_existente:
            flash("Uma das portas já está conectada.", "erro")
            return redirect(url_for("conexoes.conexoes"))

        nova_conexao = Conexao(
            interface_origem_id=origem_id,
            interface_destino_id=destino_id,
            tipo_cabo=tipo_cabo,
            descricao=descricao or None
        )

        try:
            db.session.add(nova_conexao)
            db.session.commit()
            flash("Conexão criada com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao criar conexão")
            flash("Não foi possível criar a conexão.", "erro")

        return redirect(url_for("conexoes.conexoes"))

    portas = (
        InterfaceEquipamento.query
        .join(Equipamento)
        .filter(InterfaceEquipamento.habilitada.is_(True))
        .order_by(Equipamento.nome, InterfaceEquipamento.nome)
        .all()
    )

    conexoes_cadastradas = (
        Conexao.query
        .order_by(Conexao.id.desc())
        .all()
    )

    return render_template(
        "conexoes.html",
        portas=portas,
        conexoes=conexoes_cadastradas
    )



@bp_conexoes.route("/nova-conexao/<int:interface_id>", methods=["GET", "POST"])
def nova_conexao(interface_id):
    porta_origem = db.session.get(InterfaceEquipamento, interface_id)

    if porta_origem is None:
        flash("Porta de origem não encontrada.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    if not porta_origem.habilitada:
        flash("Esta porta está desabilitada.", "erro")
        return redirect(url_for(
            "equipamentos.portas_equipamento",
            equipamento_id=porta_origem.equipamento_id
        ))

    # Verifica se a porta de origem já está conectada.
    conexao_existente = Conexao.query.filter(
        db.or_(
            Conexao.interface_origem_id == porta_origem.id,
            Conexao.interface_destino_id == porta_origem.id
        )
    ).first()

    if conexao_existente:
        flash("Esta porta já está conectada.", "erro")
        return redirect(url_for(
            "equipamentos.portas_equipamento",
            equipamento_id=porta_origem.equipamento_id
        ))

    equipamentos_destino = (
        Equipamento.query
        .filter(Equipamento.id != porta_origem.equipamento_id)
        .order_by(Equipamento.nome)
        .all()
    )

    equipamento_destino_id = request.values.get(
        "equipamento_destino_id", type=int
    )

    portas_destino = []

    if equipamento_destino_id:
        equipamento_destino = db.session.get(
            Equipamento, equipamento_destino_id
        )

        if (
            equipamento_destino is not None
            and equipamento_destino.id != porta_origem.equipamento_id
        ):
            portas_destino = (
                InterfaceEquipamento.query
                .filter_by(
                    equipamento_id=equipamento_destino.id,
                    habilitada=True
                )
                .order_by(InterfaceEquipamento.nome)
                .all()
            )

            # Retira da lista as portas que já estão conectadas.
            portas_destino = [
                porta for porta in portas_destino
                if not Conexao.query.filter(
                    db.or_(
                        Conexao.interface_origem_id == porta.id,
                        Conexao.interface_destino_id == porta.id
                    )
                ).first()
            ]

    if request.method == "POST":
        destino_id = request.form.get("interface_destino_id", type=int)
        tipo_cabo = request.form.get("tipo_cabo", "Ethernet").strip()
        descricao = request.form.get("descricao", "").strip()

        porta_destino = db.session.get(InterfaceEquipamento, destino_id)

        if (
            porta_destino is None
            or porta_destino not in portas_destino
        ):
            flash("Selecione uma porta de destino válida e disponível.", "erro")
        elif not tipo_cabo:
            flash("Informe o tipo de cabo.", "erro")
        else:
            nova_conexao = Conexao(
                interface_origem_id=porta_origem.id,
                interface_destino_id=porta_destino.id,
                tipo_cabo=tipo_cabo,
                descricao=descricao or None
            )

            try:
                db.session.add(nova_conexao)
                db.session.commit()

                flash("Cabo conectado com sucesso!", "sucesso")
                return redirect(url_for(
                    "equipamentos.portas_equipamento",
                    equipamento_id=porta_origem.equipamento_id
                ))
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Erro ao criar conexão")
                flash("Não foi possível criar a conexão.", "erro")

    return render_template(
        "nova_conexao.html",
        porta_origem=porta_origem,
        equipamentos_destino=equipamentos_destino,
        equipamento_destino_id=equipamento_destino_id,
        portas_destino=portas_destino
    )


@bp_conexoes.route("/desconectar/<int:conexao_id>", methods=["POST"])
def desconectar_cabo(conexao_id):
    conexao = db.session.get(Conexao, conexao_id)

    if conexao is None:
        flash("Conexão não encontrada.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    equipamento_id = conexao.interface_origem.equipamento_id

    try:
        db.session.delete(conexao)
        db.session.commit()
        flash("Cabo desconectado com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao desconectar cabo")
        flash("Não foi possível desconectar o cabo.", "erro")

    return redirect(url_for(
        "equipamentos.portas_equipamento",
        equipamento_id=equipamento_id
    ))
