import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap4
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
#from flask_wtf import FlaskForm
#from wtforms import StringField, IntegerField, FloatField, DecimalField, PasswordField, SubmitField
#from wtforms.validators import DataRequired, Email
#from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Date, and_, or_, create_engine
from datetime import datetime, timedelta
# import requests
import pandas as pd
from sqlalchemy.exc import IntegrityError
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = 'VMLMABVC'  # development
# app.config["SECRET_KEY"] = os.environ.get('FLASK_KEY')  # production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///crm.db"  # development

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///crm.db")  #production


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)
bootstrap = Bootstrap4(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Clientes(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(250), nullable=False)
    pj: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    telefone: Mapped[str] = mapped_column(String(30), nullable=False)
    endereco: Mapped[str] = mapped_column(String(300), nullable=True)
    id_assessor: Mapped[str] = mapped_column(Integer, nullable=False)
    assessor: Mapped[str] = mapped_column(String(250), nullable=False)
    conta: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    cod_bolsa: Mapped[int] = mapped_column(Integer, nullable=True, unique=True)
    perfil: Mapped[int] = mapped_column(Integer, nullable=True)
    valor_estimado: Mapped[int] = mapped_column(Integer, nullable=True)
    valor_atual: Mapped[int] = mapped_column(Integer, nullable=True)
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
    nome_cliente: Mapped[str] = mapped_column(String(250))
    tarefa: Mapped[str] = mapped_column(String(250))
    tipo: Mapped[str] = mapped_column(String(250))
    prioridade: Mapped[str] = mapped_column(String(250))
    prazo: Mapped[Date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(250))
    observacao: Mapped[str] = mapped_column(String(500), nullable=True)
    mesa: Mapped[int] = mapped_column(Integer)


with app.app_context():
    db.create_all()
