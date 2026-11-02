from flask import *

from config import db

from models.regiao import Regiao
from models.fabricante import Fabricante
from models.modelo_equipamento import ModeloEquipamento
from models.equipamento import Equipamento
from models.interface_equipamento import InterfaceEquipamento
from models.conexao import Conexao


bp_equipamentos = Blueprint("equipamentos", __name__)


# CREATE - CADASTRAR EQUIPAMENTO
@bp_equipamentos.route("/equipamentos", methods=["GET", "POST"])
def equipamentos():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        regiao_id = request.form.get("regiao_id", type=int)
        fabricante_id = request.form.get("fabricante_id", type=int)
        modelo_id = request.form.get("modelo_id", type=int)

        if not nome or not tipo or not regiao_id:
            flash("Preencha o nome, o tipo e a região.", "erro")
            return redirect(url_for("equipamentos.equipamentos"))

        try:
            # READ - Verifica se a região existe
            regiao = db.session.get(Regiao, regiao_id)

            if regiao is None:
                flash("Região não encontrada.", "erro")
                return redirect(url_for("equipamentos.equipamentos"))

            fabricante = None
            modelo = None

            if fabricante_id:
                fabricante = db.session.get(Fabricante, fabricante_id)

                if fabricante is None:
                    flash("Fabricante não encontrado.", "erro")
                    return redirect(url_for("equipamentos.equipamentos"))

            if modelo_id:
                modelo = db.session.get(ModeloEquipamento, modelo_id)

                if modelo is None:
                    flash("Modelo não encontrado.", "erro")
                    return redirect(url_for("equipamentos.equipamentos"))

                if fabricante is None:
                    fabricante = modelo.fabricante

                elif modelo.fabricante_id != fabricante.id:
                    flash("Modelo incompatível com o fabricante.", "erro")
                    return redirect(url_for("equipamentos.equipamentos"))

            # CREATE - Cria o equipamento
            novo_equipamento = Equipamento(
                nome=nome,
                tipo=tipo,
                regiao_id=regiao.id,
                fabricante_id=fabricante.id if fabricante else None,
                modelo_id=modelo.id if modelo else None
            )

            db.session.add(novo_equipamento)
            db.session.flush()

            # CREATE - Cria as interfaces do modelo
            if modelo is not None:

                for interface in modelo.interfaces:

                    if not interface.habilitada:
                        continue

                    nova_interface = InterfaceEquipamento(
                        equipamento_id=novo_equipamento.id,
                        interface_modelo_id=interface.id,
                        nome=interface.nome,
                        tipo=interface.tipo,
                        habilitada=True
                    )

                    db.session.add(nova_interface)

            db.session.commit()

            flash("Equipamento cadastrado com sucesso!", "sucesso")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao cadastrar equipamento")
            flash("Erro ao cadastrar equipamento.", "erro")

        return redirect(url_for("equipamentos.equipamentos"))

    # READ - Lista os equipamentos
    filtro_regiao_id = request.args.get("filtro_regiao_id", type=int)

    regioes = Regiao.query.order_by(Regiao.nome).all()

    fabricantes = Fabricante.query.order_by(
        Fabricante.nome
    ).all()

    consulta = Equipamento.query

    if filtro_regiao_id is not None:
        consulta = consulta.filter_by(regiao_id=filtro_regiao_id)

    equipamentos_cadastrados = consulta.order_by(
        Equipamento.nome
    ).all()

    return render_template(
        "equipamentos.html",
        regioes=regioes,
        fabricantes=fabricantes,
        equipamentos=equipamentos_cadastrados,
        filtro_regiao_id=filtro_regiao_id
    )


# READ - DETALHES DO EQUIPAMENTO
@bp_equipamentos.route("/equipamentos/<int:id>")
def detalhe_equipamento(id):

    equipamento = db.session.get(Equipamento, id)

    if equipamento is None:
        flash("Equipamento não encontrado.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    return render_template(
        "detalhe_equipamento.html",
        equipamento=equipamento
    )


