from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from conexao import get_db_connection
from datetime import datetime, timedelta
import requests

precifica_formulacao_bp = Blueprint('precifica_formulacao_bp', __name__)

def get_ptax_dia_anterior():
    hoje = datetime.now()
    for dias in range(1, 8):
        dia = hoje - timedelta(days=dias)
        data_br = dia.strftime('%d/%m/%Y')
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
                valor = float(cotacao['value'][0]['cotacaoVenda'])
                return valor, data_br
        except Exception:
            continue
    raise Exception("Cotação PTAX não encontrada.")

@precifica_formulacao_bp.route('/formulacao/nova', methods=['GET', 'POST'])
def criar_formula():
    return _formulacao_view(edit_mode=False)

@precifica_formulacao_bp.route('/formulacao/<int:ficha_tecnicaID>/editar', methods=['GET', 'POST'])
def editar_formula(ficha_tecnicaID):
    return _formulacao_view(edit_mode=True, ficha_tecnicaID=ficha_tecnicaID)

def _formulacao_view(edit_mode, ficha_tecnicaID=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT produtoID, produto_nome, produto_peso, produto_categoriaID, produto_unidadeID, produto_tipoID FROM produtos WHERE produto_tipoID IN (3,4) ORDER BY produto_nome"
    )
    produtos = cursor.fetchall()
    cursor.execute(
        "SELECT produtoID, produto_nome, produto_categoriaID FROM produtos WHERE produto_tipoID IN (2,3) ORDER BY produto_nome"
    )
    ingredientes = cursor.fetchall()
    cursor.execute(
        "SELECT produtoID, produto_nome, produto_custo FROM produtos WHERE produto_tipoID=6 ORDER BY produto_nome"
    )
    extras = cursor.fetchall()

    ficha, ingredientes_ficha, extras_ficha = None, [], []
    if edit_mode and ficha_tecnicaID:
        cursor.execute("""
            SELECT ficha_tecnicaID, produtoID, ficha_tecnica_nome, ativo, misturador
            FROM ficha_tecnica
            WHERE ficha_tecnicaID = %s
        """, (ficha_tecnicaID,))
        ficha = cursor.fetchone()
        cursor.execute("""
            SELECT fi.produtoID, fi.ficha_tecnica_percentual, fi.ficha_tecnica_quantidade
            FROM ficha_tecnica_itens fi
            WHERE fi.ficha_tecnicaID = %s
            ORDER BY fi.ficha_tecnicaID
        """, (ficha_tecnicaID,))
        ingredientes_ficha = cursor.fetchall()
        cursor.execute("""
            SELECT extraID, produtoID, extra_quantidade
            FROM ficha_tecnica_extras
            WHERE ficha_tecnicaID = %s
            ORDER BY extraID
        """, (ficha_tecnicaID,))
        extras_ficha = cursor.fetchall()

    if request.method == 'POST':
        produtoID = int(request.form.get('produtoID'))
        ficha_tecnica_nome = request.form.get('ficha_tecnica_nome')
        ativo = 1 if request.form.get('ativo') == 'on' else 0
        misturador = float(request.form.get('misturador') or 0)

        # Busca informações do produto para cálculo do peso_sacaria
        cursor.execute("SELECT produto_peso, produto_categoriaID, produto_unidadeID, produto_tipoID FROM produtos WHERE produtoID = %s", (produtoID,))
        prod_row = cursor.fetchone()
        peso_sacaria = float(prod_row['produto_peso']) if prod_row and prod_row['produto_peso'] is not None else 0
        categoria_produto_principal = prod_row['produto_categoriaID'] if prod_row else None
        produto_unidadeID = str(prod_row['produto_unidadeID']) if prod_row else None
        produto_tipoID = int(prod_row['produto_tipoID']) if prod_row else None

        # Verificação de soma dos percentuais
        idx = 0
        soma_percentuais = 0
        while True:
            percentual = request.form.get(f'percentual_{idx}')
            ingrediente = request.form.get(f'ingrediente_{idx}')
            if ingrediente is None or percentual is None or ingrediente == "" or percentual == "":
                break
            soma_percentuais += float(percentual)
            idx += 1
        if abs(soma_percentuais - 100.0) > 0.01:
            flash(f'A soma dos percentuais dos ingredientes deve ser 100%. Soma atual: {soma_percentuais:.4f}%', 'warning')
            conn.close()
            return redirect(request.url)

        if edit_mode and ficha_tecnicaID:
            cursor.execute("""
                UPDATE ficha_tecnica SET 
                    produtoID=%s, ficha_tecnica_nome=%s, ativo=%s, misturador=%s
                WHERE ficha_tecnicaID=%s
            """, (produtoID, ficha_tecnica_nome, ativo, misturador, ficha_tecnicaID))
            cursor.execute("DELETE FROM ficha_tecnica_itens WHERE ficha_tecnicaID=%s", (ficha_tecnicaID,))
            cursor.execute("DELETE FROM ficha_tecnica_extras WHERE ficha_tecnicaID=%s", (ficha_tecnicaID,))
        else:
            cursor.execute("""
                INSERT INTO ficha_tecnica (produtoID, ficha_tecnica_nome, ativo, misturador)
                VALUES (%s, %s, %s, %s)
            """, (produtoID, ficha_tecnica_nome, ativo, misturador))
            ficha_tecnicaID = cursor.lastrowid

        # Salva ingredientes (percentual e peso no saco)
        idx = 0
        while True:
            ingrediente = request.form.get(f'ingrediente_{idx}')
            percentual = request.form.get(f'percentual_{idx}')
            if ingrediente is None or percentual is None or ingrediente == "" or percentual == "":
                break
            percentual = float(percentual)
            peso_saco = peso_sacaria * percentual / 100
            cursor.execute("""
                INSERT INTO ficha_tecnica_itens (ficha_tecnicaID, produtoID, ficha_tecnica_percentual, ficha_tecnica_quantidade)
                VALUES (%s, %s, %s, %s)
            """, (ficha_tecnicaID, int(ingrediente), percentual, peso_saco))
            idx += 1

        # Salva extras
        idx = 0
        while True:
            extra_produto = request.form.get(f'extra_produto_{idx}')
            extra_quantidade = request.form.get(f'extra_quantidade_{idx}')
            if extra_produto is None or extra_quantidade is None or extra_produto == "":
                break
            cursor.execute("""
                INSERT INTO ficha_tecnica_extras (ficha_tecnicaID, produtoID, extra_quantidade)
                VALUES (%s, %s, %s)
            """, (ficha_tecnicaID, int(extra_produto), float(extra_quantidade)))
            idx += 1

        # Cálculo de custos dos ingredientes
        custo_oportunidade = 0.0
        if categoria_produto_principal:
            cursor.execute("SELECT custo_oportunidade FROM parametros WHERE categoriaID=%s", (categoria_produto_principal,))
            param = cursor.fetchone()
            if param and param['custo_oportunidade'] is not None:
                custo_oportunidade = float(param['custo_oportunidade'])

        cursor.execute("""
            SELECT fi.produtoID, fi.ficha_tecnica_percentual, fi.ficha_tecnica_quantidade, 
                   p.produto_custo, p.produto_custo_moeda, p.produto_custo_dolar, p.produto_perdas
            FROM ficha_tecnica_itens fi
            JOIN produtos p ON p.produtoID=fi.produtoID
            WHERE fi.ficha_tecnicaID=%s
        """, (ficha_tecnicaID,))
        ingr_custo = cursor.fetchall()

        try:
            ptax_val, ptax_data = get_ptax_dia_anterior()
        except:
            ptax_val = None

        custo_ingredientes = 0
        for row in ingr_custo:
            percentual = float(row.get("ficha_tecnica_percentual") or 0)
            peso = float(row.get("ficha_tecnica_quantidade") or 0)
            perdas = float(row.get("produto_perdas") or 0)
            peso_com_perda = peso + peso * perdas

            moeda = row.get("produto_custo_moeda") or 'R'
            custo = float(row.get("produto_custo") or 0)
            custo_dolar = float(row.get("produto_custo_dolar") or 0)
            custo_final = custo

            if moeda == 'U' and custo_dolar > 0 and ptax_val:
                convertido = custo_dolar * ptax_val
                custo_final = max(convertido, custo)

            if custo_oportunidade and custo_oportunidade != 0:
                custo_final += (custo_final * custo_oportunidade)

            custo_ingredientes += peso_com_perda * custo_final

        cursor.execute("""
            SELECT fe.produtoID, fe.extra_quantidade, p.produto_custo
            FROM ficha_tecnica_extras fe
            JOIN produtos p ON p.produtoID = fe.produtoID
            WHERE fe.ficha_tecnicaID=%s
        """, (ficha_tecnicaID,))
        extras_custo = cursor.fetchall()
        custo_extras = sum([
            float(row['extra_quantidade']) * float(row['produto_custo'])
            for row in extras_custo
        ])

        custo_total = custo_ingredientes + custo_extras

        # Custo de produção (tipoID == 3)
        custo_producao = 0
        if produto_tipoID == 3:
            cursor.execute("SELECT producao FROM parametros WHERE categoriaID=%s", (categoria_produto_principal or 1,))
            param = cursor.fetchone()
            if param and param.get("producao") is not None:
                producao = float(param["producao"])
                custo_producao = (producao / 1000) * peso_sacaria
                custo_total += custo_producao

        if ativo:
            if produto_unidadeID == "1":  # kg
                if peso_sacaria > 0:
                    custo_unitario = custo_total / peso_sacaria
                    cursor.execute("UPDATE produtos SET produto_custo=%s WHERE produtoID=%s", (custo_unitario, produtoID))
                else:
                    flash("Erro: Peso do produto não pode ser zero para conversão em kg.", "danger")
            elif produto_unidadeID == "3":  # saco/sc
                cursor.execute("UPDATE produtos SET produto_custo=%s WHERE produtoID=%s", (custo_total, produtoID))
            else:
                flash("Altere a unidade do produto para Kg ou Saco antes de salvar! (produto_unidadeID inválido)", "warning")
        else:
            flash("O produto está inativo, portanto o custo NÃO foi atualizado!", "warning")

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('precifica_formulacao_bp.editar_formula', ficha_tecnicaID=ficha_tecnicaID) if edit_mode else url_for('lista_formulacoes_bp.lista_formulacoes'))

    # GET: calcular custo de produção para exibir
    custo_producao = 0
    exibe_custo_producao = False
    if ficha and ficha.get("produtoID"):
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT produto_tipoID, produto_categoriaID, produto_peso FROM produtos WHERE produtoID=%s", (ficha["produtoID"],))
        prod_info = cursor.fetchone()
        if prod_info and int(prod_info["produto_tipoID"]) == 3:
            exibe_custo_producao = True
            cursor.execute("SELECT producao FROM parametros WHERE categoriaID=%s", (prod_info["produto_categoriaID"] or 1,))
            param = cursor.fetchone()
            if param and param.get("producao") is not None:
                producao = float(param["producao"])
                custo_producao = (producao / 1000) * float(prod_info.get("produto_peso") or 0)

    produto_categoriaID = None
    if ficha and ficha.get("produtoID"):
        for p in produtos:
            if p["produtoID"] == ficha["produtoID"]:
                produto_categoriaID = p["produto_categoriaID"]
    elif len(produtos) > 0:
        produto_categoriaID = produtos[0]["produto_categoriaID"]

    cursor.close()
    conn.close()
    return render_template(
        'produtos/precifica_formulacao.html',
        produtos=produtos,
        ingredientes=ingredientes,
        ficha=ficha,
        ingredientes_ficha=ingredientes_ficha,
        extras=extras,
        extras_ficha=extras_ficha,
        edit_mode=edit_mode,
        produto_categoriaID=produto_categoriaID,
        custo_producao=custo_producao if exibe_custo_producao else 0
    )

