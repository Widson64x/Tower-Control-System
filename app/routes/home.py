# app/routes/home.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

home_bp = Blueprint('home', __name__, url_prefix='/home')

@home_bp.route("/") # Alterado para /home/ sem subdiretório redundante
@login_required
def home():
    # Verifica o tipo de usuário e redireciona para o dashboard apropriado
    if current_user.tipo == "Admin":
        return render_template("gestor/home.html", user=current_user)
    elif current_user.tipo == "Usuário": # Assumindo que o tipo para usuários limitados é "Usuário"
        return render_template("usuario/home.html", user=current_user)
    else:
        # Caso haja outros tipos ou um tipo não reconhecido, pode-se redirecionar
        # para uma página de erro ou uma página genérica
        # Por exemplo, para o logout ou uma página de acesso negado
        flash("Seu tipo de usuário não tem acesso a esta página diretamente. Por favor, entre em contato com o suporte.", "warning")
        return redirect(url_for("auth.logout"))