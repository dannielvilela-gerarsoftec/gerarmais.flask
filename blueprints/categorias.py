from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

categorias_bp = Blueprint('categorias_bp', __name__)

@categorias_bp.route('/parametros', methods=['GET', 'POST'])
def categorias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        categoria = request.form.get('categoria')
        tipo_categoria = request.form.get('tipo_categoria')
        cursor.execute("INSERT INTO categoria (categoria, categoria_tipoID) VALUES (%s, %s)", (categoria, tipo_categoria))
        conn.commit()

    cursor.execute("SELECT categoriaID, categoria FROM categoria")
    categorias = cursor.fetchall()

    cursor.execute("SELECT tipoID, tipo FROM tipo")
    tipos = cursor.fetchall()

    # Buscar dados para as outras abas, como unidades
    cursor.execute("SELECT unidadeID, unidade, unidade_desc FROM unidades")
    unidades = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('parametros.html', categorias=categorias, tipos=tipos, unidades=unidades)

@categorias_bp.route('/adicionar_categoria', methods=['POST'])
def adicionar_categoria():
    categoria = request.form.get('categoria')
    tipo_categoria = request.form.get('tipo_categoria')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO categoria (categoria, categoria_tipoID) VALUES (%s, %s)", (categoria, tipo_categoria))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('categorias_bp.categorias'))