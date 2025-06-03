from flask import Blueprint, render_template
from flask_login import login_required, current_user

gestor_bp = Blueprint('gestor', __name__, url_prefix='/gestor')

@gestor_bp.route("/home")
@login_required
def home():
    return render_template("gestor/home.html", user=current_user)
