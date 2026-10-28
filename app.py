from flask import *
from config import db
from models.regiao import Regiao
from models.fabricante import Fabricante
from models.modelo_equipamento import ModeloEquipamento
from models.interface_modelo import InterfaceModelo
from models.porta_alimentacao_modelo import PortaAlimentacaoModelo
from models.equipamento import Equipamento
from models.interface_equipamento import InterfaceEquipamento
from models.modelo_equipamento import ModeloEquipamento
from models.conexao import Conexao
from flask import Blueprint
from rotas.regiao import bp_regioes

app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave-temporaria-netlab'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:4548@localhost:5432/netlab'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



@app.route("/equipamentos", methods=["GET", "POST"])
def equipamentos():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        tipo = request.form.get("tipo", "").strip()
        regiao_id = request.form.get("regiao_id", "").strip()
        fabricante_id = request.form.get("fabricante_id", "").strip()
        modelo_id = request.form.get("modelo_id", "").strip()

        if not nome or not tipo or not regiao_id:
            flash(
                "Preencha o nome, o tipo e a região.",
                "erro"
            )
            return redirect(url_for("equipamentos"))

        try:
            regiao = db.session.get(Regiao, int(regiao_id))

            if regiao is None:
                flash("A região selecionada não existe.", "erro")
                return redirect(url_for("equipamentos"))

            fabricante = None
            modelo = None

            if fabricante_id:
                fabricante = db.session.get(
                    Fabricante, int(fabricante_id)
                )

                if fabricante is None:
                    flash("Fabricante não encontrado.", "erro")
                    return redirect(url_for("equipamentos"))

            if modelo_id:
                modelo = db.session.get(
                    ModeloEquipamento, int(modelo_id)
                )

                if modelo is None:
                    flash("Modelo não encontrado.", "erro")
                    return redirect(url_for("equipamentos"))

                if fabricante is None:
                    fabricante = modelo.fabricante
                elif modelo.fabricante_id != fabricante.id:
                    flash(
                        "O modelo não pertence ao fabricante selecionado.",
                        "erro"
                    )
                    return redirect(url_for("equipamentos"))

            novo_equipamento = Equipamento(
                nome=nome,
                tipo=tipo,
                regiao_id=regiao.id,
                fabricante_id=fabricante.id if fabricante else None,
                modelo_id=modelo.id if modelo else None
            )

            db.session.add(novo_equipamento)

            # Garante que o equipamento receba um ID antes
            # de criar suas portas.
            db.session.flush()

            # Cria as portas individuais a partir das interfaces do modelo.
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

            # Salva o equipamento e suas portas na mesma transação.
            db.session.commit()

            flash(
                "Equipamento cadastrado com sucesso, incluindo suas interfaces!",
                "sucesso"
            )
            return redirect(url_for("equipamentos"))

        except ValueError:
            db.session.rollback()
            flash("Selecione identificadores válidos.", "erro")
            return redirect(url_for("equipamentos"))

        except Exception:
            db.session.rollback()
            app.logger.exception("Erro ao cadastrar equipamento")
            flash("Não foi possível cadastrar o equipamento.", "erro")
            return redirect(url_for("equipamentos"))

    # Região selecionada no filtro (GET)
    filtro_regiao_id = request.args.get(
        "filtro_regiao_id",
        type=int
    )

    # Mantém todas as regiões disponíveis para o cadastro e o filtro
    regioes = Regiao.query.order_by(Regiao.nome).all()

    fabricantes = Fabricante.query.order_by(
        Fabricante.nome
    ).all()

    # Consulta os equipamentos
    consulta_equipamentos = Equipamento.query

    # Se uma região foi selecionada, filtra por ela
    if filtro_regiao_id is not None:
        regiao_filtro = db.session.get(Regiao, filtro_regiao_id)

        if regiao_filtro is None:
            flash("A região selecionada não existe.", "erro")
            return redirect(url_for("equipamentos"))

        consulta_equipamentos = consulta_equipamentos.filter_by(
            regiao_id=filtro_regiao_id
        )

    equipamentos_cadastrados = (
        consulta_equipamentos
        .order_by(Equipamento.nome)
        .all()
    )

    return render_template(
        "equipamentos.html",
        regioes=regioes,
        fabricantes=fabricantes,
        equipamentos=equipamentos_cadastrados,
        filtro_regiao_id=filtro_regiao_id
    )


