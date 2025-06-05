from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

tipos_bp = Blueprint('tipos_bp', __name__)

@tipos_bp.route('/tipos', methods=['GET', 'POST'])
def tipos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        cursor.execute("INSERT INTO tipo (tipo) VALUES (%s)", (tipo,))
        conn.commit()

    cursor.execute("SELECT tipoID, tipo FROM tipo")
    tipos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('tipos.html', tipos=tipos)

@tipos_bp.route('/adicionar_tipo', methods=['POST'])
def adicionar_tipo():
    tipo = request.form.get('tipo')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO tipo (tipo) VALUES (%s)", (tipo,))
    conn.commit()

    cursor.close()
    conn.close()

    # Redirecionar para parametros, aba tipos
    return redirect(url_for('parametros_bp.parametros') + '#tipos')