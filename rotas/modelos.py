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
from models.modelo_equipamento import ModeloEquipamento
from models.interface_modelo import InterfaceModelo
from models.porta_alimentacao_modelo import PortaAlimentacaoModelo
from models.equipamento import Equipamento
from models.interface_equipamento import InterfaceEquipamento


bp_modelos = Blueprint("modelos", __name__)


def _validar_dados_modelo(modelo_id=None):
    """Valida o formulário e devolve (dados, erros)."""

    fabricante_id = request.form.get("fabricante_id", type=int)
    nome_modelo = request.form.get("modelo", "").strip()
    fluxo_ar = request.form.get("fluxo_ar", "").strip()
    unidade_peso = request.form.get("unidade_peso", "").strip()

    altura_bruta = request.form.get("altura_u", "").strip()
    peso_bruto = request.form.get("peso", "").strip()

    erros = []

    # Altura em U
    altura_u = 0.0

    if altura_bruta:
        try:
            altura_u = float(altura_bruta.replace(",", "."))
        except ValueError:
            erros.append("A altura em U deve ser um número.")
        else:
            if altura_u < 0:
                erros.append("A altura em U não pode ser negativa.")

    # Peso
    peso = None

    if peso_bruto:
        try:
            peso = float(peso_bruto.replace(",", "."))
        except ValueError:
            erros.append("O peso deve ser um número.")
        else:
            if peso < 0:
                erros.append("O peso não pode ser negativo.")

    # Fabricante
    if not fabricante_id:
        erros.append("Selecione um fabricante.")
    elif db.session.get(Fabricante, fabricante_id) is None:
        erros.append("O fabricante selecionado não existe.")

    # Nome do modelo
    if not nome_modelo:
        erros.append("Informe o nome do modelo.")

    # Unicidade: o nome do modelo é único no banco.
    if nome_modelo:
        consulta_modelo = ModeloEquipamento.query.filter_by(
            modelo=nome_modelo
        )

        if modelo_id is not None:
            consulta_modelo = consulta_modelo.filter(
                ModeloEquipamento.id != modelo_id
            )

        if consulta_modelo.first():
            erros.append("Já existe um modelo com esse nome.")

    dados = {
        "fabricante_id": fabricante_id,
        "modelo": nome_modelo,
        "altura_u": altura_u,
        "profundidade_completa": (
            "profundidade_completa" in request.form
        ),
        "fluxo_ar": fluxo_ar or None,
        "peso": peso,
        "unidade_peso": unidade_peso or None
    }

    return dados, erros



# CREATE + READ
@bp_modelos.route("/modelos", methods=["GET", "POST"])
def modelos():

    if request.method == "POST":

        dados, erros = _validar_dados_modelo()

        if erros:
            for erro in erros:
                flash(erro, "erro")
            return redirect(url_for("modelos.modelos"))

        novo_modelo = ModeloEquipamento(**dados)

        try:
            db.session.add(novo_modelo)
            db.session.commit()
            flash("Modelo cadastrado com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao cadastrar modelo")
            flash("Não foi possível cadastrar o modelo.", "erro")

        return redirect(url_for("modelos.modelos"))

    # READ
    filtro_fabricante_id = request.args.get("fabricante_id", type=int)
    pagina = request.args.get("page", 1, type=int)

    consulta = ModeloEquipamento.query

    if filtro_fabricante_id is not None:
        consulta = consulta.filter_by(fabricante_id=filtro_fabricante_id)

    modelos_paginados = (
        consulta
        .join(Fabricante)
        .order_by(Fabricante.nome, ModeloEquipamento.modelo)
        .paginate(page=pagina, per_page=25, error_out=False)
    )

    fabricantes = (
        Fabricante.query
        .order_by(Fabricante.nome)
        .all()
    )

    return render_template(
        "modelos.html",
        modelos=modelos_paginados,
        fabricantes=fabricantes,
        filtro_fabricante_id=filtro_fabricante_id
    )


