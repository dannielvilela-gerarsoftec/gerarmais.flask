from flask import Blueprint, render_template, request, jsonify
from conexao import get_db_connection

lista_produtos_bp = Blueprint('lista_produtos', __name__, url_prefix='/produtos')

@lista_produtos_bp.route('/')
def lista_produtos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categoria WHERE categoria_tipoID NOT IN (1,2)")
    categorias = cursor.fetchall()

    cursor.close()
    conn.close()

    from datetime import datetime
    return render_template('produtos/lista_produtos.html', categorias=categorias, datahora=datetime.now())



@lista_produtos_bp.route('/api')
def lista_produtos_api():
    query_nome = request.args.get('q')
    query_categoria = request.args.get('categoria')
    query_preco = request.args.get('preco', 'de')
    query_tipo = request.args.get('tipo', 'venda')  # novo campo

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql_query = """
        SELECT p.*, c.categoria, u.unidade
        FROM produtos p
        LEFT JOIN categoria c ON p.produto_categoriaID = c.categoriaID
        LEFT JOIN unidades u ON p.produto_unidadeID = u.unidadeID
        WHERE c.categoria_tipoID NOT IN (1,2)
    """
    filtros = []
    params = []

    if query_nome:
        filtros.append("""(
            p.produto_nome LIKE %s OR 
            p.produto_fornecedor LIKE %s OR 
            p.produto_descricao LIKE %s OR 
            c.categoria LIKE %s OR 
            u.unidade LIKE %s
        )""")
        termo = '%' + query_nome + '%'
        params.extend([termo]*5)

    if query_categoria:
        filtros.append("p.produto_categoriaID = %s")
        params.append(query_categoria)

    if filtros:
        sql_query += " AND " + " AND ".join(filtros)

    sql_query += " ORDER BY p.produto_nome ASC"
    cursor.execute(sql_query, params)
    produtos = cursor.fetchall()

    # preço baseado em tipo
    for p in produtos:
        try:
            if query_tipo == 'revenda':
                valor = p.get(f'produto_revenda_{query_preco}')
            else:
                valor = p.get(f'produto_venda_{query_preco}')
            p['preco_venda'] = float(valor) if valor is not None else 0.0
        except (TypeError, ValueError):
            p['preco_venda'] = 0.0

    cursor.close()
    conn.close()
    return jsonify(produtos)

