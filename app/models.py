from .extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSONB # Importe JSONB para dados semi-estruturados

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    tipo = db.Column(db.String(50), default="colaborador")
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255))

    def __repr__(self):
        return f"<User {self.email}>"

class Employees(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    cargo = db.Column(db.String(120), nullable=False)
    salario = db.Column(db.Numeric(10, 2), nullable=False)
    media_feedbacks = db.Column(db.Numeric(3, 2), default=0.0)
    data_entrada = db.Column(db.Date, default=date.today)
    data_saida = db.Column(db.Date)
    status = db.Column(db.String(50), default='Ativo')
    active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('funcionario', uselist=False))

    def __repr__(self):
        return f'<Funcionario {self.user.nome}>'

class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    gestor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    descricao = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativo')

    gestor = db.relationship('User', foreign_keys=[gestor_id])
    membros = db.relationship('TeamMember', back_populates='time')


class TeamMember(db.Model):
    __tablename__ = "team_members"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responsabilidade = db.Column(db.String(80))
    status = db.Column(db.String(20), default='ativo')
    data_entrada = db.Column(db.Date)
    data_saida = db.Column(db.Date)

    time = db.relationship('Team', back_populates='membros')
    user = db.relationship('User')

class PromotionLog(db.Model):
    __tablename__ = "promotions_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    cargo_anterior = db.Column(db.String(120), nullable=False)
    salario_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    cargo_novo = db.Column(db.String(120), nullable=False)
    salario_novo = db.Column(db.Numeric(10, 2), nullable=False)
    data_promocao = db.Column(db.Date, nullable=False, default=date.today)
    promovido_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    motivo = db.Column(db.Text)

    employee = db.relationship('Employees', backref='historico_promocoes')
    promovido_por = db.relationship('User')

# Novo modelo para Feedback
class Feedback(db.Model):
    __tablename__ = "feedbacks"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    giver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_feedback = db.Column(db.DateTime, default=datetime.utcnow)
    descricao = db.Column(db.Text, nullable=False)
    kpis = db.Column(JSONB) # Armazenar KPIs como um dicionário JSON
    tipo_feedback = db.Column(db.String(50)) # Ex: "positivo", "construtivo", "avaliação"
    pontuacao_geral = db.Column(db.Numeric(3, 2)) # Pontuação de 0 a 5, por exemplo

    employee = db.relationship('Employees', backref='feedbacks')
    giver = db.relationship('User', foreign_keys=[giver_id])

    def __repr__(self):
        return f'<Feedback {self.id} para {self.employee.user.nome}>'
    
class SalaryAdjustmentLog(db.Model):
    __tablename__ = "salary_adjustments_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    salario_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    salario_novo = db.Column(db.Numeric(10, 2), nullable=False)
    data_ajuste = db.Column(db.Date, nullable=False, default=date.today)
    tipo_ajuste = db.Column(db.String(80), nullable=False)
    motivo = db.Column(db.Text, nullable=True)
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    employee = db.relationship('Employees', backref=db.backref('historico_ajustes', lazy=True))
    aprovado_por = db.relationship('User')

    def __repr__(self):
        return f'<SalaryAdjustmentLog {self.id} - {self.tipo_ajuste}>'