# UPDATE - EDITAR EQUIPAMENTO
@bp_equipamentos.route("/equipamentos/<int:id>/editar", methods=["GET", "POST"])
def editar_equipamento(id):

    equipamento = db.session.get(Equipamento, id)

    if equipamento is None:
        flash("Equipamento não encontrado.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        regiao_id = request.form.get("regiao_id", type=int)

        if not nome or not tipo or not regiao_id:
            flash("Preencha todos os campos obrigatórios.", "erro")
        else:
            regiao = db.session.get(Regiao, regiao_id)

            if regiao is None:
                flash("Região não encontrada.", "erro")
            else:
                try:
                    # UPDATE - Altera os dados
                    equipamento.nome = nome
                    equipamento.tipo = tipo
                    equipamento.regiao_id = regiao.id

                    db.session.commit()

                    flash("Equipamento atualizado com sucesso!", "sucesso")

                    return redirect(url_for(
                        "equipamentos.detalhe_equipamento",
                        id=equipamento.id
                    ))

                except Exception:
                    db.session.rollback()
                    current_app.logger.exception("Erro ao editar equipamento")
                    flash("Não foi possível atualizar o equipamento.", "erro")

    regioes = Regiao.query.order_by(Regiao.nome).all()

    return render_template(
        "editar_equipamento.html",
        equipamento=equipamento,
        regioes=regioes
    )


# DELETE - EXCLUIR EQUIPAMENTO
@bp_equipamentos.route("/equipamentos/<int:id>/excluir", methods=["POST"])
def excluir_equipamento(id):

    equipamento = db.session.get(Equipamento, id)

    if equipamento is None:
        flash("Equipamento não encontrado.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    try:
        # READ - Busca as interfaces do equipamento
        portas = InterfaceEquipamento.query.filter_by(
            equipamento_id=equipamento.id
        ).all()

        ids_portas = [porta.id for porta in portas]

        if ids_portas:

            # READ - Busca as conexões dessas interfaces
            conexoes = Conexao.query.filter(
                db.or_(
                    Conexao.interface_origem_id.in_(ids_portas),
                    Conexao.interface_destino_id.in_(ids_portas)
                )
            ).all()

            # DELETE - Exclui as conexões
            for conexao in conexoes:
                db.session.delete(conexao)

            # DELETE - Exclui as interfaces
            for porta in portas:
                db.session.delete(porta)

        # DELETE - Exclui o equipamento
        db.session.delete(equipamento)

        db.session.commit()

        flash("Equipamento excluído com sucesso!", "sucesso")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir equipamento")
        flash("Não foi possível excluir o equipamento.", "erro")

    return redirect(url_for("equipamentos.equipamentos"))


# READ - MODELOS POR FABRICANTE (API)
@bp_equipamentos.route("/api/fabricantes/<int:fabricante_id>/modelos")
def modelos_por_fabricante(fabricante_id):

    fabricante = db.session.get(Fabricante, fabricante_id)

    if fabricante is None:
        return {"erro": "Fabricante não encontrado."}, 404

    modelos = ModeloEquipamento.query.filter_by(
        fabricante_id=fabricante_id
    ).order_by(ModeloEquipamento.modelo).all()

    return {
        "modelos": [
            {"id": modelo.id, "nome": modelo.modelo}
            for modelo in modelos
        ]
    }


# READ - PORTAS DO EQUIPAMENTO
@bp_equipamentos.route("/equipamentos/<int:equipamento_id>/portas")
def portas_equipamento(equipamento_id):

    equipamento = db.session.get(Equipamento, equipamento_id)

    if equipamento is None:
        flash("Equipamento não encontrado.", "erro")
        return redirect(url_for("equipamentos.equipamentos"))

    portas = InterfaceEquipamento.query.filter_by(
        equipamento_id=equipamento.id
    ).order_by(InterfaceEquipamento.nome).all()

    conexoes_portas = {}

    for porta in portas:

        conexao = Conexao.query.filter(
            db.or_(
                Conexao.interface_origem_id == porta.id,
                Conexao.interface_destino_id == porta.id
            )
        ).first()

        if conexao:

            if conexao.interface_origem_id == porta.id:
                outra_porta = conexao.interface_destino
            else:
                outra_porta = conexao.interface_origem

            conexoes_portas[porta.id] = {
                "id": conexao.id,
                "equipamento": outra_porta.equipamento.nome,
                "porta": outra_porta.nome,
                "tipo_cabo": conexao.tipo_cabo
            }

    portas_conectadas = set(conexoes_portas.keys())

    return render_template(
        "portas_equipamento.html",
        equipamento=equipamento,
        portas=portas,
        portas_conectadas=portas_conectadas,
        conexoes_portas=conexoes_portas
    )
