from flask import Flask, render_template, request, redirect, url_for, flash, session, app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
# from flask_wtf import FlaskForm
# from wtforms import StringField, IntegerField, FloatField, DecimalField, PasswordField, SubmitField
# from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Date, and_, or_
from datetime import datetime, timedelta
import requests
import pandas as pd
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config["SECRET_KEY"] = "!AcvMLfVDTRxc624^t^R"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)
bootstrap = Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)

class Clientes(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(250), nullable=False)
    pj: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    telefone: Mapped[int] = mapped_column(Integer, nullable=False)
    endereco: Mapped[str] = mapped_column(String(300), nullable=True)
    id_assessor: Mapped[str] = mapped_column(Integer, nullable=False)
    assessor: Mapped[str] = mapped_column(String(250), nullable=False)
    conta: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    cod_bolsa: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    perfil: Mapped[int] = mapped_column(Integer, nullable=True)
    valor_estimado: Mapped[int] = mapped_column(Integer, nullable=True)
    valor_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    abertura: Mapped[Date] = mapped_column(Date, nullable=True)
    fechamento: Mapped[Date] = mapped_column(Date, nullable=True)
    inicio: Mapped[Date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(250), nullable=True)


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(1000), nullable=False)
    admin: Mapped[int] = mapped_column(Integer, nullable=True)
    mesa: Mapped[int] = mapped_column(Integer)
    # mesa: 0 não 1 RF 2 RV


class Tarefas(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tarefa: Mapped[str] = mapped_column(String(250))
    tipo: Mapped[str] = mapped_column(String(250))
    prioridade: Mapped[str] = mapped_column(String(250))
    prazo: Mapped[Date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(250))
    observacao: Mapped[str] = mapped_column(String(500), nullable=True)
    mesa: Mapped[int] = mapped_column(Integer)


class ativos(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cliente: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[str] = mapped_column(String(250))
    tipo: Mapped[str] = mapped_column(String(250))
    nome: Mapped[str] = mapped_column(String(250))
    taxa: Mapped[float] = mapped_column(Float)
    cupom: Mapped[float] = mapped_column(Float)


class carteira(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cliente: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[str] = mapped_column(String(250))
    tipo: Mapped[str] = mapped_column(String(250))
    nome: Mapped[str] = mapped_column(String(250))
    taxa: Mapped[float] = mapped_column(Float)
    cupom: Mapped[float] = mapped_column(Float)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.before_request
def make_session_permanet():
    session.permanent = True
    app.permanet_session_lifetime = timedelta(minutes=5)


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
@app.route('/tarefas/<int:id>', methods=["POST", "GET"])
@login_required
def tarefas(id):
    session['user_id'] = id
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Clientes).where(Clientes.id == id))
    cliente = result.scalar()
    result = db.session.execute(
        db.select(Tarefas).where(Tarefas.cliente_id == cliente.id, Tarefas.status != "cancelado", Tarefas.status != 'conluído', Tarefas.mesa != 1))
    tarefa = result.scalars()
    return render_template("tarefas.html", user_name=user_name, cliente=cliente, tarefa=tarefa)


@app.route('/adicionar_tarefa/<int:id>', methods=["POST", "GET"])
@login_required
def adicionar_tarefa(id):
    if request.method == "POST":
        tarefa = request.form.get('tarefa')
        tipo = request.form.get('tipo')
        prioridade = request.form.get('prioridade')
        prazo = request.form.get('prazo')
        prazo = datetime.strptime(prazo, "%Y-%m-%d").date() if prazo else None
        mesa = request.form.get('mesa')
        if mesa =='mesa':
            mesa=1

        novo = Tarefas(
            cliente_id=id,
            tarefa=tarefa,
            tipo=tipo,
            prioridade=prioridade,
            prazo=prazo,
            status="novo",
            mesa=mesa
        )
        db.session.add(novo)
        db.session.commit()
        return redirect(url_for('tarefas', id=id))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Clientes).where(Clientes.id == id))
    cliente = result.scalar()
    return render_template("adicionar_tarefa.html", user_name=user_name, cliente=cliente, id=id)


@app.route('/editar_tarefa/<int:id>', methods=["POST", "GET"])
@login_required
def editar_tarefa(id):
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

        result = db.session.execute(db.select(Tarefas).where(Tarefas.id == id))
        resultado = result.scalar()
        resultado.tarefa = tarefa
        resultado.prioridade = prioridade
        resultado.prazo = prazo
        resultado.status = status
        resultado.observacao = observacao
        resultado.mesa = mesa
        db.session.commit()
        return redirect(url_for("tarefas", id=id))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Tarefas).where(Tarefas.id == id))
    tarefa = result.scalar()
    return render_template("editar_tarefa.html", tarefa=tarefa, user_name=user_name)


@app.route('/tarefas_concluidas/<int:id>', methods=["POST", "GET"])
@login_required
def tarefas_concluidas(id):
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Tarefas).where(Tarefas.cliente_id == id, Tarefas.status == 'concluido'))
    tarefa = result.scalars()
    return render_template("tarefas_concluidas", tarefa=tarefa, user_name=user_name)


carrinho_de_investimentos = []
@app.route('/adicionar_ativo/<int:id>', methods=["POST", "GET"])
@login_required
def adicionar_ativo(id):
    if request.method == "POST":
        form = request.form.get('id')
        return redirect(url_for("tarefas", id=form))
    user_name = session.get('user_name')
    result = db.session.execute(db.select(Clientes).where(Clientes.id == id))
    cliente = result.scalar()
    return render_template("adicionar_ativo.html", user_name=user_name, cliente=cliente)


@app.route('/adicionar_rendafixa/', methods=["POST", "GET"])
@login_required
def adicionar_rendafixa():
    if request.method == "POST":
        return redirect(url_for('adicionar_ativo'))
    user_name = session.get('user_name')
    titulos = pd.read_csv('titulos publicos.csv')
    creditos = pd.read_csv('cri-cra.csv')
    debentures = pd.read_csv('debentures.csv')
    return render_template("adicionar_rendafixa.html", user_name=user_name, titulos=titulos, creditos=creditos, debentures=debentures)


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

@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))

@app.errorhandler(404)
def unauthorized(error):
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
