from flask import Blueprint, render_template
from conexao import get_db_connection

lista_formulacoes_bp = Blueprint('lista_formulacoes_bp', __name__)

@lista_formulacoes_bp.route("/formulacoes", methods=["GET"])
def lista_formulacoes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            f.ficha_tecnicaID, 
            f.ficha_tecnica_nome, 
            f.ativo,
            f.misturador,
            p.produtoID, 
            p.produto_nome, 
            p.produto_peso
        FROM ficha_tecnica f
        JOIN produtos p ON f.produtoID = p.produtoID
        ORDER BY p.produto_nome, f.ficha_tecnica_nome
    """)
    formulacoes = cursor.fetchall()

    for f in formulacoes:
        cursor.execute("""
            SELECT
                fi.produtoID,
                p.produto_nome,
                fi.ficha_tecnica_quantidade
            FROM ficha_tecnica_itens fi
            JOIN produtos p ON fi.produtoID=p.produtoID
            WHERE fi.ficha_tecnicaID = %s
        """, (f['ficha_tecnicaID'],))
        f['ingredientes'] = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("produtos/lista_formulacoes.html", formulacoes=formulacoes)