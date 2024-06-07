from app import *

pd.options.display.max_columns = 20


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.before_request
def make_session_permanet():
    session.permanent = True
    app.permanet_session_lifetime = timedelta(minutes=20)


@app.route('/', methods=["GET", "POST"])
def home():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("Email incorreto, tente novamente")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Senha incorreta, tente novamente')
            return redirect(url_for('login'))
        else:
            login_user(user)
            session['user_name'] = user.name
            session['user_id'] = user.id
            session['admin'] = user.admin
            session['mesa'] = user.mesa
            return redirect(url_for('monitorar'))
    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            flash("Email já cadastrado, faça o login")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            password=hash_and_salted_password,
            name=request.form.get('name'),
            admin=0
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        session['user_id'] = new_user.id
        session["user_name"] = new_user.name
        session['admin'] = user.admin
        session['mesa'] = user.mesa
        return redirect(url_for("monitorar"))
    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("Email incorreto, tente novamente")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Senha incorreta, tente novamente')
            return redirect(url_for('login'))
        else:
            login_user(user)
            session['user_name'] = user.name
            session['user_id'] = user.id
            session['admin'] = user.admin
            session['mesa'] = user.mesa
            return redirect(url_for('monitorar'))
    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/monitorar', methods=["POST", "GET"])
@login_required
def monitorar():
    name = session.get('user_name')
    user_id = session.get('user_id')
    admin = session.get("admin")
    mesa = session.get("mesa")
    print(mesa)
    result = db.session.execute(db.select(Clientes).where(Clientes.id_assessor == user_id))
    clientes = result.scalars()
    return render_template('monitorar.html', user_name=name, user_id=user_id, clientes=clientes, admin=admin, mesa=mesa)


@app.route('/cadastrar', methods=["POST", "GET"])
@login_required
def cadastrar():
    if request.method == "POST":
        formato_data = "%Y-%m-%d"
        inicio_str = request.form.get('cliente_desde')
        abertura_str = request.form.get('abertura')
        fechamento_str = request.form.get('fechamento')
        inicio = datetime.strptime(inicio_str, formato_data).date() if inicio_str else None
        abertura = datetime.strptime(abertura_str, formato_data).date() if abertura_str else None
        fechamento = datetime.strptime(fechamento_str, formato_data).date() if fechamento_str else None
        novo = Clientes(
            nome=request.form.get('nome'),
            pj=request.form.get('pj'),
            email=request.form.get('email'),
            telefone=request.form.get('telefone'),
            endereco=request.form.get('endereco'),
            id_assessor=session.get('user_id'),
            assessor=session.get('user_name'),
            conta=request.form.get('conta'),
            cod_bolsa=request.form.get('cod_bolsa'),
            perfil=request.form.get('perfil'),
            valor_estimado=request.form.get('valor_estimado'),
            valor_atual=request.form.get('valor_atual'),
            abertura=abertura,
            fechamento=fechamento,
            inicio=inicio,
            status='novo'
        )
        try:
            db.session.add(novo)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            error_message = str(e.orig)
            if 'duplicate key value violates unique constraint' in error_message:
                if 'conta' in error_message:
                    flash('A conta informada já está cadastrada. Por favor, insira outra.', 'error')
                elif 'cod_bolsa' in error_message:
                    flash('O código da bolsa informado já está cadastrada. Por favor, insira outro.', 'error')
        return redirect(url_for('monitorar'))

    name = session.get('user_name')
    user_id = session.get('user_id')
    mesa = session.get('mesa')
    return render_template("cadastrar.html", name=name, user_id=user_id, mesa=mesa)


# rotas tarefas: mostram em lista tarefas do cliente, adiciona e edita tarefa e atualiza DB,
# adiciona e edita carteira do cliente
@app.route('/tarefas', methods=["POST", "GET"])
@login_required
def tarefas():
    id_do_cliente = session.get('cliente_id')
    if id_do_cliente is None:
        return "Cliente ID não encontrado na sessão", 400
    user_name = session.get('user_name')
    cliente = db.session.execute(db.select(Clientes).where(Clientes.id == id_do_cliente)).scalar()
    tarefa = db.session.execute(
        db.select(Tarefas).where(Tarefas.cliente_id == id_do_cliente, Tarefas.status != "cancelado",
                                 Tarefas.status != 'concluido', Tarefas.mesa != 1)).scalars()
    mesa = session.get('mesa')
    return render_template("tarefas.html", user_name=user_name, cliente=cliente, tarefa=tarefa, mesa=mesa)


@app.route('/adicionar_tarefa/<int:id>', methods=["POST", "GET"])
@login_required
def adicionar_tarefa(idi):
    if request.method == "POST":
        tarefa = request.form.get('tarefa')
        tipo = request.form.get('tipo')
        prioridade = request.form.get('prioridade')
        prazo = request.form.get('prazo')
        prazo = datetime.strptime(prazo, "%Y-%m-%d").date() if prazo else None
        mesa = request.form.get('mesa')
        if mesa == 'mesa':
            mesa = 1
        else:
            mesa = 0

        novo = Tarefas(
            cliente_id=idi,
            tarefa=tarefa,
            tipo=tipo,
            prioridade=prioridade,
            prazo=prazo,
            status="novo",
            mesa=mesa
        )
        db.session.add(novo)
        db.session.commit()

        return redirect(url_for('tarefas', id=idi))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Clientes).where(Clientes.id == idi))
    cliente = result.scalar()
    return render_template("adicionar_tarefa.html", user_name=user_name, cliente=cliente, id=id)


