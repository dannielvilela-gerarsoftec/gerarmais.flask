from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

# Criação do blueprint para gerir as rotas relacionadas a unidades
unidades_bp = Blueprint('unidades_bp', __name__)

@unidades_bp.route('/unidades', methods=['GET', 'POST'])
def unidades():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Recebe os dados do formulário
        unidade = request.form.get('unidade')
        unidade_desc = request.form.get('unidade_desc')
        # Insere a nova unidade e sua descrição no banco de dados
        cursor.execute("INSERT INTO unidades (unidade, unidade_desc) VALUES (%s, %s)", (unidade, unidade_desc))
        conn.commit()

    # Seleciona todas as unidades para exibição
    cursor.execute("SELECT unidadeID, unidade, unidade_desc FROM unidades")
    unidades = cursor.fetchall()

    cursor.close()
    conn.close()

    # Renderiza o template para parâmetros, incluindo unidades
    return render_template('parametros.html', unidades=unidades)

@unidades_bp.route('/adicionar_unidade', methods=['POST'])
def adicionar_unidade():
    unidade = request.form.get('unidade')
    unidade_desc = request.form.get('unidade_desc')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insere a nova unidade na tabela 'unidades' com descrição
    cursor.execute("INSERT INTO unidades (unidade, unidade_desc) VALUES (%s, %s)", (unidade, unidade_desc))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('unidades_bp.unidades'))