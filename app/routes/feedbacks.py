from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Employees, Feedback, User
from app.extensions import db
from datetime import datetime
import json

feedbacks_bp = Blueprint('feedbacks', __name__, url_prefix='/feedbacks')

@feedbacks_bp.route('/')
@login_required
def dashboard_feedbacks():
    # ❗ CORREÇÃO: Lista apenas funcionários ativos.
    funcionarios_ordenados = Employees.query.filter_by(active=True).order_by(Employees.media_feedbacks.desc()).all()
    return render_template('gestor/dashboard_feedbacks.html', funcionarios=funcionarios_ordenados)

@feedbacks_bp.route('/funcionario/<int:employee_id>')
@login_required
def ver_feedbacks_funcionario(employee_id):
    funcionario = Employees.query.get_or_404(employee_id)

    # ❗ VALIDAÇÃO: Impede a visualização de feedbacks de funcionário inativo.
    if not funcionario.active:
        flash('Não é possível visualizar feedbacks de um funcionário inativo.', 'danger')
        return redirect(url_for('feedbacks.dashboard_feedbacks'))

    feedbacks_recebidos = Feedback.query.filter_by(employee_id=employee_id).order_by(Feedback.data_feedback.desc()).all()
    media_feedbacks_funcionario = db.session.query(db.func.avg(Feedback.pontuacao_geral)).filter(Feedback.employee_id == employee_id).scalar()
    
    return render_template('gestor/ver_feedbacks_funcionario.html',
                           funcionario=funcionario,
                           feedbacks=feedbacks_recebidos,
                           media_feedbacks=media_feedbacks_funcionario)

@feedbacks_bp.route('/dar/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def dar_feedback(employee_id):
    funcionario_alvo = Employees.query.get_or_404(employee_id)

    # ❗ VALIDAÇÃO: Impede dar feedback para funcionário inativo.
    if not funcionario_alvo.active:
        flash('Não é possível dar feedback para um funcionário inativo.', 'danger')
        return redirect(url_for('feedbacks.dashboard_feedbacks'))
    
    # ... (o resto da função permanece o mesmo)
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        tipo_feedback = request.form.get('tipo_feedback')
        pontuacao_str = request.form.get('pontuacao_geral')
        
        if not descricao:
            flash('A descrição do feedback é obrigatória.', 'danger')
            return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))
        
        try:
            pontuacao_geral = float(pontuacao_str)
            if not (0 <= pontuacao_geral <= 5):
                raise ValueError
        except (ValueError, TypeError):
            flash('A pontuação geral deve ser um número entre 0 e 5.', 'danger')
            return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))

        kpis_data = {"qualidades": {}, "defeitos": {}}
        
        qualidade_nomes = request.form.getlist('kpi_qualidade_nome[]')
        qualidade_niveis = request.form.getlist('kpi_qualidade_nivel[]')
        
        for i in range(len(qualidade_nomes)):
            nome = qualidade_nomes[i].strip()
            nivel_str = qualidade_niveis[i].strip()
            if nome and nivel_str:
                try:
                    nivel = float(nivel_str)
                    if not (0 <= nivel <= 5):
                        flash(f"Nível inválido para a qualidade '{nome}'. Deve ser entre 0 e 5.", 'danger')
                        return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))
                    kpis_data["qualidades"][nome] = nivel
                except (ValueError, TypeError):
                    flash(f"Nível inválido para a qualidade '{nome}'. Deve ser um número.", 'danger')
                    return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))

        defeito_nomes = request.form.getlist('kpi_defeito_nome[]')
        defeito_niveis = request.form.getlist('kpi_defeito_nivel[]')

        for i in range(len(defeito_nomes)):
            nome = defeito_nomes[i].strip()
            nivel_str = defeito_niveis[i].strip()
            if nome and nivel_str:
                try:
                    nivel = float(nivel_str)
                    if not (0 <= nivel <= 5):
                        flash(f"Nível inválido para o defeito '{nome}'. Deve ser entre 0 e 5.", 'danger')
                        return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))
                    kpis_data["defeitos"][nome] = nivel
                except (ValueError, TypeError):
                    flash(f"Nível inválido para o defeito '{nome}'. Deve ser um número.", 'danger')
                    return redirect(url_for('feedbacks.dar_feedback', employee_id=employee_id))
        
        if not kpis_data["qualidades"] and not kpis_data["defeitos"]:
            kpis_to_save = None
        else:
            kpis_to_save = kpis_data

        novo_feedback = Feedback(
            employee_id=funcionario_alvo.id,
            giver_id=current_user.id,
            descricao=descricao,
            tipo_feedback=tipo_feedback,
            pontuacao_geral=pontuacao_geral,
            kpis=kpis_to_save
        )

        db.session.add(novo_feedback)
        db.session.commit()

        media_atualizada = db.session.query(db.func.avg(Feedback.pontuacao_geral)).filter(Feedback.employee_id == funcionario_alvo.id).scalar()
        if media_atualizada is not None:
            funcionario_alvo.media_feedbacks = media_atualizada
        else:
            funcionario_alvo.media_feedbacks = 0.0
            
        db.session.commit()
        
        flash(f'Feedback para {funcionario_alvo.user.nome} registrado com sucesso!', 'success')
        return redirect(url_for('feedbacks.ver_feedbacks_funcionario', employee_id=employee_id))

    return render_template('gestor/dar_feedback.html', funcionario=funcionario_alvo)

