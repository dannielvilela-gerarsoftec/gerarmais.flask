from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

parametros_bp = Blueprint('parametros_bp', __name__)

@parametros_bp.route('/parametros', methods=['GET', 'POST'])
def parametros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Corrigido: converte custo de oportunidade e juros diário para decimal
        custo_oportunidade = float(request.form.get('custo_oportunidade', 0) or '0') / 100
        juros_diario = float(request.form.get('juros_diario', 0) or '0') / 100
        cursor.execute("SELECT categoriaID FROM categoria WHERE categoria_tipoID IN (2, 3, 4, 5)")
        categoria_ids = [row['categoriaID'] for row in cursor.fetchall()]
        for categoria_id in categoria_ids:
            cursor.execute("""
                UPDATE parametros SET custo_oportunidade = %s, juros_diario = %s WHERE categoriaID = %s
            """, (custo_oportunidade, juros_diario, categoria_id))
        conn.commit()

        for item in request.form:
            if item.startswith('producao_'):
                categoria_id = item.split('_')[1]
                producao = float(request.form.get(f'producao_{categoria_id}', 0) or '0')
                frete = float(request.form.get(f'frete_{categoria_id}', 0) or '0')
                outros_custos = float(request.form.get(f'outros_custos_{categoria_id}', 0) or '0') / 100
                lucro_desejado = float(request.form.get(f'lucro_desejado_{categoria_id}', 0) or '0') / 100

                cursor.execute("""
                SELECT COUNT(*) AS count FROM parametros WHERE categoriaID = %s
                """, (categoria_id,))
                count_result = cursor.fetchone()

                if count_result['count'] > 0:
                    update_query = """
                    UPDATE parametros SET 
                        producao = %s, 
                        frete = %s, 
                        outros_custos = %s, 
                        lucro_desejado = %s
                    WHERE categoriaID = %s
                    """
                    cursor.execute(update_query, (producao, frete, outros_custos, lucro_desejado, categoria_id))
                else:
                    insert_query = """
                    INSERT INTO parametros (categoriaID, producao, frete, outros_custos, lucro_desejado, custo_oportunidade, juros_diario) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (categoria_id, producao, frete, outros_custos, lucro_desejado, custo_oportunidade, juros_diario))
                conn.commit()

        for item in request.form:
            if item.startswith('pis_'):
                categoria_id = item.split('_')[1]
                pis = float(request.form.get(f'pis_{categoria_id}', 0) or '0') / 100
                cofins = float(request.form.get(f'cofins_{categoria_id}', 0) or '0') / 100
                irpj = float(request.form.get(f'irpj_{categoria_id}', 0) or '0') / 100
                csll = float(request.form.get(f'csll_{categoria_id}', 0) or '0') / 100
                icms = float(request.form.get(f'icms_{categoria_id}', 0) or '0') / 100
                icms_fe = float(request.form.get(f'icms_fe_{categoria_id}', 0) or '0') / 100

                cursor.execute("""
                SELECT COUNT(*) AS count FROM parametros WHERE categoriaID = %s
                """, (categoria_id,))
                count_result = cursor.fetchone()

                if count_result['count'] > 0:
                    update_query = """
                    UPDATE parametros SET 
                        pis = %s, 
                        cofins = %s, 
                        irpj = %s, 
                        csll = %s, 
                        icms = %s,
                        icms_fe = %s
                    WHERE categoriaID = %s
                    """
                    cursor.execute(update_query, (pis, cofins, irpj, csll, icms, icms_fe, categoria_id))
                else:
                    insert_query = """
                    INSERT INTO parametros
                        (categoriaID, pis, cofins, irpj, csll, icms, icms_fe)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (categoria_id, pis, cofins, irpj, csll, icms, icms_fe))
                conn.commit()

        return redirect(url_for('parametros_bp.parametros') + '#impostos')

    cursor.execute("SELECT custo_oportunidade, juros_diario FROM parametros LIMIT 1")
    custo_oportunidade_row = cursor.fetchone()
    custo_oportunidade = custo_oportunidade_row['custo_oportunidade'] if custo_oportunidade_row else 0
    juros_diario = custo_oportunidade_row['juros_diario'] if custo_oportunidade_row else 0

    cursor.execute("""
    SELECT c.categoriaID, c.categoria, p.producao, p.frete, p.outros_custos, p.lucro_desejado
    FROM categoria c
    LEFT JOIN parametros p ON c.categoriaID = p.categoriaID
    WHERE c.categoria_tipoID IN (2, 3, 4, 5)
    ORDER BY c.categoria
    """)
    categorias = cursor.fetchall()

    cursor.execute("""
    SELECT c.categoriaID, c.categoria, p.pis, p.cofins, p.irpj, p.csll, p.icms, p.icms_fe
    FROM categoria c
    LEFT JOIN parametros p ON c.categoriaID = p.categoriaID
    WHERE c.categoria_tipoID IN (2, 3, 4, 5)
    ORDER BY c.categoria
    """)
    impostos = cursor.fetchall()

    cursor.execute("SELECT tipoID, tipo FROM tipo")
    tipos = cursor.fetchall()
    cursor.execute("SELECT unidadeID, unidade, unidade_desc FROM unidades")
    unidades = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'parametros.html',
        categorias=categorias,
        tipos=tipos,
        impostos=impostos,
        unidades=unidades,
        custo_oportunidade=custo_oportunidade,
        juros_diario=juros_diario
    )