# app/routes/kpi.py
from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from app.models import db, Employees, PromotionLog, Team, TeamMember, User
from sqlalchemy import func, case, and_, extract
from datetime import datetime, timedelta

kpi_bp = Blueprint('kpi', __name__, url_prefix='/kpis')

# =================================================================
# ROTA PRINCIPAL DO HUB
# =================================================================

@kpi_bp.route('/hub')
@login_required
def hub():
    """Renderiza a página principal do dashboard de análise."""
    return render_template('kpi/analytics_hub.html')

# =================================================================
# --- ENDPOINTS DA API 100% BASEADOS NO SEU MODEL.PY ---
# =================================================================

# -----------------------------------------------------------------
# KPI 1: MÉTRICAS VITAIS (OS GRANDES NÚMEROS)
# -----------------------------------------------------------------
@kpi_bp.route('/api/vital-metrics')
@login_required
def api_vital_metrics():
    """Fornece os principais indicadores numéricos da empresa."""
    active_employees_query = db.session.query(Employees).filter(Employees.status == 'Ativo')
    headcount = active_employees_query.count()
    
    one_year_ago = datetime.now().date() - timedelta(days=365)

    # CORREÇÃO: Usando TeamMember.data_saida para o cálculo de turnover.
    terminations_last_12m = db.session.query(TeamMember).filter(
        TeamMember.data_saida >= one_year_ago
    ).count()

    # Headcount médio: (Headcount atual + Headcount 1 ano atrás) / 2
    headcount_12m_ago_query = db.session.query(Employees).filter(Employees.data_entrada < one_year_ago)
    active_at_that_time = headcount_12m_ago_query.filter(
        (Employees.status == 'Ativo') | 
        (db.session.query(TeamMember.id).filter(
            TeamMember.user_id == Employees.user_id,
            TeamMember.data_saida >= one_year_ago
        ).exists())
    ).count()

    avg_headcount_last_12m = (headcount + active_at_that_time) / 2 if (headcount + active_at_that_time) > 0 else 0
    turnover_rate = (terminations_last_12m / avg_headcount_last_12m) * 100 if avg_headcount_last_12m > 0 else 0

    total_payroll = active_employees_query.with_entities(func.sum(Employees.salario)).scalar() or 0
    avg_tenure_delta = active_employees_query.with_entities(func.avg(func.current_date() - Employees.data_entrada)).scalar()
    avg_tenure_months = (avg_tenure_delta.days / 30) if avg_tenure_delta else 0

    return jsonify({
        'headcount': {'value': headcount, 'label': 'Colaboradores Ativos'},
        'turnover_rate': {'value': f"{turnover_rate:.1f}%", 'label': 'Turnover Anual'},
        'avg_tenure': {'value': f"{avg_tenure_months:.1f}", 'label': 'Tempo de Casa (Meses)'},
        'total_payroll': {'value': float(total_payroll), 'label': 'Folha Mensal'}
    })

# -----------------------------------------------------------------
# KPI 2: JORNADA DO COLABORADOR (FLUXO DE TALENTOS)
# -----------------------------------------------------------------
@kpi_bp.route('/api/employee-journey-sankey')
@login_required
def api_employee_journey_sankey():
    """Cria dados para um gráfico Sankey mostrando o ciclo de vida completo."""
    sankey_data = []
    one_year_ago = datetime.now().date() - timedelta(days=365)
    
    # 1. Fluxo de Promoções
    promotions = db.session.query(
        PromotionLog.cargo_anterior, PromotionLog.cargo_novo, func.count(PromotionLog.id)
    ).filter(PromotionLog.data_promocao >= one_year_ago).group_by(PromotionLog.cargo_anterior, PromotionLog.cargo_novo).all()
    for source, target, weight in promotions:
        sankey_data.append([str(source), str(target), weight])

    # 2. Fluxo de Novas Contratações
    new_hires = db.session.query(
        Employees.cargo, func.count(Employees.id)
    ).filter(Employees.data_entrada >= one_year_ago).group_by(Employees.cargo).all()
    for target, weight in new_hires:
        sankey_data.append(['Contratação', str(target), weight])

    # 3. CORREÇÃO: Fluxo de Desligamentos usando TeamMember.data_saida
    terminations = db.session.query(
        Employees.cargo, func.count(Employees.id)
    ).join(User, Employees.user_id == User.id)\
     .join(TeamMember, User.id == TeamMember.user_id)\
     .filter(TeamMember.data_saida >= one_year_ago)\
     .group_by(Employees.cargo).all()
    for source, weight in terminations:
        sankey_data.append([str(source), 'Desligamento', weight])
        
    return jsonify(sankey_data)

