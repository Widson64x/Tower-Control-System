from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Salary
from app.extensions import db
from datetime import datetime, date

salary_bp = Blueprint('salary', __name__, url_prefix='/gestor/salarios')

@salary_bp.route("/", methods=["GET"])
@login_required
def salaries_list():
    # Recebe filtros do frontend
    status = request.args.get("status")      # ativo, inativo, ou vazio (todos)
    salario = request.args.get("salario")    # com, sem, ou vazio (todos)
    search = request.args.get("search", "")  # nome ou email

    query = User.query

    if status == "ativo":
        query = query.filter(User.active == True)
    elif status == "inativo":
        query = query.filter(User.active == False)

    if salario == "com":
        query = query.filter(User.salary.has())
    elif salario == "sem":
        query = query.filter(~User.salary.has())

    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                db.func.lower(User.nome).like(like),
                db.func.lower(User.email).like(like)
            )
        )

    usuarios = query.order_by(User.nome).all()
    return render_template("gestor/salaries.html", usuarios=usuarios, status=status, salario=salario, search=search)

@salary_bp.route("/novo", methods=["GET", "POST"])
@login_required
def salary_novo():
    # Só mostra funcionários que ainda NÃO possuem salário cadastrado
    colaboradores = User.query.filter(
        User.id != current_user.id,
        ~User.salary.has(),
        User.active == True  # Somente ativos
    ).all()

    if request.method == "POST":
        user_id = request.form["user_id"]
        valor = float(request.form["valor"])
        moeda = request.form.get("moeda", "BRL")
        data_inicio = request.form.get("data_inicio", date.today())
        # Confirma que não existe salário cadastrado
        if Salary.query.filter_by(user_id=user_id).first():
            flash("Já existe um salário cadastrado para este usuário!")
            return redirect(url_for("salary.salary_novo"))
        novo_salario = Salary(
            user_id=user_id,
            valor=valor,
            moeda=moeda,
            data_inicio=data_inicio,
            gestor_id=current_user.id
        )
        db.session.add(novo_salario)
        db.session.commit()
        flash("Salário cadastrado com sucesso!")
        return redirect(url_for("salary.salaries_list"))
    return render_template("gestor/salary_form.html", colaboradores=colaboradores)
