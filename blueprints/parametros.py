from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

parametros_bp = Blueprint('parametros_bp', __name__)

@parametros_bp.route('/parametros', methods=['GET', 'POST'])
def parametros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        aba = request.form.get('aba')

        if aba == 'custos':
            if 'custo_oportunidade' in request.form and 'juros_diario' in request.form:
                custo_oportunidade = float(request.form.get('custo_oportunidade', 0) or '0') / 100
                juros_diario = float(request.form.get('juros_diario', 0) or '0') / 100
                cursor.execute("""
                    UPDATE parametros SET custo_oportunidade = %s, juros_diario = %s
                    WHERE categoriaID = 0
                """, (custo_oportunidade, juros_diario))

            cursor.execute("SELECT categoriaID FROM categoria WHERE categoria_tipoID IN (2, 3, 4, 5) AND categoriaID != 0")
            categoria_ids = [row['categoriaID'] for row in cursor.fetchall()]
            for categoria_id in categoria_ids:
                producao = float(request.form.get(f'producao_{categoria_id}', 0) or '0')
                frete = float(request.form.get(f'frete_{categoria_id}', 0) or '0')
                outros_custos = float(request.form.get(f'outros_custos_{categoria_id}', 0) or '0') / 100
                lucro_desejado = float(request.form.get(f'lucro_desejado_{categoria_id}', 0) or '0') / 100

                cursor.execute("SELECT COUNT(*) AS count FROM parametros WHERE categoriaID = %s", (categoria_id,))
                count_result = cursor.fetchone()

                if count_result['count'] > 0:
                    cursor.execute("""
                        UPDATE parametros SET producao = %s, frete = %s, outros_custos = %s, lucro_desejado = %s
                        WHERE categoriaID = %s
                    """, (producao, frete, outros_custos, lucro_desejado, categoria_id))
                else:
                    cursor.execute("""
                        INSERT INTO parametros (categoriaID, producao, frete, outros_custos, lucro_desejado, custo_oportunidade, juros_diario)
                        VALUES (%s, %s, %s, %s, %s, 0, 0)
                    """, (categoria_id, producao, frete, outros_custos, lucro_desejado))

        elif aba == 'impostos':
            impostos_padrao = {}
            for campo in ['pis', 'cofins', 'irpj', 'csll', 'icms', 'icms_fe', 'icms_fe_2']:
                impostos_padrao[campo] = float(request.form.get(f'{campo}_0', 0) or '0') / 100

            cursor.execute("""
                UPDATE parametros SET pis = %(pis)s, cofins = %(cofins)s, irpj = %(irpj)s,
                                      csll = %(csll)s, icms = %(icms)s, icms_fe = %(icms_fe)s, icms_fe_2 = %(icms_fe_2)s
                WHERE categoriaID = 0
            """, impostos_padrao)

            cursor.execute("SELECT categoriaID FROM categoria WHERE categoria_tipoID IN (3, 4, 5)")
            ids_impostos = [row['categoriaID'] for row in cursor.fetchall()]

            cursor.execute("SELECT pis, cofins, irpj, csll, icms, icms_fe, icms_fe_2 FROM parametros WHERE categoriaID = 0")
            impostos_ref = cursor.fetchone() or {}

            for categoria_id in ids_impostos:
                cst = request.form.get(f'cst_{categoria_id}', '').strip()
                if not cst:
                    continue

                irpj = impostos_ref['irpj'] if request.form.get(f'irpj_{categoria_id}') else 0
                csll = impostos_ref['csll'] if request.form.get(f'csll_{categoria_id}') else 0
                icms = impostos_ref['icms'] if request.form.get(f'icms_{categoria_id}') else 0
                pis = impostos_ref['pis'] if cst in ['01', '51'] else 0
                cofins = impostos_ref['cofins'] if cst in ['01', '51'] else 0
                icms_fe = impostos_ref['icms_fe'] if request.form.get(f'icms_fe_{categoria_id}') else 0
                icms_fe_2 = impostos_ref['icms_fe_2'] if request.form.get(f'icms_fe_2_{categoria_id}') else 0


                cursor.execute("SELECT COUNT(*) AS count FROM parametros WHERE categoriaID = %s", (categoria_id,))
                count_result = cursor.fetchone()

                if count_result['count'] > 0:
                    cursor.execute("""
                        UPDATE parametros SET cst = %s, irpj = %s, csll = %s, icms = %s,
                                              pis = %s, cofins = %s, icms_fe = %s, icms_fe_2 = %s
                        WHERE categoriaID = %s
                    """, (cst, irpj, csll, icms, pis, cofins, icms_fe, icms_fe_2, categoria_id))

        conn.commit()
        return redirect(url_for('parametros_bp.parametros') + f'#{aba}')

    # --- GET ---
    cursor.execute("SELECT custo_oportunidade, juros_diario FROM parametros WHERE categoriaID = 0")
    row = cursor.fetchone() or {}
    custo_oportunidade = row.get('custo_oportunidade', 0)
    juros_diario = row.get('juros_diario', 0)

    cursor.execute("""
        SELECT c.categoriaID, c.categoria, p.producao, p.frete, p.outros_custos, p.lucro_desejado
        FROM categoria c
        LEFT JOIN parametros p ON c.categoriaID = p.categoriaID
        WHERE c.categoria_tipoID IN (3, 4, 5)
        ORDER BY c.categoria
    """)
    categorias = cursor.fetchall()

    cursor.execute("""
        SELECT c.categoriaID, c.categoria, p.pis, p.cofins, p.irpj, p.csll, p.icms, p.icms_fe, p.icms_fe_2, p.cst
        FROM categoria c
        LEFT JOIN parametros p ON c.categoriaID = p.categoriaID
        WHERE c.categoria_tipoID IN (3, 4, 5)
        ORDER BY c.categoria
    """)
    impostos = cursor.fetchall()

    cursor.execute("SELECT tipoID, tipo FROM tipo")
    tipos = cursor.fetchall()

    cursor.execute("SELECT unidadeID, unidade, unidade_desc FROM unidades")
    unidades = cursor.fetchall()

    cursor.execute("""
        SELECT pis, cofins, irpj, csll, icms, icms_fe, icms_fe_2
        FROM parametros
        WHERE categoriaID = 0
    """)
    impostos_padrao = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'parametros.html',
        categorias=categorias,
        tipos=tipos,
        impostos=impostos,
        unidades=unidades,
        custo_oportunidade=custo_oportunidade,
        juros_diario=juros_diario,
        impostos_padrao=impostos_padrao
    )