# -----------------------------------------------------------------
# KPI 3: DISTRIBUIÇÃO DE PERFORMANCE
# -----------------------------------------------------------------
@kpi_bp.route('/api/performance-distribution')
@login_required
def api_performance_distribution():
    """Agrupa os colaboradores por faixa de performance."""
    rating_band_case = case(
        (Employees.media_feedbacks >= 4.5, 'Excelente'),
        (Employees.media_feedbacks >= 3.5, 'Bom'),
        (Employees.media_feedbacks >= 2.5, 'Médio'),
        (Employees.media_feedbacks < 2.5, 'Abaixo da Média'),
        else_='Sem Avaliação'
    ).label('rating_band')

    data = db.session.query(
        rating_band_case, func.count(Employees.id)
    ).filter(Employees.status == 'Ativo').group_by('rating_band').order_by(rating_band_case).all()

    return jsonify({'series': [d[1] for d in data], 'labels': [d[0] for d in data]})

# -----------------------------------------------------------------
# KPI 4: FLUXO DE PESSOAL (CONTRATAÇÕES VS. DESLIGAMENTOS)
# -----------------------------------------------------------------
@kpi_bp.route('/api/headcount-flow')
@login_required
def api_headcount_flow():
    """Fornece dados mensais de contratações e desligamentos."""
    labels, hires_data, terminations_data = [], [], []

    for i in range(5, -1, -1):
        target_date = datetime.now().date() - timedelta(days=i * 30)
        month, year = target_date.month, target_date.year
        labels.append(target_date.strftime("%b/%y"))

        # CORREÇÃO: Usando TeamMember.data_entrada para contratações.
        hires_count = db.session.query(func.count(TeamMember.id)).filter(
            extract('month', TeamMember.data_entrada) == month,
            extract('year', TeamMember.data_entrada) == year
        ).scalar()
        
        # CORREÇÃO: Usando TeamMember.data_saida para desligamentos.
        terminations_count = db.session.query(func.count(TeamMember.id)).filter(
            extract('month', TeamMember.data_saida) == month,
            extract('year', TeamMember.data_saida) == year
        ).scalar()

        hires_data.append(hires_count)
        terminations_data.append(terminations_count)

    return jsonify({
        'labels': labels,
        'series': [
            {'name': 'Contratações', 'data': hires_data},
            {'name': 'Desligamentos', 'data': terminations_data}
        ]
    })

# -----------------------------------------------------------------
# KPI 5: PERFORMANCE MÉDIA POR EQUIPE
# -----------------------------------------------------------------
@kpi_bp.route('/api/performance-by-team')
@login_required
def api_performance_by_team():
    """Calcula a média de performance para cada equipe."""
    query = db.session.query(
        Team.nome, func.avg(Employees.media_feedbacks)
    ).join(TeamMember, Team.id == TeamMember.team_id)\
     .join(User, TeamMember.user_id == User.id)\
     .join(Employees, User.id == Employees.user_id)\
     .filter(Employees.status == 'Ativo', TeamMember.status == 'ativo')\
     .group_by(Team.nome)\
     .order_by(func.avg(Employees.media_feedbacks).desc())\
     .all()

    return jsonify({
        'series': [{'data': [round(float(d[1] or 0), 2) for d in query]}],
        'labels': [d[0] for d in query]
    })