from flask import Blueprint, render_template, request, flash, redirect, url_for
from conexao import get_db_connection
from decimal import Decimal, InvalidOperation
import requests
import os
import json
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
    cache_file = "ptax_cache.json"
    hoje = datetime.now().date()

    # Verifica cache local
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            try:
                data = json.load(f)
                if data.get("data") == str(hoje) and data.get("valor"):
                    return float(data["valor"])
            except Exception:
                pass  # Se erro ao ler JSON, ignora e refaz

    # Busca nova cotação (últimos 7 dias úteis)
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
                ptax = float(cotacao['value'][0]['cotacaoVenda'])

                # Salva no cache
                with open(cache_file, 'w') as f:
                    json.dump({
                        "data": str(hoje),
                        "valor": ptax
                    }, f)
                return ptax
        except Exception:
            continue

    raise Exception("Não foi possível obter a cotação do dólar.")

@cadastro_produto_bp.route('/cadastro_produto', methods=['GET', 'POST'])
def cadastro_produto():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tipo")
    tipos = cursor.fetchall()
    cursor.execute("SELECT * FROM categoria")
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM unidades")
    unidades = cursor.fetchall()

    produto = None

    if request.method == 'POST':
        produto = request.form.to_dict()

        try:
            produto_nome = request.form['produto_nome'].strip().upper() or None
            produto_tipoID = request.form['produto_tipoID'].strip() or None
            produto_categoriaID = request.form['produto_categoriaID'].strip() or None
            produto_descricao = request.form['produto_descricao'].strip().upper() or None
            produto_peso = sanitize_decimal(request.form.get('produto_peso', '0'))
            produto_validade = request.form['produto_validade'].strip() or None
            produto_unidadeID = request.form['produto_unidadeID'].strip() or None
            produto_custo = sanitize_decimal(request.form.get('produto_custo', '0'))
            produto_custo_moeda = request.form.get('produto_custo_moeda', 'R')
            produto_fornecedor = request.form['produto_fornecedor'].strip().upper() or None
            produto_custo_dolar = None

            if not all([produto_nome, produto_tipoID, produto_categoriaID, produto_unidadeID]):
                flash("Preencha todos os campos obrigatórios.", "danger")
                raise ValueError("Campos obrigatórios ausentes.")

            if produto_peso is None or produto_custo is None:
                flash("Peso e custo devem ser valores numéricos.", "danger")
                raise ValueError("Peso ou custo inválido.")

            if produto_custo_moeda == 'U':
                ptax = get_ptax_dia_anterior()
                produto_custo_dolar = produto_custo
                produto_custo = round(produto_custo_dolar * Decimal(str(ptax)), 4)

            insert_query = """
                INSERT INTO produtos 
                (produto_nome, produto_tipoID, produto_categoriaID, produto_descricao, produto_peso, produto_validade,
                 produto_unidadeID, produto_custo, produto_custo_moeda, produto_custo_dolar, produto_fornecedor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                produto_nome, produto_tipoID, produto_categoriaID, produto_descricao,
                produto_peso, produto_validade, produto_unidadeID,
                produto_custo, produto_custo_moeda, produto_custo_dolar,
                produto_fornecedor
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
            flash("Erro ao salvar produto: " + str(e), "danger")
            print("Erro ao salvar:", str(e))

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
