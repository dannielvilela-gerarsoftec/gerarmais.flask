from flask import Blueprint, render_template, request
from conexao import get_db_connection

# Definindo o blueprint para a lista de produtos
lista_produtos_bp = Blueprint('lista_produtos', __name__, url_prefix='/produtos')

@lista_produtos_bp.route('/')
def lista_produtos():
    query_nome = request.args.get('q')
    query_categoria = request.args.get('categoria')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # FILTRA categorias pelo tipo
    cursor.execute("SELECT * FROM categoria WHERE categoria_tipoID NOT IN (1,2)")
    categorias = cursor.fetchall()

    sql_query = """
        SELECT p.*, c.categoria, pl.juros_diario
        FROM produtos p
        LEFT JOIN categoria c ON p.produto_categoriaID = c.categoriaID
        LEFT JOIN parametros pl ON p.produto_categoriaID = pl.categoriaID
    """
    # Sempre filtrar pelas categorias cujo categoria_tipoID <> 1
    filtros = ["c.categoria_tipoID NOT IN (1,2)"]
    params = []

    if query_nome:
        filtros.append("p.produto_nome LIKE %s")
        params.append('%' + query_nome + '%')

    if query_categoria:
        filtros.append("p.produto_categoriaID = %s")
        params.append(query_categoria)

    if filtros:
        sql_query += " WHERE " + " AND ".join(filtros)
        sql_query += " ORDER BY p.produto_nome ASC"

    cursor.execute(sql_query, params)
    produtos = cursor.fetchall()

    for produto in produtos:
        produto_venda_de = produto.get('produto_venda_de_sf')
        juros_diario = produto.get('juros_diario', 0.001)  # Define o valor padrão para juros

        # Convertendo `None` para 0 se produto_venda_de for assim
        produto_venda_de = float(produto_venda_de) if produto_venda_de is not None else 0

        # Certifica que juros_diario é um número válido
        juros_diario = float(juros_diario) if juros_diario is not None else 0.001

        # Calcula os preços para diferentes métodos de pagamento
        produto['price_avista'] = produto_venda_de
        produto['price_28'] = produto_venda_de + (produto_venda_de * (juros_diario * 28))
        produto['price_56'] = produto_venda_de + (produto_venda_de * (juros_diario * 56))
        produto['price_28_56'] = produto_venda_de + (produto_venda_de * (juros_diario * 42))
        produto['price_84'] = produto_venda_de + (produto_venda_de * (juros_diario * 84))
        produto['price_card_3x'] = produto_venda_de + (produto_venda_de * (juros_diario * 70))

    cursor.close()
    conn.close()
    
    return render_template('produtos/lista_produtos.html', produtos=produtos, categorias=categorias, query_nome=query_nome, query_categoria=query_categoria)