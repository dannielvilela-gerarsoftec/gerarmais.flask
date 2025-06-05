from flask import Blueprint, render_template, request, flash, redirect, url_for
from conexao import get_db_connection
from decimal import Decimal, InvalidOperation
import requests
from datetime import datetime, timedelta

cadastro_produto_bp = Blueprint('cadastro_produto_bp', __name__)

def sanitize_decimal(value):
    if not value:
        return None
    try:
        value = value.replace(',', '.').strip()
        return Decimal(value)
    except InvalidOperation:
        return None

def get_ptax_dia_anterior():
    hoje = datetime.now()
    for dias in range(1, 8):
        dia = hoje - timedelta(days=dias)
        data_api = dia.strftime('%m-%d-%Y')
        url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
            f"@dataInicial='{data_api}'&@dataFinalCotacao='{data_api}'&$top=1&$format=json"
        )
        try:
            r = requests.get(url, timeout=5)
            cotacao = r.json()
            if cotacao['value']:
                return float(cotacao['value'][0]['cotacaoVenda'])
        except Exception:
            continue
    raise Exception("Não foi possível obter a cotação do dólar.")

@cadastro_produto_bp.route('/cadastro_produto', methods=['GET', 'POST'])
def cadastro_produto():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Preenche os selects independentemente do método
    cursor.execute("SELECT * FROM tipo")
    tipos = cursor.fetchall()
    cursor.execute("SELECT * FROM categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM unidades")
    unidades = cursor.fetchall()

    produto = None  # usado para repopular campos em caso de erro

    if request.method == 'POST':
        produto = request.form.to_dict()  # Captura os dados preenchidos para repopular

        try:
            produto_nome = request.form['produto_nome'].strip().upper() or None
            produto_tipoID = request.form['produto_tipoID'].strip() or None
            produto_categoriaID = request.form['produto_categoriaID'].strip() or None
            produto_descricao = request.form['produto_descricao'].strip().upper() or None
            produto_peso = sanitize_decimal(request.form.get('produto_peso', '0'))
            produto_validade = request.form['produto_validade'].strip() or None
            produto_unidadeID = request.form['produto_unidadeID'].strip() or None
            produto_custo = sanitize_decimal(request.form.get('produto_custo', '0'))
            produto_fornecedor = request.form['produto_fornecedor'].strip().upper() or None

            if not all([produto_nome, produto_tipoID, produto_categoriaID, produto_unidadeID]):
                flash("Preencha todos os campos obrigatórios.", "danger")
                raise ValueError("Campos obrigatórios ausentes.")

            if produto_peso is None or produto_custo is None:
                flash("Peso e custo devem ser valores numéricos.", "danger")
                raise ValueError("Peso ou custo inválido.")

            insert_query = """
                INSERT INTO produtos 
                (produto_nome, produto_tipoID, produto_categoriaID, produto_descricao, produto_peso, produto_validade,
                 produto_unidadeID, produto_custo, produto_fornecedor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                produto_nome, produto_tipoID, produto_categoriaID, produto_descricao,
                produto_peso, produto_validade, produto_unidadeID, produto_custo, produto_fornecedor
            ))
            conn.commit()
            produto_id = cursor.lastrowid
            return render_template(
                'cadastros/cadastro_produto.html',
                produto=None,
                tipos=tipos,
                categorias=categorias,
                unidades=unidades,
                clonar=False,
                produto_cadastrado=True,
                produto_id=produto_id
            )


        except Exception as e:
            # Já mostramos o flash acima quando necessário
            print("Erro ao salvar:", str(e))  # Útil no log/terminal

    cursor.close()
    conn.close()

    return render_template(
        'cadastros/cadastro_produto.html',
        tipos=tipos,
        categorias=categorias,
        unidades=unidades,
        produto=produto,
        clonar=False
    )
