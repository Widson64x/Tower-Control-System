from .extensions import db
from flask_login import UserMixin
from datetime import datetime, date

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    tipo = db.Column(db.String(50), default="colaborador")  
        # Exemplo: "colaborador", "gestor", "analista" etc.
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento 1:1 com Salary (cada usuário tem no máximo 1 salário “fixo”)
    salary = db.relationship('Salary', back_populates='user', uselist=False)

    # Relacionamento 1:N com Bonus (cada usuário pode ter N bonificações)
    bonuses = db.relationship('Bonus', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.email}>"



class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gestor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data = db.Column(db.DateTime, default=db.func.now())
    texto = db.Column(db.Text, nullable=False)
    nota = db.Column(db.Integer, nullable=False, default=5)  # 1 a 5

    user = db.relationship('User', foreign_keys=[user_id])
    gestor = db.relationship('User', foreign_keys=[gestor_id])


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


class Salary(db.Model):
    __tablename__ = "salaries"

    id = db.Column(db.Integer, primary_key=True)

    # Cada salary referencia exatamente um usuário (1:1)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    moeda = db.Column(db.String(3), nullable=False, default='BRL')
    data_inicio = db.Column(db.Date, nullable=False, default=date.today)
    observacao = db.Column(db.String(255), nullable=True)

    # Relacionamento de volta para User
    user = db.relationship('User', back_populates='salary')

    def __repr__(self):
        return f"<Salary user_id={self.user_id} valor={self.valor} {self.moeda}>"


class Bonus(db.Model):
    __tablename__ = "bonuses"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    moeda = db.Column(db.String(3), nullable=False, default='BRL')
    data = db.Column(db.Date, nullable=False, default=date.today)
    motivo = db.Column(db.String(255), nullable=True)
    observacao = db.Column(db.Text, nullable=True)

    # Relacionamento de volta para User
    user = db.relationship('User', back_populates='bonuses')

    def __repr__(self):
        return f"<Bonus user_id={self.user_id} valor={self.valor} {self.moeda} em {self.data}>"