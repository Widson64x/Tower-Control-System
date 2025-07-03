# app/routes/salarios.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, User, Employees, SalaryAdjustmentLog, PromotionLog
from datetime import date
from decimal import Decimal

salarios_bp = Blueprint('salarios', __name__, url_prefix='/salarios')

@salarios_bp.route('/')
@login_required
def index():
    """Lista todos os funcionários para acesso ao painel financeiro."""
    # CORREÇÃO: Adicionado join com User para ordenar por nome.
    funcionarios = db.session.query(Employees).join(User).order_by(User.nome).all()
    return render_template('salarios/lista_funcionarios.html', funcionarios=funcionarios)

@salarios_bp.route('/painel/<int:employee_id>')
@login_required
def painel_financeiro(employee_id):
    """Exibe o painel financeiro detalhado de um funcionário."""
    employee = Employees.query.get_or_404(employee_id)

    promocoes = PromotionLog.query.filter_by(employee_id=employee.id).all()
    ajustes = SalaryAdjustmentLog.query.filter_by(employee_id=employee.id).all()

    # Unifica os eventos em uma única linha do tempo
    linha_do_tempo = []
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

    # Ordena a linha do tempo pela data, do mais recente para o mais antigo
    linha_do_tempo.sort(key=lambda x: x['data'], reverse=True)

    # Prepara dados para o gráfico (ordenado do mais antigo para o mais recente)
    eventos_ordenados_grafico = sorted(linha_do_tempo, key=lambda x: x['data'])
    chart_labels = [item['data'].strftime('%d/%m/%Y') for item in eventos_ordenados_grafico]
    chart_data = [float(item['salario_novo']) for item in eventos_ordenados_grafico]

    return render_template(
        'salarios/painel_financeiro.html',
        employee=employee,
        linha_do_tempo=linha_do_tempo,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

@salarios_bp.route('/ajuste/novo/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def novo_ajuste(employee_id):
    """Página para adicionar um novo ajuste salarial."""
    employee = Employees.query.get_or_404(employee_id)

    if request.method == 'POST':
        novo_salario_str = request.form.get('novo_salario')
        tipo_ajuste = request.form.get('tipo_ajuste')
        motivo = request.form.get('motivo')
        data_ajuste_str = request.form.get('data_ajuste')

        if not all([novo_salario_str, tipo_ajuste, data_ajuste_str]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'warning')
            return redirect(url_for('salarios.novo_ajuste', employee_id=employee.id))

        try:
            salario_anterior = employee.salario
            # Converte para Decimal de forma segura
            novo_salario = Decimal(novo_salario_str.replace('.', '').replace(',', '.'))
            data_ajuste = date.fromisoformat(data_ajuste_str)

            # Cria o log
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

            # Atualiza o salário atual do funcionário
            employee.salario = novo_salario

            db.session.commit()
            flash(f'Ajuste salarial para {employee.user.nome} registrado com sucesso!', 'success')
            return redirect(url_for('salarios.painel_financeiro', employee_id=employee.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar o ajuste: {e}', 'danger')


    return render_template('salarios/novo_ajuste.html', employee=employee, hoje=date.today().isoformat())