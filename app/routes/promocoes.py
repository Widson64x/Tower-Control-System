from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import date
from app.models import Employees, PromotionLog
from app.extensions import db

promocoes_bp = Blueprint('promocoes', __name__, url_prefix='/promocoes')

def parse_salario(valor_str):
    """
    Converte 'R$X.XXX,XX' -> float(Xxxx.xx)
    """
    valor_str = valor_str.strip().replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return None
    
# 🔥 Tela para listar funcionários e promover
@promocoes_bp.route('/')
@login_required
def lista_funcionarios():
    funcionarios = Employees.query.all()
    return render_template('gestor/promocoes.html', funcionarios=funcionarios)

# ✨ Rota de promover funcionário
@promocoes_bp.route('/<int:funcionario_id>/promover', methods=['GET', 'POST'])
@login_required
def promover_funcionario(funcionario_id):
    funcionario = Employees.query.get_or_404(funcionario_id)

    if request.method == 'POST':
        novo_cargo = request.form.get('cargo')
        novo_salario_str = request.form.get('salario')
        motivo = request.form.get('motivo')

        # Conversão de salário
        novo_salario = parse_salario(novo_salario_str)
        if novo_salario is None:
            flash('Formato de salário inválido. Use o formato "1234,56".', 'danger')
            return redirect(url_for('promocoes.promover_funcionario', funcionario_id=funcionario_id))

        # VALIDAÇÃO: Garante que o novo salário é maior que o atual
        if novo_salario <= funcionario.salario:
            # -------------------------------------------------------------------- #
            # ✨ CORREÇÃO APLICADA AQUI ✨
            # Formata o salário atual para exibição (funciona com float e Decimal)
            # -------------------------------------------------------------------- #
            salario_formatado_temp = format(funcionario.salario, ",.2f")
            # Troca '.' por ',' e ',' por '.' de forma segura
            salario_atual_formatado = salario_formatado_temp.replace(',', 'X').replace('.', ',').replace('X', '.')
            
            flash(f'Erro: O novo salário ({novo_salario_str}) deve ser maior que o salário atual (R$ {salario_atual_formatado}).', 'danger')
            return redirect(url_for('promocoes.promover_funcionario', funcionario_id=funcionario_id))
        
        # Se a validação passou, continua com o registro...
        promocao = PromotionLog(
            employee_id=funcionario.id,
            cargo_anterior=funcionario.cargo,
            salario_anterior=funcionario.salario,
            cargo_novo=novo_cargo,
            salario_novo=novo_salario,
            data_promocao=date.today(),
            promovido_por_id=current_user.id,
            motivo=motivo
        )

        funcionario.cargo = novo_cargo
        funcionario.salario = novo_salario

        db.session.add(promocao)
        db.session.commit()

        flash('Funcionário promovido com sucesso!', 'success')
        return redirect(url_for('promocoes.lista_funcionarios'))

    return render_template('gestor/promover_funcionario.html', funcionario=funcionario)