@app.route("/api/fabricantes/<int:fabricante_id>/modelos")
def modelos_por_fabricante(fabricante_id):
    fabricante = db.session.get(Fabricante, fabricante_id)

    if fabricante is None:
        return {"erro": "Fabricante não encontrado."}, 404

    modelos = (
        ModeloEquipamento.query
        .filter_by(fabricante_id=fabricante_id)
        .order_by(ModeloEquipamento.modelo)
        .all()
    )

    return {
        "modelos": [
            {
                "id": modelo.id,
                "nome": modelo.modelo
            }
            for modelo in modelos
        ]
    }


@app.route("/equipamentos/<int:id>")
def detalhe_equipamento(id):
    equipamento = db.get_or_404(Equipamento, id)

    return render_template(
        "detalhe_equipamento.html",
        equipamento=equipamento
    )


@app.route("/equipamentos/<int:equipamento_id>/portas")
def portas_equipamento(equipamento_id):
    equipamento = db.session.get(Equipamento, equipamento_id)

    if equipamento is None:
        flash("Equipamento não encontrado.", "erro")
        return redirect(url_for("equipamentos"))

    portas = (
        InterfaceEquipamento.query
        .filter_by(equipamento_id=equipamento.id)
        .order_by(InterfaceEquipamento.nome)
        .all()
    )

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

@app.route("/conexoes", methods=["GET", "POST"])
def conexoes():
    if request.method == "POST":
        origem_id = request.form.get("interface_origem_id", type=int)
        destino_id = request.form.get("interface_destino_id", type=int)
        tipo_cabo = request.form.get("tipo_cabo", "Ethernet").strip()
        descricao = request.form.get("descricao", "").strip()

        if not origem_id or not destino_id:
            flash("Selecione as duas portas.", "erro")
            return redirect(url_for("conexoes"))

        if origem_id == destino_id:
            flash("Escolha duas portas diferentes.", "erro")
            return redirect(url_for("conexoes"))

        origem = db.session.get(InterfaceEquipamento, origem_id)
        destino = db.session.get(InterfaceEquipamento, destino_id)

        if origem is None or destino is None:
            flash("Uma das portas selecionadas não existe.", "erro")
            return redirect(url_for("conexoes"))

        if not origem.habilitada or not destino.habilitada:
            flash("As duas portas precisam estar habilitadas.", "erro")
            return redirect(url_for("conexoes"))

        if origem.equipamento_id == destino.equipamento_id:
            flash(
                "Selecione portas de equipamentos diferentes.",
                "erro"
            )
            return redirect(url_for("conexoes"))

        if not tipo_cabo:
            flash("Informe o tipo de cabo.", "erro")
            return redirect(url_for("conexoes"))

        # Verifica se alguma das portas já está conectada.
        conexao_existente = Conexao.query.filter(
            db.or_(
                Conexao.interface_origem_id.in_([origem_id, destino_id]),
                Conexao.interface_destino_id.in_([origem_id, destino_id])
            )
        ).first()

        if conexao_existente:
            flash("Uma das portas já está conectada.", "erro")
            return redirect(url_for("conexoes"))

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
            app.logger.exception("Erro ao criar conexão")
            flash("Não foi possível criar a conexão.", "erro")

        return redirect(url_for("conexoes"))

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



@app.route("/nova-conexao/<int:interface_id>", methods=["GET", "POST"])
def nova_conexao(interface_id):
    porta_origem = db.session.get(InterfaceEquipamento, interface_id)

    if porta_origem is None:
        flash("Porta de origem não encontrada.", "erro")
        return redirect(url_for("equipamentos"))

    if not porta_origem.habilitada:
        flash("Esta porta está desabilitada.", "erro")
        return redirect(url_for(
            "portas_equipamento",
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
            "portas_equipamento",
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
                    "portas_equipamento",
                    equipamento_id=porta_origem.equipamento_id
                ))
            except Exception:
                db.session.rollback()
                app.logger.exception("Erro ao criar conexão")
                flash("Não foi possível criar a conexão.", "erro")

    return render_template(
        "nova_conexao.html",
        porta_origem=porta_origem,
        equipamentos_destino=equipamentos_destino,
        equipamento_destino_id=equipamento_destino_id,
        portas_destino=portas_destino
    )


@app.route("/desconectar/<int:conexao_id>", methods=["POST"])
def desconectar_cabo(conexao_id):
    conexao = db.session.get(Conexao, conexao_id)

    if conexao is None:
        flash("Conexão não encontrada.", "erro")
        return redirect(url_for("equipamentos"))

    equipamento_id = conexao.interface_origem.equipamento_id

    try:
        db.session.delete(conexao)
        db.session.commit()
        flash("Cabo desconectado com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        app.logger.exception("Erro ao desconectar cabo")
        flash("Não foi possível desconectar o cabo.", "erro")

    return redirect(url_for(
        "portas_equipamento",
        equipamento_id=equipamento_id
    ))




with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
