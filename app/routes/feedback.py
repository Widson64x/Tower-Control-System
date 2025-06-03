from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Feedback
from app.extensions import db

feedback_bp = Blueprint('feedback', __name__, url_prefix='/gestor/feedbacks')

@feedback_bp.route("/", methods=["GET"])
@login_required
def feedbacks_list():
    colaboradores = User.query.filter(User.id != current_user.id).all()  # Todos menos eu
    filtro_id = request.args.get('colaborador')
    if filtro_id:
        feedbacks = Feedback.query.filter_by(user_id=filtro_id).order_by(Feedback.data.desc()).all()
    else:
        feedbacks = Feedback.query.order_by(Feedback.data.desc()).all()
    # Pontuação média de cada usuário
    pontuacoes = db.session.query(
        Feedback.user_id,
        db.func.avg(Feedback.nota).label('media'),
        db.func.count(Feedback.id).label('qtd')
    ).group_by(Feedback.user_id).all()
    media_dict = {p.user_id: (float(p.media), int(p.qtd)) for p in pontuacoes}
    return render_template(
        "gestor/feedbacks.html",
        feedbacks=feedbacks,
        colaboradores=colaboradores,
        filtro_id=filtro_id,
        media_dict=media_dict
    )

@feedback_bp.route("/novo", methods=["GET", "POST"])
@login_required
def feedbacks_novo():
    colaboradores = User.query.filter(User.id != current_user.id).all()
    if request.method == "POST":
        user_id = request.form["user_id"]
        texto = request.form["texto"]
        nota = int(request.form.get("nota", 5))
        if not texto.strip():
            flash("O feedback não pode ser vazio!")
            return redirect(url_for("feedback.feedbacks_novo"))
        novo_feedback = Feedback(user_id=user_id, gestor_id=current_user.id, texto=texto, nota=nota)
        db.session.add(novo_feedback)
        db.session.commit()
        flash("Feedback enviado com sucesso!")
        return redirect(url_for("feedback.feedbacks_list"))
    return render_template("gestor/feedback_form.html", colaboradores=colaboradores)
