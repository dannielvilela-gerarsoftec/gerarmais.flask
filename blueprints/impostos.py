from flask import Blueprint, render_template, request, redirect, url_for
from conexao import get_db_connection

impostos_bp = Blueprint('impostos_bp', __name__)

@impostos_bp.route('/impostos', methods=['POST'])
def impostos_post():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        for item in request.form:
            if item.startswith('pis_'):
                # Extrair o ID da categoria
                categoria_id = item.split('_')[1]
                pis = float(request.form.get(f'pis_{categoria_id}', 0) or '0') / 100
                cofins = float(request.form.get(f'cofins_{categoria_id}', 0) or '0') / 100
                irpj = float(request.form.get(f'irpj_{categoria_id}', 0) or '0') / 100
                csll = float(request.form.get(f'csll_{categoria_id}', 0) or '0') / 100
                icms = float(request.form.get(f'icms_{categoria_id}', 0) or '0') / 100

                # Verificar se a categoria já existe na tabela parametros
                cursor.execute("SELECT COUNT(*) as count FROM parametros WHERE categoriaID = %s", (categoria_id,))
                count_result = cursor.fetchone()

                if count_result['count'] > 0:
                    # Atualizar valores de imposto no banco de dados
                    update_query = """
                    UPDATE parametros SET 
                        pis = %s, 
                        cofins = %s, 
                        irpj = %s, 
                        csll = %s, 
                        icms = %s
                    WHERE categoriaID = %s
                    """
                    cursor.execute(update_query, (pis, cofins, irpj, csll, icms, categoria_id))
                else:
                    # Inserir nova linha na tabela parametros
                    insert_query = """
                    INSERT INTO parametros (categoriaID, pis, cofins, irpj, csll, icms) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (categoria_id, pis, cofins, irpj, csll, icms))
                conn.commit()

    cursor.close()
    conn.close()
    # Redirecionar para a aba impostos após a edição ser concluída.
    return redirect(url_for('parametros_bp.parametros') + '#impostos')