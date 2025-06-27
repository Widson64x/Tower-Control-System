from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from datetime import date

from app.models import db, User, Team, TeamMember, Employees

times_bp = Blueprint('times', __name__, url_prefix='/times')


# 📜 Listagem de times
@times_bp.route('/')
@login_required
def times_list():
    times = Team.query.all()
    return render_template('gestor/times.html', times=times)


# ➕ Criação de time
@times_bp.route('/criar', methods=['GET', 'POST'])
@login_required
def criar_time():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        gestor_id = request.form.get('gestor_id')

        if not nome or not gestor_id:
            flash('Nome e gestor são obrigatórios.', 'danger')
            return redirect(url_for('times.criar_time'))

        novo_time = Team(
            nome=nome,
            descricao=descricao,
            gestor_id=gestor_id,
            status='ativo'
        )

        db.session.add(novo_time)
        db.session.commit()

        flash('Time criado com sucesso!', 'success')
        return redirect(url_for('times.times_list'))

    gestores = User.query.all()
    return render_template('gestor/criar_time.html', gestores=gestores)


# ➕ Adicionar membro ao time
@times_bp.route('/<int:time_id>/adicionar_membro', methods=['GET', 'POST'])
@login_required
def adicionar_membro(time_id):
    time = Team.query.get_or_404(time_id)

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        responsabilidade = request.form.get('responsabilidade')

        membro_existente = TeamMember.query.filter_by(team_id=time_id, user_id=user_id, status='ativo').first()
        if membro_existente:
            flash('Este funcionário já faz parte do time.', 'warning')
            return redirect(url_for('times.detalhes_time', time_id=time_id))

        novo_membro = TeamMember(
            team_id=time_id,
            user_id=user_id,
            responsabilidade=responsabilidade,
            status='ativo',
            data_entrada=date.today()
        )

        db.session.add(novo_membro)
        db.session.commit()

        flash('Funcionário adicionado ao time!', 'success')
        return redirect(url_for('times.detalhes_time', time_id=time_id))

    # Só mostra funcionários efetivos (employees)
    funcionarios = Employees.query.all()
    return render_template('gestor/adicionar_membro.html', time=time, funcionarios=funcionarios)

# 🧠 Detalhes do time
@times_bp.route('/<int:time_id>/detalhes')
@login_required
def detalhes_time(time_id):
    time = Team.query.get_or_404(time_id)
    return render_template('gestor/detalhes_time.html', time=time)


# ✏️ Editar time
@times_bp.route('/<int:time_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_time(time_id):
    time = Team.query.get_or_404(time_id)

    if request.method == 'POST':
        time.nome = request.form.get('nome')
        time.descricao = request.form.get('descricao')
        time.gestor_id = request.form.get('gestor_id')
        db.session.commit()

        flash('Time atualizado com sucesso!', 'success')
        return redirect(url_for('times.times_list'))

    gestores = User.query.all()
    return render_template('gestor/editar_time.html', time=time, gestores=gestores)


# 🗑️ Deletar time
@times_bp.route('/<int:time_id>/deletar')
@login_required
def deletar_time(time_id):
    time = Team.query.get_or_404(time_id)
    db.session.delete(time)
    db.session.commit()
    flash('Time deletado com sucesso!', 'success')
    return redirect(url_for('times.times_list'))


# 🗑️ Remover membro do time
@times_bp.route('/remover_membro/<int:membro_id>')
@login_required
def remover_membro(membro_id):
    membro = TeamMember.query.get_or_404(membro_id)
    db.session.delete(membro)
    db.session.commit()
    flash('Membro removido do time.', 'success')
    return redirect(url_for('times.detalhes_time', time_id=membro.team_id))