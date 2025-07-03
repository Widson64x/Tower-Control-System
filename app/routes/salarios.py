from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, User, Employees, SalaryAdjustmentLog, PromotionLog
from datetime import date
from decimal import Decimal

salarios_bp = Blueprint('salarios', __name__, url_prefix='/salarios')

@salarios_bp.route('/')
@login_required
def index():
    # ❗ CORREÇÃO: Lista apenas funcionários ativos.
    funcionarios = db.session.query(Employees).join(User).filter(Employees.active == True).order_by(User.nome).all()
    return render_template('salarios/lista_funcionarios.html', funcionarios=funcionarios)

@salarios_bp.route('/painel/<int:employee_id>')
@login_required
def painel_financeiro(employee_id):
    employee = Employees.query.get_or_404(employee_id)

    # ❗ VALIDAÇÃO: Impede o acesso ao painel de funcionário inativo.
    if not employee.active:
        flash('Não é possível acessar o painel de um funcionário inativo.', 'danger')
        return redirect(url_for('salarios.index'))

    promocoes = PromotionLog.query.filter_by(employee_id=employee.id).all()
    ajustes = SalaryAdjustmentLog.query.filter_by(employee_id=employee.id).all()
    
    linha_do_tempo = []
    # ... (lógica da linha do tempo continua a mesma)
    for p in promocoes:
        linha_do_tempo.append({
            'data': p.data_promocao,
            'evento': f'Promoção para {p.novo_cargo}',
            'salario_anterior': p.salario_anterior,
            'salario_novo': p.salario_novo,
            'motivo': p.motivo
        })

    for a in ajustes:
        linha_do_tempo.append({
            'data': a.data_ajuste,
            'evento': f'Ajuste por {a.tipo_ajuste}',
            'salario_anterior': a.salario_anterior,
            'salario_novo': a.salario_novo,
            'motivo': a.motivo
        })

    linha_do_tempo.sort(key=lambda x: x['data'], reverse=True)
    
    eventos_ordenados_grafico = sorted(linha_do_tempo, key=lambda x: x['data'])
    chart_labels = [item['data'].strftime('%d/%m/%Y') for item in eventos_ordenados_grafico]
    chart_data = [float(item['salario_novo']) for item in eventos_ordenados_grafico]

    return render_template('salarios/painel_financeiro.html',
                           employee=employee,
                           linha_do_tempo=linha_do_tempo,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@salarios_bp.route('/ajuste/novo/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def novo_ajuste(employee_id):
    employee = Employees.query.get_or_404(employee_id)

    # ❗ VALIDAÇÃO: Impede ajuste salarial para funcionário inativo.
    if not employee.active:
        flash('Não é possível fazer ajuste salarial para um funcionário inativo.', 'danger')
        return redirect(url_for('salarios.index'))

    if request.method == 'POST':
        # ... (lógica do POST continua a mesma)
        novo_salario_str = request.form.get('novo_salario')
        tipo_ajuste = request.form.get('tipo_ajuste')
        motivo = request.form.get('motivo')
        data_ajuste_str = request.form.get('data_ajuste')

        if not all([novo_salario_str, tipo_ajuste, data_ajuste_str]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'warning')
            return redirect(url_for('salarios.novo_ajuste', employee_id=employee.id))

        try:
            salario_anterior = employee.salario
            novo_salario = Decimal(novo_salario_str.replace('.', '').replace(',', '.'))
            data_ajuste = date.fromisoformat(data_ajuste_str)

            novo_log = SalaryAdjustmentLog(
                employee_id=employee.id,
                salario_anterior=salario_anterior,
                salario_novo=novo_salario,
                data_ajuste=data_ajuste,
                tipo_ajuste=tipo_ajuste,
                motivo=motivo,
                aprovado_por_id=current_user.id
            )
            db.session.add(novo_log)

            employee.salario = novo_salario
            db.session.commit()
            
            flash(f'Ajuste salarial para {employee.user.nome} registrado com sucesso!', 'success')
            return redirect(url_for('salarios.painel_financeiro', employee_id=employee.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar o ajuste: {e}', 'danger')

    return render_template('salarios/novo_ajuste.html', employee=employee, hoje=date.today().isoformat())