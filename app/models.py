from .extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSONB # Importe JSONB para dados semi-estruturados
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship


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
    
class Milestone(db.Model):
    """
    Modelo para Milestones (Marcos).
    O nome da tabela é 'milestones', mas as colunas estão em português.
    """
    __tablename__ = "milestones"

    # Coluna no DB: 'id'
    id = Column(Integer, primary_key=True)
    
    # Coluna no DB: 'titulo'
    title = Column('titulo', String(150), nullable=False)
    
    # Coluna no DB: 'descricao'
    description = Column('descricao', Text)
    
    # Coluna no DB: 'data_marco'
    milestone_date = Column('data_marco', Date, nullable=False, default=date.today)
    
    # Coluna no DB: 'status'
    status = Column('status', String(50), nullable=False, default='A fazer')
    
    # Coluna no DB: 'icone'
    icon = Column('icone', String(50), default='bi-flag')

    # Chaves Estrangeiras
    created_by_id = Column('criado_por_id', Integer, ForeignKey('users.id'))
    employee_id = Column('employee_id', Integer, ForeignKey('employees.id'))
    team_id = Column('team_id', Integer, ForeignKey('teams.id'))

    # Coluna no DB: 'data_criacao'
    created_at = Column('data_criacao', DateTime, default=datetime.utcnow)

    # Relacionamentos (não criam colunas, apenas facilitam as queries)
    creator = relationship('User', foreign_keys=[created_by_id])
    employee = relationship('Employees', backref='milestones')
    team = relationship('Team', backref='milestones')

    def __repr__(self):
        return f'<Milestone {self.id}: {self.title}>'
    
class Jornada(db.Model):
    __tablename__ = 'journeys'  # <-- ATUALIZADO

    id = Column(Integer, primary_key=True)
    titulo = Column('titulo', String(200), nullable=False)
    descricao = Column('descricao', Text)
    data_jornada = Column('data_jornada', Date, nullable=False, default=date.today)
    tipo = Column('tipo', String(50), nullable=False, default='Individual')
    categoria = Column('categoria', String(50))
    icone = Column('icone', String(50), default='bi-flag')
    cor_card = Column('cor_card', String(30), default='bg-light')
    criado_por_id = Column('criado_por_id', Integer, ForeignKey('users.id'))
    employee_id = Column('employee_id', Integer, ForeignKey('employees.id'))
    team_id = Column('team_id', Integer, ForeignKey('teams.id'))
    data_criacao = Column('data_criacao', DateTime, default=datetime.utcnow)

    # Relacionamentos (nenhuma mudança necessária aqui)
    criador = relationship('User', foreign_keys=[criado_por_id])
    employee = relationship('Employees', backref='jornadas')
    time = relationship('Team', backref='jornadas')
    reacoes = relationship('JornadaReacao', backref='jornada', cascade="all, delete-orphan")
    comentarios = relationship('JornadaComentario', backref='jornada', cascade="all, delete-orphan")

class Conquista(db.Model):
    __tablename__ = 'achievements'  # <-- ATUALIZADO

    id = Column(Integer, primary_key=True)
    nome = Column('nome', String(100), nullable=False, unique=True)
    descricao = Column('descricao', Text, nullable=False)
    icone_emblema = Column('icone_emblema', String(50), nullable=False)
    pontos = Column('pontos', Integer, default=10)

class UsuarioConquista(db.Model):
    __tablename__ = 'user_achievements'  # <-- ATUALIZADO

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
    conquista_id = Column('conquista_id', Integer, ForeignKey('achievements.id'), nullable=False) # Ref atualizada
    jornada_id = Column('jornada_id', Integer, ForeignKey('journeys.id')) # Ref atualizada
    data_desbloqueio = Column('data_desbloqueio', DateTime, default=datetime.utcnow)
    
    usuario = relationship('User', backref='conquistas_ganhas')
    conquista = relationship('Conquista')
    jornada_origem = relationship('Jornada')

class JornadaReacao(db.Model):
    __tablename__ = 'journey_reactions'  # <-- ATUALIZADO

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
    jornada_id = Column('jornada_id', Integer, ForeignKey('journeys.id'), nullable=False) # Ref atualizada
    tipo_reacao = Column('tipo_reacao', String(50), nullable=False)

    usuario = relationship('User')

class JornadaComentario(db.Model):
    __tablename__ = 'journey_comments'  # <-- ATUALIZADO

    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('users.id'), nullable=False)
    jornada_id = Column('jornada_id', Integer, ForeignKey('journeys.id'), nullable=False) # Ref atualizada
    comentario = Column('comentario', Text, nullable=False)
    data_comentario = Column('data_comentario', DateTime, default=datetime.utcnow)

    usuario = relationship('User')