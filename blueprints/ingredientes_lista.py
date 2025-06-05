from flask import Blueprint, render_template, request, redirect, url_for, flash
from conexao import get_db_connection

ingredientes_bp = Blueprint('ingredientes_bp', __name__)

# IDs REAIS
IDS_NUTRIENTES_PERCENTUAL = {
    7,   # Umidade
    1,   # Proteína Bruta
    42,  # Nitrogênio
    2,   # NNP Equiv. Proteína
    3,   # NDT
    4,   # Extrato Etéreo
    5,   # Fibra Bruta
    6,   # FDA
    43,  # Matéria Mineral
}

IDS_PROTEINAS_ENERGIAS = [
    7, 1, 42, 2, 3, 4, 5, 6, 43, 1000  # Ajuste 1000 para a 10ª coluna correta
]
IDS_MACROS = [8, 9, 10, 11, 12, 13]
IDS_MICROS = [14, 15, 16, 17, 18, 19, 20, 21, 22]

@ingredientes_bp.route('/ingredientes', methods=['GET', 'POST'])
def lista_ingredientes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, u.unidade
        FROM produtos p
        LEFT JOIN unidades u ON u.unidadeID = p.produto_unidadeID
        WHERE p.produto_tipoID IN (2, 3)
        ORDER BY p.produto_nome
    """)
    ingredientes = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM produtos WHERE produto_tipoID = 1
    """)
    todos_nutrientes = cursor.fetchall()

    def por_ids(ids):
        return [nut for id_ in ids for nut in todos_nutrientes if nut['produtoID'] == id_]

    proteinas_energias = por_ids(IDS_PROTEINAS_ENERGIAS)
    macros = por_ids(IDS_MACROS)
    micros = por_ids(IDS_MICROS)

    cursor.execute("""
        SELECT * FROM produtos 
        WHERE produto_tipoID = 1 AND produto_categoriaID = 12
        ORDER BY produto_nome
    """)
    aditivos = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM ingrediente_nutriente
    """)
    valores_lista = cursor.fetchall()
    ingredientes_valores = {}
    for row in valores_lista:
        ingredientes_valores.setdefault(row['ingredienteID'], {})[row['nutrienteID']] = row['valor']

    cursor.close()
    conn.close()

    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        for ing in ingredientes:
            preco = request.form.get(f'preco_{ing["produtoID"]}', '').replace(',', '.') or None
            perdas = request.form.get(f'perdas_{ing["produtoID"]}', '').replace(',', '.')
            perdas_decimal = float(perdas)/100 if perdas not in (None, '', 'None') else None
            cursor.execute("""
                UPDATE produtos SET produto_custo=%s, produto_perdas=%s WHERE produtoID=%s
            """, (preco, perdas_decimal, ing['produtoID']))
        nutrientes_atualizar = proteinas_energias + macros + micros
        for ing in ingredientes:
            for nut in nutrientes_atualizar + aditivos:
                valor_input = request.form.get(f'val_{ing["produtoID"]}_{nut["produtoID"]}', '').replace(',', '.')
                if valor_input not in ('', None, 'None'):
                    try:
                        valor_float = float(valor_input)
                        if nut['produtoID'] in IDS_NUTRIENTES_PERCENTUAL:
                            valor_float = valor_float / 100.0
                        cursor.execute("""
                            INSERT INTO ingrediente_nutriente (ingredienteID, nutrienteID, valor)
                            VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE valor=VALUES(valor)
                        """, (ing['produtoID'], nut['produtoID'], valor_float))
                    except Exception as e:
                        flash(f"Erro ao salvar valor do ingrediente {ing['produto_nome']} e nutriente {nut['produto_nome']}: {e}", "danger")
                else:
                    cursor.execute("""
                        DELETE FROM ingrediente_nutriente WHERE ingredienteID=%s AND nutrienteID=%s
                    """, (ing['produtoID'], nut['produtoID']))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Dados de ingredientes/nutrientes salvos com sucesso!", "success")
        return redirect(url_for('ingredientes_bp.lista_ingredientes'))

    return render_template(
        'ingredientes_lista.html',
        ingredientes=ingredientes,
        proteinas=proteinas_energias,
        macros=macros,
        micros=micros,
        aditivos=aditivos,
        ingredientes_valores=ingredientes_valores,
        IDS_NUTRIENTES_PERCENTUAL=IDS_NUTRIENTES_PERCENTUAL
    )