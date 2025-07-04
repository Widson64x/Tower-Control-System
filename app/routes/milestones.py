# app/routes/milestones.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# Importe o modelo User junto com os outros
from app.models import db, Milestone, Employees, Team, User
from datetime import date

milestones_bp = Blueprint('milestones', __name__, url_prefix='/milestones')

@milestones_bp.route('/')
@login_required
def list_milestones():
    milestones = Milestone.query.order_by(Milestone.milestone_date.desc()).all()
    return render_template('gestor/milestones_list.html', milestones=milestones)

@milestones_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_milestone():
    if request.method == 'POST':
        # ... (lógica do POST continua a mesma) ...
        new_milestone = Milestone(
            title=request.form.get('title'),
            description=request.form.get('description'),
            milestone_date=date.fromisoformat(request.form.get('milestone_date')),
            status=request.form.get('status'),
            icon=request.form.get('icon'),
            created_by_id=current_user.id,
            employee_id=int(request.form.get('employee_id')) if request.form.get('employee_id') else None,
            team_id=int(request.form.get('team_id')) if request.form.get('team_id') else None
        )
        db.session.add(new_milestone)
        db.session.commit()
        flash('Marco criado com sucesso!', 'success')
        return redirect(url_for('milestones.list_milestones'))

    # CORREÇÃO AQUI: Use join para ordenar pelo nome do User
    employees = db.session.query(Employees).join(User).filter(Employees.active==True).order_by(User.nome).all()
    teams = Team.query.filter_by(status='ativo').order_by(Team.nome).all()
    
    return render_template('gestor/milestones_form.html',
                           employees=employees,
                           teams=teams,
                           today=date.today().isoformat())

@milestones_bp.route('/edit/<int:milestone_id>', methods=['GET', 'POST'])
@login_required
def edit_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)

    if request.method == 'POST':
        # ... (lógica do POST continua a mesma) ...
        milestone.title = request.form.get('title')
        milestone.description = request.form.get('description')
        milestone.milestone_date = date.fromisoformat(request.form.get('milestone_date'))
        milestone.status = request.form.get('status')
        milestone.icon = request.form.get('icon')
        milestone.employee_id = int(request.form.get('employee_id')) if request.form.get('employee_id') else None
        milestone.team_id = int(request.form.get('team_id')) if request.form.get('team_id') else None
        db.session.commit()
        flash('Marco atualizado com sucesso!', 'info')
        return redirect(url_for('milestones.list_milestones'))

    # CORREÇÃO AQUI TAMBÉM: Use join para ordenar pelo nome do User
    employees = db.session.query(Employees).join(User).filter(Employees.active==True).order_by(User.nome).all()
    teams = Team.query.filter_by(status='ativo').order_by(Team.nome).all()
    
    return render_template('gestor/milestones_form.html',
                           milestone=milestone,
                           employees=employees,
                           teams=teams,
                           today=date.today().isoformat())

# ... (a rota de delete continua a mesma) ...
@milestones_bp.route('/delete/<int:milestone_id>', methods=['POST'])
@login_required
def delete_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    db.session.delete(milestone)
    db.session.commit()
    flash('Marco deletado com sucesso!', 'danger')
    return redirect(url_for('milestones.list_milestones'))