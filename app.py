from flask import *
from config import db
from models.regiao import Regiao
from models.fabricante import Fabricante
from models.modelo_equipamento import ModeloEquipamento
from models.interface_modelo import InterfaceModelo
from models.porta_alimentacao_modelo import PortaAlimentacaoModelo
from models.equipamento import Equipamento

app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave-temporaria-netlab'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:4548@localhost:5432/netlab'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


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
        return f"Erro ao conectar com o banco: {erro}", 500


@app.route("/regiao", methods=["GET", "POST"])
def regiao():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        regiao_pai_id = request.form.get("regiao_pai_id", "").strip()

        if not nome:
            flash("O nome da região é obrigatório.", "erro")
            return redirect(url_for("regiao"))

        regiao_pai = None

        if regiao_pai_id:
            regiao_pai = db.session.get(Regiao, regiao_pai_id)

            if regiao_pai is None:
                flash("A região pai selecionada não existe.", "erro")
                return redirect(url_for("regiao"))

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
            flash("Não foi possível cadastrar a região.", "erro")

        return redirect(url_for("regiao"))


    todas_regioes = Regiao.query.order_by(Regiao.nome).all()

    regioes_principais = (
        Regiao.query
        .filter_by(regiao_pai_id=None)
        .order_by(Regiao.nome)
        .all()
    )

    # Organiza as regiões em uma lista hierárquica
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

    return render_template(
        "regiao.html",
        regioes=todas_regioes,
        regioes_principais=regioes_principais,
        regioes_para_selecao=regioes_para_selecao
    )





@app.route("/regiao/<int:id>/editar", methods=["GET", "POST"])
def editar_regiao(id):
    regiao_atual = db.get_or_404(Regiao, id)
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        descricao = request.form.get("descricao", "").strip()
        regiao_pai_id = request.form.get("regiao_pai_id", "").strip()
        if not nome:
            flash("O nome da região é obrigatório.", "erro")
            return redirect(url_for("editar_regiao", id=id))
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
                return redirect(url_for("editar_regiao", id=id))

            # Impede que a região seja pai dela mesma
            # ou de uma de suas regiões ancestrais.
            verificar = regiao_pai

            while verificar is not None:
                if verificar.id == regiao_atual.id:
                    flash(
                        "Não é possível criar esse relacionamento, "
                        "pois ele formaria um ciclo.",
                        "erro"
                    )
                    return redirect(
                        url_for("editar_regiao", id=id)
                    )

                verificar = verificar.regiao_pai

        regiao_atual.nome = nome
        regiao_atual.descricao = descricao or None
        regiao_atual.regiao_pai = regiao_pai

        try:
            db.session.commit()
            flash("Região atualizada com sucesso!", "sucesso")
            return redirect(url_for("regiao"))
        except Exception:
            db.session.rollback()
            flash("Não foi possível atualizar a região.", "erro")
            return redirect(url_for("editar_regiao", id=id))
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





@app.route("/regiao/<int:id>/excluir", methods=["POST"])
def excluir_regiao(id):
    regiao = db.get_or_404(Regiao, id)

    if regiao.subregioes:
        flash(
            "Não é possível excluir esta região, "
            "pois ela possui sub-regiões. "
            "Mova ou exclua as sub-regiões primeiro.",
            "erro"
        )
        return redirect(url_for("regiao"))

    try:
        db.session.delete(regiao)
        db.session.commit()
        flash("Região excluída com sucesso!", "sucesso")
    except Exception:
        db.session.rollback()
        flash("Não foi possível excluir a região.", "erro")

    return redirect(url_for("regiao"))


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
            db.session.commit()

            flash("Equipamento cadastrado com sucesso!", "sucesso")
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

    regioes = Regiao.query.order_by(Regiao.nome).all()
    fabricantes = Fabricante.query.order_by(Fabricante.nome).all()

    equipamentos_cadastrados = (
        Equipamento.query
        .order_by(Equipamento.nome)
        .all()
    )

    return render_template(
        "equipamentos.html",
        regioes=regioes,
        fabricantes=fabricantes,
        equipamentos=equipamentos_cadastrados
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




with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
