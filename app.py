
from flask import *
from config import db
from models.regiao import Regiao

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




with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
