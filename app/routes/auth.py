from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash # Importe generate_password_hash
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route("login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email") # Use .get() para evitar KeyError
        senha = request.form.get("senha") # Use .get() para evitar KeyError
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            flash("Login realizado com sucesso!", "success") # Adicionado categoria de flash
            return redirect(url_for("home.home"))
        else:
            flash("Email ou senha incorretos!", "danger") # Adicionado categoria de flash
    return render_template("login.html")

@auth_bp.route("register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        # Validações Básicas
        if not nome or not email or not senha or not confirmar_senha:
            flash("Todos os campos são obrigatórios!", "danger")
            return render_template("register.html", nome=nome, email=email) # Mantém dados no formulário
        
        if senha != confirmar_senha:
            flash("As senhas não coincidem!", "danger")
            return render_template("register.html", nome=nome, email=email)
        
        if len(senha) < 6: # Exemplo de validação de senha
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("register.html", nome=nome, email=email)

        # Verificar se o email já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Este email já está registrado. Por favor, use outro.", "danger")
            return render_template("register.html", nome=nome) # Não pré-preenche email para segurança

        # Criar hash da senha
        senha_hash = generate_password_hash(senha)

        # Criar novo usuário
        new_user = User(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            tipo="Usuário" # Definindo um tipo padrão para novos registros
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registro realizado com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro ao registrar: {str(e)}", "danger")

    return render_template("register.html")

@auth_bp.route("logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado(a) com sucesso.", "info") # Adicionado categoria de flash
    return redirect(url_for("auth.login"))