@app.route('/editar_tarefa/<int:id>', methods=["POST", "GET"])
@login_required
def editar_tarefa(idi):
    if request.method == "POST":
        tarefa = request.form.get('tarefa')
        prioridade = request.form.get('prioridade')
        prazo = request.form.get('prazo')
        prazo = datetime.strptime(prazo, "%Y-%m-%d").date() if prazo else None
        status = request.form.get('status')
        observacao = request.form.get('observacao')
        mesa = request.form.get('mesa')
        if mesa == 'mesa':
            mesa = 1
        else:
            mesa = 0
        tarefa_to_update = db.session.execute(db.select(Tarefas).where(Tarefas.id == id)).scalar()
        with app.app_context():
            tarefa_to_update.tarefa = tarefa
            tarefa_to_update.prioridade = prioridade
            tarefa_to_update.prazo = prazo
            tarefa_to_update.status = status
            tarefa_to_update.observacao = observacao
            tarefa_to_update.mesa = mesa
            db.session.merge(tarefa_to_update)
            db.session.commit()
        tid = tarefa_to_update.cliente_id
        cliente = db.session.execute(db.select(Clientes).where(Clientes.id == tid)).scalar()
        return redirect(url_for("sessiondid", did=cliente.id, route='tarefas'))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Tarefas).where(Tarefas.id == idi))
    tarefa = result.scalar()
    return render_template("editar_tarefa.html", tarefa=tarefa, user_name=user_name)


@app.route('/tarefas_concluidas/<int:id>', methods=["POST", "GET"])
@login_required
def tarefas_concluidas(idi):
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Tarefas).where(Tarefas.cliente_id == idi, Tarefas.status == 'concluido'))
    tarefa = result.scalars()
    return render_template("tarefas_concluidas", tarefa=tarefa, user_name=user_name)


@app.route("/tarefas_mesa/")
@login_required
def tarefas_mesa():
    tarefas = db.session.execute(db.select(Tarefas).where(Tarefas.mesa == 1, Tarefas.status == 'concluido')).scalars()
    return render_template('tarefas_mesa.html', tarefas=tarefas)


@app.route("/tarefas_concluidas_mesa/")
@login_required
def tarefas_concluidas_mesa():
    tarefas = db.session.execute(db.select(Tarefas).where(Tarefas.mesa == 1, Tarefas.status == 'concluido')).scalars()
    return render_template('tarefas_concluidas_mesa.html', tarefas=tarefas)


CARRINHO = []


@app.route('/adicionar_ativo/<int:id>', methods=["POST", "GET"])
@login_required
def adicionar_ativo(idi):
    if request.method == "POST":
        form = request.form.get('id')
        return redirect(url_for("tarefas", id=form))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Clientes).where(Clientes.id == idi))
    cliente = result.scalar()
    return render_template("adicionar_ativo.html", user_name=user_name, cliente=cliente)


@app.route('/adicionar_rendafixa/', methods=["POST", "GET"])
@login_required
def adicionar_rendafixa():
    user_name = session.get('user_name')
    mesa = session.get('mesa')
    response = db.session.execute(db.select(Renda_fixa))
    titulos = response.scalars()
    return render_template("adicionar_rendafixa.html", user_name=user_name, mesa=mesa, titulos=titulos)


@app.route('/adicionar_fundos/', methods=["POST", "GET"])
@login_required
def adicionar_fundos():
    return render_template("adicionar_ativo.html")


@app.route('/adicionar_rendavariavel/', methods=["POST", "GET"])
@login_required
def adicionar_rendavariavel():
    return render_template("adicionar_ativo.html")


@app.route('/editar_cliente/<int:id>', methods=["POST", "GET"])
@login_required
def editar_cliente(id):
    result = db.session.execute(db.select(Clientes).where(Clientes.id == id))
    cliente = result.scalars()
    return render_template("editar_cliente.html", cliente=cliente)


@app.route('/perfil', methods=["POST", "GET"])
@login_required
def perfil():
    return render_template("perfil.html")


@app.route('/ativos', methods=["POST", "GET"])
@login_required
def ativos():
    return render_template("ativos.html")


@app.route('/verificar_conta')
def verificar_conta():
    conta = request.args.get('conta')
    existe = Clientes.query.filter_by(conta=conta).first() is not None
    return jsonify({'exists': existe})


@app.route('/verificar_cod_bolsa')
def verificar_cod_bolsa():
    cod_bolsa = request.args.get('cod_bolsa')
    existe = Clientes.query.filter_by(cod_bolsa=cod_bolsa).first() is not None
    return jsonify({'exists': existe})


@app.route("/sessiondid/<int:did>/<route>")
def sessiondid(did, route):
    if route == 'tarefas':
        session['cliente_id'] = did
        print(did)
        return redirect(url_for('tarefas'))
    else:
        pass


@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))


@app.errorhandler(404)
def unauthorized(error):
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=False)
