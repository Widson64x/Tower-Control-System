# app/routes/kpi.py
from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from app.models import db, Employees, PromotionLog, Feedback, User, Team, TeamMember, SalaryAdjustmentLog
from sqlalchemy import func, case, and_ # <-- CORREÇÃO: Adicionado 'case'
from datetime import datetime, timedelta # <-- CORREÇÃO: Adicionado 'timedelta'

kpi_bp = Blueprint('kpi', __name__, url_prefix='/kpis')

# ROTA PRINCIPAL
@kpi_bp.route('/hub')
@login_required
def hub():
    return render_template('kpi/analytics_hub.html')

# =================================================================
# --- API ENDPOINTS ---
# =================================================================

@kpi_bp.route('/api/kpi-summary')
@login_required
def api_kpi_summary():
    active_employees = db.session.query(Employees).filter(Employees.status == 'Ativo')
    headcount = active_employees.count()
    total_payroll = active_employees.with_entities(func.sum(Employees.salario)).scalar() or 0
    
    # CORREÇÃO: A média de diferença de datas retorna um timedelta, que precisa ser tratado
    avg_tenure_delta = active_employees.with_entities(func.avg(datetime.now().date() - Employees.data_entrada)).scalar()
    avg_tenure_months = (avg_tenure_delta.days / 30) if avg_tenure_delta else 0

    avg_feedback = active_employees.with_entities(func.avg(Employees.media_feedbacks)).scalar() or 0

    return jsonify({
        'headcount': {'value': headcount, 'label': 'Colaboradores Ativos'},
        'avg_tenure': {'value': round(avg_tenure_months, 1), 'label': 'Tempo de Casa (Meses)'},
        'total_payroll': {'value': float(total_payroll), 'label': 'Folha Mensal'},
        'avg_feedback': {'value': round(float(avg_feedback), 2), 'label': 'Média de Performance'}
    })

@kpi_bp.route('/api/employee-journey-sankey')
@login_required
def api_employee_journey_sankey():
    sankey_data = []
    promotions = db.session.query(PromotionLog.cargo_anterior, PromotionLog.cargo_novo, func.count(PromotionLog.id))\
        .group_by(PromotionLog.cargo_anterior, PromotionLog.cargo_novo).all()
    for source, target, weight in promotions:
        sankey_data.append([source, target, weight])

    one_year_ago = datetime.now() - timedelta(days=365)
    new_hires = db.session.query(Employees.cargo, func.count(Employees.id))\
        .filter(Employees.data_entrada >= one_year_ago)\
        .group_by(Employees.cargo).all()
    for target, weight in new_hires:
        sankey_data.append(['Contratação', target, weight])
        
    return jsonify(sankey_data)

@kpi_bp.route('/api/performance-distribution-polar')
@login_required
def api_performance_distribution_polar():
    # CORREÇÃO: A função 'case' estava sendo chamada sem ter sido importada
    rating_band_case = case(
        (Employees.media_feedbacks >= 4.5, 'Excelente (4.5+)'),
        (Employees.media_feedbacks >= 3.5, 'Bom (3.5-4.4)'),
        (Employees.media_feedbacks >= 2.5, 'Médio (2.5-3.4)'),
        (Employees.media_feedbacks < 2.5, 'Abaixo (0-2.4)'),
        else_='Sem Nota'
    ).label('rating_band')

    data = db.session.query(
        rating_band_case,
        func.count(Employees.id)
    ).filter(Employees.status == 'Ativo').group_by('rating_band').all()

    return jsonify({
        'series': [d[1] for d in data],
        'labels': [d[0] for d in data]
    })

@kpi_bp.route('/api/feedback-network')
@login_required
def api_feedback_network():
    # Em um modelo real, o nome do recebedor viria de um join com a tabela de usuários
    # Aqui, vamos simular para o gráfico funcionar
    feedbacks = db.session.query(
        User.nome.label('giver_name'),
        Team.nome.label('giver_team'),
        Employees.user.has(User.nome) # Placeholder para a lógica do recebedor
    ).join(Feedback, User.id == Feedback.giver_id)\
     .join(TeamMember, User.id == TeamMember.user_id)\
     .join(Team, TeamMember.team_id == Team.id)\
     .join(Employees, Feedback.employee_id == Employees.id)\
     .limit(50).all() 
    
    nodes = {}
    edges = []
    # A lógica aqui precisaria ser ajustada com o modelo de dados real para o recebedor do feedback
    # Por enquanto, criaremos uma estrutura de exemplo para o gráfico renderizar
    for f in feedbacks:
        if f.giver_name not in nodes:
            nodes[f.giver_name] = {'id': f.giver_name, 'group': f.giver_team}
    
    return jsonify({'nodes': list(nodes.values()), 'edges': []}) # Retorna sem arestas por enquanto