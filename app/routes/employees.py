from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app.models import User, Employees, TeamMember
from app.extensions import db
from datetime import date

funcionarios_bp = Blueprint('funcionarios', __name__, url_prefix='/funcionarios')

def parse_salario(valor_str):
    """
    Converte 'R$X.XXX,XX' -> float(Xxxx.xx)
    """
    valor_str = valor_str.strip().replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(valor_str)
    except ValueError:
        return None

@funcionarios_bp.route('/')
@login_required
def lista_funcionarios():
    funcionarios = Employees.query.all()
    return render_template('gestor/funcionarios.html', funcionarios=funcionarios)

@funcionarios_bp.route('/demitir/<int:funcionario_id>', methods=['POST'])
@login_required
def demitir_funcionario(funcionario_id):
    funcionario = Employees.query.get_or_404(funcionario_id)

    funcionario.active = False
    funcionario.status = 'Demitido'

    # Atualiza os registros na tabela team_members
    membros = TeamMember.query.filter_by(user_id=funcionario.user_id, status='ativo').all()
    for membro in membros:
        membro.status = 'inativo'
        membro.data_saida = date.today()

    db.session.commit()

    flash('Funcionário demitido com sucesso! Ele também foi removido dos times.', 'success')
    return redirect(url_for('funcionarios.lista_funcionarios'))

@funcionarios_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_funcionario():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        cargo = request.form.get('cargo')
        salario_str = request.form.get('salario')
        data_entrada_str = request.form.get('data_entrada')

        salario = parse_salario(salario_str)

        if salario is None:
            flash('Formato de salário inválido.', 'danger')
            return redirect(url_for('funcionarios.adicionar_funcionario'))

        user = User.query.get(user_id)
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('funcionarios.adicionar_funcionario'))

        try:
            data_entrada = date.fromisoformat(data_entrada_str)
        except Exception:
            flash('Data de entrada inválida.', 'danger')
            return redirect(url_for('funcionarios.adicionar_funcionario'))

        funcionario_existente = Employees.query.filter_by(user_id=user_id).first()

        if funcionario_existente:
            if funcionario_existente.active:
                flash('Este usuário já é um funcionário ativo.', 'warning')
                return redirect(url_for('funcionarios.lista_funcionarios'))
            else:
                # Reativar funcionário inativo
                funcionario_existente.cargo = cargo
                funcionario_existente.salario = salario
                funcionario_existente.data_entrada = data_entrada
                funcionario_existente.active = True
                funcionario_existente.status = 'Ativo'

                db.session.commit()
                flash('Funcionário reativado com sucesso!', 'success')
                return redirect(url_for('funcionarios.lista_funcionarios'))

        # Criar novo funcionário
        novo_funcionario = Employees(
            user_id=user_id,
            cargo=cargo,
            salario=salario,
            data_entrada=data_entrada,
            active=True
        )

        db.session.add(novo_funcionario)
        db.session.commit()

        flash('Funcionário adicionado com sucesso!', 'success')
        return redirect(url_for('funcionarios.lista_funcionarios'))

    usuarios = User.query.all()
    return render_template('gestor/adicionar_funcionario.html', usuarios=usuarios)