# ...demais endpoints auxiliares como produto_peso, produto_custo, produto_perda, etc. permanecem iguais.

@precifica_formulacao_bp.route('/formulacao/produto_peso/<int:produtoID>')
def produto_peso(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT produto_peso FROM produtos WHERE produtoID = %s", (produtoID,))
    pesagem = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'produto_peso': pesagem['produto_peso'] if pesagem else 0})

@precifica_formulacao_bp.route('/produtos/custo/<int:produtoID>')
def produto_custo(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT produto_custo, produto_custo_moeda, produto_custo_dolar FROM produtos WHERE produtoID = %s",
        (produtoID,))
    valor = cursor.fetchone()
    cursor.close()
    conn.close()
    if not valor:
        return jsonify({'produto_custo': 0, 'produto_custo_moeda': 'R', 'produto_custo_dolar': 0})
    return jsonify({
        'produto_custo': float(valor['produto_custo']) if valor['produto_custo'] else 0,
        'produto_custo_moeda': valor.get('produto_custo_moeda') or 'R',
        'produto_custo_dolar': float(valor['produto_custo_dolar']) if valor.get('produto_custo_dolar') else 0,
    })

@precifica_formulacao_bp.route('/produtos/perda/<int:produtoID>')
def produto_perda(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT produto_perdas FROM produtos WHERE produtoID = %s", (produtoID,))
    valor = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'produto_perda': float(valor['produto_perdas']) if valor and valor['produto_perdas'] is not None else 0})

@precifica_formulacao_bp.route('/parametros/custo_oportunidade/<int:categoriaID>')
def custo_oportunidade_categoria(categoriaID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT custo_oportunidade FROM parametros WHERE categoriaID = %s", (categoriaID,))
    valor = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'custo_oportunidade': float(valor['custo_oportunidade']) if valor and valor['custo_oportunidade'] is not None else 0})

@precifica_formulacao_bp.route('/ptax')
def ptax():
    try:
        ptax_val, ptax_data = get_ptax_dia_anterior()
        return jsonify({'ptax': ptax_val, 'data': ptax_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500