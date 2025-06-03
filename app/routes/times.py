from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Team, TeamMember, User
from app.extensions import db

times_bp = Blueprint('times', __name__, url_prefix='/gestor/times')

@times_bp.route("/")
@login_required
def times_list():
    times = Team.query.all()
    return render_template("gestor/times.html", times=times)

@times_bp.route("/novo", methods=["GET", "POST"])
@login_required
def times_novo():
    gestores = User.query.all()
    if request.method == "POST":
        nome = request.form["nome"]
        gestor_id = request.form["gestor_id"]
        descricao = request.form.get("descricao", "")
        novo_time = Team(nome=nome, gestor_id=gestor_id, descricao=descricao)
        db.session.add(novo_time)
        db.session.commit()
        flash("Time criado com sucesso!")
        return redirect(url_for("times.times_list"))
    return render_template("gestor/time_form.html", gestores=gestores)

@times_bp.route("/<int:time_id>", methods=["GET", "POST"])
@login_required
def times_detalhe(time_id):
    time = Team.query.get_or_404(time_id)
    membros = TeamMember.query.filter_by(team_id=time_id, status='ativo').all()
    users = User.query.all()
    if request.method == "POST":
        # Editar informações do time
        time.nome = request.form["nome"]
        time.gestor_id = request.form["gestor_id"]
        time.descricao = request.form.get("descricao", "")
        db.session.commit()
        flash("Time atualizado com sucesso!")
        return redirect(url_for("times.times_detalhe", time_id=time_id))
    return render_template("gestor/time_detalhe.html", time=time, membros=membros, users=users)

@times_bp.route("/<int:time_id>/excluir", methods=["POST"])
@login_required
def times_apagar(time_id):
    time = Team.query.get_or_404(time_id)
    db.session.delete(time)
    db.session.commit()
    flash("Time excluído!")
    return redirect(url_for("times.times_list"))

@times_bp.route("/<int:time_id>/membro/novo", methods=["POST"])
@login_required
def times_add_membro(time_id):
    user_id = request.form["user_id"]
    responsabilidade = request.form["responsabilidade"]
    membro = TeamMember(team_id=time_id, user_id=user_id, responsabilidade=responsabilidade, data_entrada=db.func.now())
    db.session.add(membro)
    db.session.commit()
    flash("Membro adicionado ao time!")
    return redirect(url_for("times.times_detalhe", time_id=time_id))

@times_bp.route("/<int:time_id>/membro/<int:membro_id>/editar", methods=["POST"])
@login_required
def times_editar_membro(time_id, membro_id):
    membro = TeamMember.query.get_or_404(membro_id)
    membro.responsabilidade = request.form["responsabilidade"]
    db.session.commit()
    flash("Função atualizada!")
    return redirect(url_for("times.times_detalhe", time_id=time_id))

@times_bp.route("/<int:time_id>/membro/<int:membro_id>/excluir", methods=["POST"])
@login_required
def times_remover_membro(time_id, membro_id):
    membro = TeamMember.query.get_or_404(membro_id)
    db.session.delete(membro)
    db.session.commit()
    flash("Membro removido do time!")
    return redirect(url_for("times.times_detalhe", time_id=time_id))