# UPDATE
@bp_modelos.route(
    "/modelos/<int:id>/editar",
    methods=["GET", "POST"]
)
def editar_modelo(id):

    modelo = db.session.get(ModeloEquipamento, id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if request.method == "POST":

        dados, erros = _validar_dados_modelo(modelo_id=modelo.id)

        if erros:
            for erro in erros:
                flash(erro, "erro")
            return redirect(url_for("modelos.editar_modelo", id=modelo.id))

        try:
            for campo, valor in dados.items():
                setattr(modelo, campo, valor)

            db.session.commit()
            flash("Modelo atualizado com sucesso!", "sucesso")
            return redirect(url_for("modelos.modelos"))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao editar modelo")
            flash("Não foi possível atualizar o modelo.", "erro")

    fabricantes = (
        Fabricante.query
        .order_by(Fabricante.nome)
        .all()
    )

    return render_template(
        "editar_modelo.html",
        modelo=modelo,
        fabricantes=fabricantes
    )


# DELETE
@bp_modelos.route(
    "/modelos/<int:id>/excluir",
    methods=["POST"]
)
def excluir_modelo(id):

    modelo = db.session.get(ModeloEquipamento, id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if Equipamento.query.filter_by(modelo_id=modelo.id).first():
        flash(
            "Não é possível excluir: existem equipamentos com este modelo.",
            "erro"
        )
        return redirect(url_for("modelos.modelos"))

    ids_interfaces = [interface.id for interface in modelo.interfaces]

    if ids_interfaces:
        interface_em_uso = InterfaceEquipamento.query.filter(
            InterfaceEquipamento.interface_modelo_id.in_(ids_interfaces)
        ).first()

        if interface_em_uso:
            flash(
                "Não é possível excluir: as interfaces deste modelo "
                "estão sendo usadas por equipamentos.",
                "erro"
            )
            return redirect(url_for("modelos.modelos"))

    try:
        db.session.delete(modelo)
        db.session.commit()
        flash("Modelo excluído com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir modelo")
        flash("Não foi possível excluir o modelo.", "erro")

    return redirect(url_for("modelos.modelos"))


# CREATE + READ - INTERFACES DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/interfaces",
    methods=["GET", "POST"]
)
def interfaces_modelo(modelo_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        habilitada = "habilitada" in request.form
        gerenciamento = "gerenciamento" in request.form

        if not nome or not tipo:
            flash("Informe o nome e o tipo da interface.", "erro")
            return redirect(
                url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
            )

        if InterfaceModelo.query.filter_by(
            modelo_id=modelo.id,
            nome=nome
        ).first():
            flash(
                "Já existe uma interface com esse nome neste modelo.",
                "erro"
            )
            return redirect(
                url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
            )

        nova_interface = InterfaceModelo(
            modelo_id=modelo.id,
            nome=nome,
            tipo=tipo,
            habilitada=habilitada,
            gerenciamento=gerenciamento
        )

        try:
            db.session.add(nova_interface)
            db.session.commit()
            flash("Interface cadastrada com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erro ao cadastrar interface")
            flash("Não foi possível cadastrar a interface.", "erro")

        return redirect(
            url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
        )

    pagina = request.args.get("page", 1, type=int)

    interfaces_paginadas = (
        InterfaceModelo.query
        .filter_by(modelo_id=modelo.id)
        .order_by(InterfaceModelo.nome)
        .paginate(page=pagina, per_page=50, error_out=False)
    )

    return render_template(
        "interfaces_modelo.html",
        modelo=modelo,
        interfaces=interfaces_paginadas
    )


# UPDATE - INTERFACE DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/interfaces/<int:interface_id>/editar",
    methods=["GET", "POST"]
)
def editar_interface_modelo(modelo_id, interface_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)
    interface = db.session.get(InterfaceModelo, interface_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if interface is None or interface.modelo_id != modelo.id:
        flash("Interface não encontrada neste modelo.", "erro")
        return redirect(
            url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
        )

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        habilitada = "habilitada" in request.form
        gerenciamento = "gerenciamento" in request.form

        if not nome or not tipo:
            flash("Informe o nome e o tipo da interface.", "erro")
        elif InterfaceModelo.query.filter(
            InterfaceModelo.modelo_id == modelo.id,
            InterfaceModelo.nome == nome,
            InterfaceModelo.id != interface.id
        ).first():
            flash(
                "Já existe outra interface com esse nome neste modelo.",
                "erro"
            )
        else:
            try:
                interface.nome = nome
                interface.tipo = tipo
                interface.habilitada = habilitada
                interface.gerenciamento = gerenciamento

                db.session.commit()
                flash("Interface atualizada com sucesso!", "sucesso")
                return redirect(
                    url_for(
                        "modelos.interfaces_modelo",
                        modelo_id=modelo.id
                    )
                )
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Erro ao editar interface")
                flash("Não foi possível atualizar a interface.", "erro")

    return render_template(
        "editar_interface_modelo.html",
        modelo=modelo,
        interface=interface
    )


# DELETE - INTERFACE DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/interfaces/<int:interface_id>/excluir",
    methods=["POST"]
)
def excluir_interface_modelo(modelo_id, interface_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)
    interface = db.session.get(InterfaceModelo, interface_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if interface is None or interface.modelo_id != modelo.id:
        flash("Interface não encontrada neste modelo.", "erro")
        return redirect(
            url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
        )

    if InterfaceEquipamento.query.filter_by(
        interface_modelo_id=interface.id
    ).first():
        flash(
            "Não é possível excluir: esta interface está sendo usada "
            "por equipamentos.",
            "erro"
        )
        return redirect(
            url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
        )

    try:
        db.session.delete(interface)
        db.session.commit()
        flash("Interface excluída com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erro ao excluir interface")
        flash("Não foi possível excluir a interface.", "erro")

    return redirect(
        url_for("modelos.interfaces_modelo", modelo_id=modelo.id)
    )


# CREATE + READ - PORTAS DE ALIMENTAÇÃO DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/portas-alimentacao",
    methods=["GET", "POST"]
)
def portas_alimentacao_modelo(modelo_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if not nome or not tipo:
            flash("Informe o nome e o tipo da porta.", "erro")
            return redirect(
                url_for(
                    "modelos.portas_alimentacao_modelo",
                    modelo_id=modelo.id
                )
            )

        if PortaAlimentacaoModelo.query.filter_by(
            modelo_id=modelo.id,
            nome=nome
        ).first():
            flash("Já existe uma porta com esse nome neste modelo.", "erro")
            return redirect(
                url_for(
                    "modelos.portas_alimentacao_modelo",
                    modelo_id=modelo.id
                )
            )

        nova_porta = PortaAlimentacaoModelo(
            modelo_id=modelo.id,
            nome=nome,
            tipo=tipo,
            descricao=descricao or None
        )

        try:
            db.session.add(nova_porta)
            db.session.commit()
            flash("Porta de alimentação cadastrada com sucesso!", "sucesso")
        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Erro ao cadastrar porta de alimentação"
            )
            flash(
                "Não foi possível cadastrar a porta de alimentação.",
                "erro"
            )

        return redirect(
            url_for(
                "modelos.portas_alimentacao_modelo",
                modelo_id=modelo.id
            )
        )

    portas = (
        PortaAlimentacaoModelo.query
        .filter_by(modelo_id=modelo.id)
        .order_by(PortaAlimentacaoModelo.nome)
        .all()
    )

    return render_template(
        "portas_alimentacao_modelo.html",
        modelo=modelo,
        portas=portas
    )


# UPDATE - PORTA DE ALIMENTAÇÃO DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/portas-alimentacao/<int:porta_id>/editar",
    methods=["GET", "POST"]
)
def editar_porta_alimentacao_modelo(modelo_id, porta_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)
    porta = db.session.get(PortaAlimentacaoModelo, porta_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if porta is None or porta.modelo_id != modelo.id:
        flash("Porta não encontrada neste modelo.", "erro")
        return redirect(
            url_for(
                "modelos.portas_alimentacao_modelo",
                modelo_id=modelo.id
            )
        )

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if not nome or not tipo:
            flash("Informe o nome e o tipo da porta.", "erro")
        elif PortaAlimentacaoModelo.query.filter(
            PortaAlimentacaoModelo.modelo_id == modelo.id,
            PortaAlimentacaoModelo.nome == nome,
            PortaAlimentacaoModelo.id != porta.id
        ).first():
            flash(
                "Já existe outra porta com esse nome neste modelo.",
                "erro"
            )
        else:
            try:
                porta.nome = nome
                porta.tipo = tipo
                porta.descricao = descricao or None

                db.session.commit()
                flash(
                    "Porta de alimentação atualizada com sucesso!",
                    "sucesso"
                )
                return redirect(
                    url_for(
                        "modelos.portas_alimentacao_modelo",
                        modelo_id=modelo.id
                    )
                )
            except Exception:
                db.session.rollback()
                current_app.logger.exception(
                    "Erro ao editar porta de alimentação"
                )
                flash(
                    "Não foi possível atualizar a porta de alimentação.",
                    "erro"
                )

    return render_template(
        "editar_porta_alimentacao_modelo.html",
        modelo=modelo,
        porta=porta
    )


# DELETE - PORTA DE ALIMENTAÇÃO DO MODELO
@bp_modelos.route(
    "/modelos/<int:modelo_id>/portas-alimentacao/<int:porta_id>/excluir",
    methods=["POST"]
)
def excluir_porta_alimentacao_modelo(modelo_id, porta_id):

    modelo = db.session.get(ModeloEquipamento, modelo_id)
    porta = db.session.get(PortaAlimentacaoModelo, porta_id)

    if modelo is None:
        flash("Modelo não encontrado.", "erro")
        return redirect(url_for("modelos.modelos"))

    if porta is None or porta.modelo_id != modelo.id:
        flash("Porta não encontrada neste modelo.", "erro")
        return redirect(
            url_for(
                "modelos.portas_alimentacao_modelo",
                modelo_id=modelo.id
            )
        )

    try:
        db.session.delete(porta)
        db.session.commit()
        flash("Porta de alimentação excluída com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Erro ao excluir porta de alimentação"
        )
        flash("Não foi possível excluir a porta de alimentação.", "erro")

    return redirect(
        url_for(
            "modelos.portas_alimentacao_modelo",
            modelo_id=modelo.id
        )
    )