# --- Rota para editar um feedback (AJUSTADA PARA KPIS DINÂMICOS) ---
@feedbacks_bp.route('/editar/<int:feedback_id>', methods=['GET', 'POST'])
@login_required
def editar_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)

    if feedback.giver_id != current_user.id and current_user.tipo != 'administrador':
        flash('Você não tem permissão para editar este feedback.', 'danger')
        return redirect(url_for('feedbacks.ver_feedbacks_funcionario', employee_id=feedback.employee_id))

    if request.method == 'POST':
        feedback.descricao = request.form.get('descricao')
        feedback.tipo_feedback = request.form.get('tipo_feedback')
        
        pontuacao_str = request.form.get('pontuacao_geral')
        try:
            pontuacao_geral = float(pontuacao_str)
            if not (0 <= pontuacao_geral <= 5):
                raise ValueError
            feedback.pontuacao_geral = pontuacao_geral
        except (ValueError, TypeError):
            flash('A pontuação geral deve ser um número entre 0 e 5.', 'danger')
            return redirect(url_for('feedbacks.editar_feedback', feedback_id=feedback_id))

        # --- PROCESSAMENTO DOS KPIS DINÂMICOS NA EDIÇÃO ---
        kpis_data = {"qualidades": {}, "defeitos": {}}
        
        # Coleta os dados de qualidades
        qualidade_nomes = request.form.getlist('kpi_qualidade_nome[]')
        qualidade_niveis = request.form.getlist('kpi_qualidade_nivel[]')
        
        for i in range(len(qualidade_nomes)):
            nome = qualidade_nomes[i].strip()
            nivel_str = qualidade_niveis[i].strip()
            if nome and nivel_str:
                try:
                    nivel = float(nivel_str)
                    if not (0 <= nivel <= 5):
                        flash(f"Nível inválido para a qualidade '{nome}'. Deve ser entre 0 e 5.", 'danger')
                        return redirect(url_for('feedbacks.editar_feedback', feedback_id=feedback_id))
                    kpis_data["qualidades"][nome] = nivel
                except (ValueError, TypeError):
                    flash(f"Nível inválido para a qualidade '{nome}'. Deve ser um número.", 'danger')
                    return redirect(url_for('feedbacks.editar_feedback', feedback_id=feedback_id))

        # Coleta os dados de defeitos
        defeito_nomes = request.form.getlist('kpi_defeito_nome[]')
        defeito_niveis = request.form.getlist('kpi_defeito_nivel[]')

        for i in range(len(defeito_nomes)):
            nome = defeito_nomes[i].strip()
            nivel_str = defeito_niveis[i].strip()
            if nome and nivel_str:
                try:
                    nivel = float(nivel_str)
                    if not (0 <= nivel <= 5):
                        flash(f"Nível inválido para o defeito '{nome}'. Deve ser entre 0 e 5.", 'danger')
                        return redirect(url_for('feedbacks.editar_feedback', feedback_id=feedback_id))
                    kpis_data["defeitos"][nome] = nivel
                except (ValueError, TypeError):
                    flash(f"Nível inválido para o defeito '{nome}'. Deve ser um número.", 'danger')
                    return redirect(url_for('feedbacks.editar_feedback', feedback_id=feedback_id))
        
        if not kpis_data["qualidades"] and not kpis_data["defeitos"]:
            feedback.kpis = None
        else:
            feedback.kpis = kpis_data
        # ------------------------------------------

        db.session.commit()
        
        media_atualizada = db.session.query(db.func.avg(Feedback.pontuacao_geral))\
                                    .filter(Feedback.employee_id == feedback.employee_id)\
                                    .scalar()
        if media_atualizada is not None:
            feedback.employee.media_feedbacks = media_atualizada
        else:
            feedback.employee.media_feedbacks = 0.0
        db.session.commit()

        flash('Feedback atualizado com sucesso!', 'success')
        return redirect(url_for('feedbacks.ver_feedbacks_funcionario', employee_id=feedback.employee.id))
    
    # Para o GET request, prepare os dados para preencher o formulário dinâmico
    # O template de edição usará estas listas para recriar os campos dinâmicos
    qualidades_existentes = feedback.kpis.get('qualidades', {}) if feedback.kpis else {}
    defeitos_existentes = feedback.kpis.get('defeitos', {}) if feedback.kpis else {}

    return render_template('gestor/editar_feedback.html', 
                           feedback=feedback,
                           qualidades_existentes=qualidades_existentes,
                           defeitos_existentes=defeitos_existentes)

# --- Rota para deletar um feedback ---
@feedbacks_bp.route('/deletar/<int:feedback_id>', methods=['POST'])
@login_required
def deletar_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    employee_id = feedback.employee_id

    if feedback.giver_id != current_user.id and current_user.tipo != 'administrador':
        flash('Você não tem permissão para deletar este feedback.', 'danger')
        return redirect(url_for('feedbacks.ver_feedbacks_funcionario', employee_id=employee_id))
    
    db.session.delete(feedback)
    db.session.commit()

    media_atualizada = db.session.query(db.func.avg(Feedback.pontuacao_geral))\
                                .filter(Feedback.employee_id == employee_id)\
                                .scalar()
    funcionario = Employees.query.get(employee_id)
    if funcionario:
        if media_atualizada is not None:
            funcionario.media_feedbacks = media_atualizada
        else:
            funcionario.media_feedbacks = 0.0
        db.session.commit()

    flash('Feedback deletado com sucesso!', 'success')
    return redirect(url_for('feedbacks.ver_feedbacks_funcionario', employee_id=employee_id))