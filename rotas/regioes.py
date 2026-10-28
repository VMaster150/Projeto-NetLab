
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
            try:
                regiao_pai = db.session.get(Regiao, int(regiao_pai_id))
            except ValueError:
                regiao_pai = None

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
            app.logger.exception("Erro ao cadastrar região")
            flash("Não foi possível cadastrar a região.", "erro")

        return redirect(url_for("regiao"))

    # Identificador da região escolhida no seletor
    filtro_regiao_id = request.args.get("filtro_regiao_id", type=int)

    # Busca todas as regiões
    todas_regioes = Regiao.query.order_by(Regiao.nome).all()

    # Busca as regiões principais
    regioes_principais = (
        Regiao.query
        .filter_by(regiao_pai_id=None)
        .order_by(Regiao.nome)
        .all()
    )

    # Prepara as regiões para o formulário de cadastro e para o filtro
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

    # Por padrão, exibe todas as regiões
    regioes_principais_exibidas = regioes_principais

    # IDs das regiões que serão mostradas no HTML
    ids_regioes_visiveis = {
        item.id for item in todas_regioes
    }

    if filtro_regiao_id is not None:
        regiao_selecionada = db.session.get(Regiao, filtro_regiao_id)

        if regiao_selecionada is None:
            flash("A região selecionada não existe.", "erro")
            return redirect(url_for("regiao"))

        # Começa com a região escolhida e inclui todas as suas sub-regiões
        ids_regioes_visiveis = set()

        def incluir_subregioes(item):
            ids_regioes_visiveis.add(item.id)

            for filha in item.subregioes:
                incluir_subregioes(filha)

        incluir_subregioes(regiao_selecionada)

        # Mantém a hierarquia, mostrando a região escolhida como raiz
        regioes_principais_exibidas = [regiao_selecionada]

        # Se a região escolhida for uma sub-região, a macro HTML
        # precisa começar nela com nível zero, para exibi-la corretamente.
        # A hierarquia original do banco de dados não é modificada.

    return render_template(
        "regiao.html",
        regioes=todas_regioes,
        regioes_principais=regioes_principais_exibidas,
        regioes_para_selecao=regioes_para_selecao,
        filtro_regiao_id=filtro_regiao_id,
        ids_regioes_visiveis=ids_regioes_visiveis,
        regioes_encontradas=todas_regioes
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

