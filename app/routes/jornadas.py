# app/routes/jornadas.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Jornada, JornadaReacao, JornadaComentario, Employees, Team, User
from sqlalchemy.orm import joinedload, subqueryload
from datetime import date

jornadas_bp = Blueprint('jornadas', __name__, url_prefix='/jornada')

@jornadas_bp.route('/')
@login_required
def timeline():
    """ Rota principal que renderiza a página da timeline. """
    return render_template('gestor/jornada_timeline.html')

# (As rotas de adicionar, editar e deletar continuam as mesmas da resposta anterior)
@jornadas_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_jornada():
    """ Rota para criar um novo evento na jornada. """
    if request.method == 'POST':
        nova_jornada = Jornada(
            titulo=request.form.get('titulo'),
            descricao=request.form.get('descricao'),
            data_jornada=date.fromisoformat(request.form.get('data_jornada')),
            tipo=request.form.get('tipo'),
            categoria=request.form.get('categoria'),
            icone=request.form.get('icone'),
            criado_por_id=current_user.id,
            employee_id=int(request.form.get('employee_id')) if request.form.get('employee_id') else None,
            team_id=int(request.form.get('team_id')) if request.form.get('team_id') else None
        )
        db.session.add(nova_jornada)
        db.session.commit()
        flash('Novo marco adicionado à Jornada com sucesso!', 'success')
        return redirect(url_for('jornadas.timeline'))

    # Para o método GET, busca dados para preencher os selects
    employees = db.session.query(Employees).join(User).filter(Employees.active==True).order_by(User.nome).all()
    teams = Team.query.filter_by(status='ativo').order_by(Team.nome).all()
    return render_template('gestor/jornada_form.html',
                           employees=employees,
                           teams=teams,
                           today=date.today().isoformat())

@jornadas_bp.route('/editar/<int:jornada_id>', methods=['GET', 'POST'])
@login_required
def editar_jornada(jornada_id):
    """ Rota para editar um evento existente na jornada. """
    jornada = Jornada.query.get_or_404(jornada_id)

    if request.method == 'POST':
        jornada.titulo = request.form.get('titulo')
        jornada.descricao = request.form.get('descricao')
        jornada.data_jornada = date.fromisoformat(request.form.get('data_jornada'))
        jornada.tipo = request.form.get('tipo')
        jornada.categoria = request.form.get('categoria')
        jornada.icone = request.form.get('icone')
        jornada.employee_id = int(request.form.get('employee_id')) if request.form.get('employee_id') else None
        jornada.team_id = int(request.form.get('team_id')) if request.form.get('team_id') else None
        db.session.commit()
        flash('Marco da Jornada atualizado com sucesso!', 'info')
        return redirect(url_for('jornadas.timeline'))

    employees = db.session.query(Employees).join(User).filter(Employees.active==True).order_by(User.nome).all()
    teams = Team.query.filter_by(status='ativo').order_by(Team.nome).all()
    return render_template('gestor/jornada_form.html',
                           jornada=jornada,
                           employees=employees,
                           teams=teams,
                           today=date.today().isoformat())


@jornadas_bp.route('/deletar/<int:jornada_id>', methods=['POST'])
@login_required
def deletar_jornada(jornada_id):
    """ Rota para deletar um evento da jornada. """
    jornada = Jornada.query.get_or_404(jornada_id)
    # Adicione aqui uma verificação se o usuário tem permissão para deletar
    db.session.delete(jornada)
    db.session.commit()
    flash('Marco da Jornada removido.', 'danger')
    return redirect(url_for('jornadas.timeline'))



# --- ROTAS DA API (PARA O FRONTEND DINÂMICO) ---

@jornadas_bp.route('/api/dados')
@login_required
def api_dados_jornada():
    """ API OTIMIZADA que envia os dados da jornada, agora com filtro por tipo. """
    tipo_filtro = request.args.get('tipo', None) # Pega o parâmetro 'tipo' da URL

    # Query base otimizada
    query = Jornada.query.options(
        joinedload(Jornada.employee).joinedload(Employees.user),
        joinedload(Jornada.time),
        subqueryload(Jornada.reacoes).joinedload(JornadaReacao.usuario),
        subqueryload(Jornada.comentarios).joinedload(JornadaComentario.usuario)
    )

    # Aplica o filtro se ele foi fornecido
    if tipo_filtro:
        query = query.filter(Jornada.tipo == tipo_filtro)
    
    jornadas = query.order_by(Jornada.data_jornada.desc(), Jornada.id.desc()).all()
    
    # O resto da serialização continua igual
    dados_json = []
    for jornada in jornadas:
        reacoes_contagem = {}
        for r in jornada.reacoes:
            reacoes_contagem[r.tipo_reacao] = reacoes_contagem.get(r.tipo_reacao, 0) + 1
        
        user_reacoes = {r.tipo_reacao for r in jornada.reacoes if r.user_id == current_user.id}

        dados_json.append({
            'id': jornada.id,
            'titulo': jornada.titulo,
            'descricao': jornada.descricao,
            'data_jornada': jornada.data_jornada.strftime('%d de %B de %Y'),
            'tipo': jornada.tipo,
            'categoria': jornada.categoria,
            'icone': jornada.icone,
            'employee': jornada.employee.user.nome if jornada.employee and jornada.employee.user else None,
            'team': jornada.time.nome if jornada.time else None,
            'reacoes_contagem': reacoes_contagem,
            'user_reacoes': list(user_reacoes),
            'comentarios': [{'id': c.id, 'texto': c.comentario, 'user': c.usuario.nome, 'data': c.data_comentario.strftime('%d/%m %H:%M')} for c in jornada.comentarios],
        })
    return jsonify(dados_json)


@jornadas_bp.route('/api/reagir', methods=['POST'])
@login_required
def api_reagir():
    """ API para adicionar/remover uma reação. """
    data = request.json
    jornada_id = data.get('jornada_id')
    tipo_reacao = data.get('tipo_reacao')
    
    reacao_existente = JornadaReacao.query.filter_by(user_id=current_user.id, jornada_id=jornada_id, tipo_reacao=tipo_reacao).first()

    if reacao_existente:
        db.session.delete(reacao_existente)
        db.session.commit()
        return jsonify({'status': 'removido'})
    else:
        nova_reacao = JornadaReacao(user_id=current_user.id, jornada_id=jornada_id, tipo_reacao=tipo_reacao)
        db.session.add(nova_reacao)
        db.session.commit()
        return jsonify({'status': 'adicionado'})

@jornadas_bp.route('/api/comentar', methods=['POST'])
@login_required
def api_comentar():
    """ API para adicionar um comentário. """
    data = request.json
    jornada_id = data.get('jornada_id')
    comentario_texto = data.get('comentario')

    if not comentario_texto or not comentario_texto.strip():
        return jsonify({'status': 'erro', 'message': 'Comentário não pode ser vazio.'}), 400

    novo_comentario = JornadaComentario(
        user_id=current_user.id,
        jornada_id=jornada_id,
        comentario=comentario_texto
    )
    db.session.add(novo_comentario)
    db.session.commit()

    return jsonify({
        'status': 'sucesso',
        'comentario': {
            'id': novo_comentario.id,
            'texto': novo_comentario.comentario,
            'user': current_user.nome,
            'data': novo_comentario.data_comentario.strftime('%d/%m %H:%M')
        }
    })