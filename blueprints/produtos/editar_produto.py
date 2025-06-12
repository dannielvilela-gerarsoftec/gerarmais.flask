from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from conexao import get_db_connection
from decimal import Decimal, InvalidOperation
from blueprints.cadastros.cadastro_produto import get_ptax_dia_anterior

editar_produto_bp = Blueprint('editar_produto_bp', __name__)

def sanitize_decimal(value):
    if value in (None, '', ' '):
        return None
    try:
        return Decimal(str(value).replace(',', '.').strip())
    except InvalidOperation:
        return None


def obter_parametros(categoriaID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT pis, cofins, irpj, csll, icms, icms_fe, frete, producao,
               outros_custos, lucro_desejado, lucro_revenda, juros_diario
        FROM parametros
        WHERE categoriaID = %s
    """, (categoriaID,))
    parametros = cursor.fetchone() or {}
    cursor.close()
    conn.close()
    return parametros

def calcular_precificacao(custo, frete, producao, lucro, outros, pis, cofins, irpj, csll, icms):
    custo = Decimal(custo or 0)
    frete = Decimal(frete or 0)
    producao = Decimal(producao or 0)
    outros = Decimal(outros or 0)
    lucro = Decimal(lucro or 0)
    pis = Decimal(pis or 0)
    cofins = Decimal(cofins or 0)
    irpj = Decimal(irpj or 0)
    csll = Decimal(csll or 0)
    icms = Decimal(icms or 0)

    soma_percentuais = lucro + outros + pis + cofins + irpj + csll + icms
    base = 1 - soma_percentuais
    preco_venda = (custo + frete + producao) / base if base != 0 else Decimal(0)
    outros_r = preco_venda * outros
    custo_total = custo + frete + producao + outros_r
    impostos = preco_venda * (pis + cofins + irpj + csll + icms)
    lucro_liquido = preco_venda - custo_total - impostos
    lucro_pct = (lucro_liquido / preco_venda) * 100 if preco_venda else Decimal(0)
    return preco_venda, lucro_liquido, impostos, lucro_pct, custo_total, outros_r

@editar_produto_bp.route('/editar_produto/<int:produtoID>', methods=['GET', 'POST'])
def editar_produto(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM produtos WHERE produtoID = %s", (produtoID,))
    produto = cursor.fetchone()
    if not produto:
        return "Produto não encontrado", 404

    cursor.execute("SELECT * FROM tipo")
    tipos = cursor.fetchall()
    cursor.execute("SELECT * FROM categoria WHERE categoria_tipoID = %s", (produto['produto_tipoID'],))
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM unidades")
    unidades = cursor.fetchall()

    ptax_valor = Decimal(str(get_ptax_dia_anterior()))
    ptax_data = None

    if produto['produto_custo_moeda'] == 'U' and produto['produto_custo_dolar']:
        produto['produto_custo_convertido'] = round(Decimal(produto['produto_custo_dolar']) * Decimal(ptax_valor), 4)
    else:
        produto['produto_custo_convertido'] = produto['produto_custo']

    parametros = obter_parametros(produto['produto_categoriaID'])

    # Buscar juros_diario e custo_oportunidade da categoriaID = 0
    cursor.execute("SELECT juros_diario, custo_oportunidade FROM parametros WHERE categoriaID = 0")
    juros_row = cursor.fetchone()
    juros_diario = float(juros_row.get('juros_diario', 0.001))
    custo_oportunidade = float(juros_row.get('custo_oportunidade', 0))

    frete_ton = Decimal(parametros.get('frete', 0))
    producao_ton = Decimal(parametros.get('producao', 0))
    outros_pct = Decimal(parametros.get('outros_custos', 0))
    lucro_pct = Decimal(parametros.get('lucro_desejado', 0))
    pis = Decimal(parametros.get('pis', 0))
    cofins = Decimal(parametros.get('cofins', 0))
    irpj = Decimal(parametros.get('irpj', 0))
    csll = Decimal(parametros.get('csll', 0))
    icms = Decimal(parametros.get('icms', 0))
    icms_fe = Decimal(parametros.get('icms_fe', 0))
    peso = Decimal(produto.get('produto_peso') or 0)
    custo = Decimal(produto.get('produto_custo') or 0)
    frete = (frete_ton / 1000) * peso
    producao = (producao_ton / 1000) * peso

    def prec(usa_frete, usa_icms):
        return calcular_precificacao(
            custo, frete if usa_frete else 0, producao, lucro_pct, outros_pct,
            pis, cofins, irpj, csll, icms if usa_icms else icms_fe
        )

    precs = {
        'de': prec(False, True),
        'de_fr': prec(True, True),
        'fe': prec(False, False),
        'fe_fr': prec(True, False),
    }

    lucro_revenda_pct = Decimal(parametros.get('lucro_revenda', 0))

    def prec_rev(usa_frete, usa_icms):
        return calcular_precificacao(
            custo, frete if usa_frete else 0, producao, lucro_revenda_pct, outros_pct,
            pis, cofins, irpj, csll, icms if usa_icms else icms_fe
        )

    precs_rev = {
        'de': prec_rev(False, True),
        'de_fr': prec_rev(True, True),
        'fe': prec_rev(False, False),
        'fe_fr': prec_rev(True, False),
    }

    def calc_pagamentos(base):
        base = Decimal(base)
        return {
            'avista': float(base),
            '28': float(base * (Decimal('1') + Decimal(str(juros_diario)) * Decimal('28'))),
            '56': float(base * (Decimal('1') + Decimal(str(juros_diario)) * Decimal('56'))),
            '28_56': float(base * (Decimal('1') + Decimal(str(juros_diario)) * Decimal('42'))),
            '84': float(base * (Decimal('1') + Decimal(str(juros_diario)) * Decimal('84'))),
            '3x': float(base * (Decimal('1') + Decimal(str(juros_diario)) * Decimal('70'))),
        }
 
    tabela_pagamentos_revenda = [
        {'nome': 'Dentro - Sem Frete', **calc_pagamentos(precs_rev['de'][0])},
        {'nome': 'Dentro - Com Frete', **calc_pagamentos(precs_rev['de_fr'][0])},
        {'nome': 'Fora - Sem Frete', **calc_pagamentos(precs_rev['fe'][0])},
        {'nome': 'Fora - Com Frete', **calc_pagamentos(precs_rev['fe_fr'][0])},
    ]

    if request.method == 'POST':
        form = request.form

        produto_nome = form['produto_nome'].strip().upper()
        produto_tipoID = form['produto_tipoID']
        produto_categoriaID = form.get('produto_categoriaID')
        if not produto_categoriaID:
            flash("Erro: Categoria do produto não foi selecionada.", "danger")
            return redirect(request.url)

        produto_descricao = form.get('produto_descricao', '').strip().upper()
        produto_peso = Decimal(form.get('produto_peso', 0))
        produto_validade = form['produto_validade']
        produto_unidadeID = form['produto_unidadeID']
        produto_custo = sanitize_decimal(form.get('produto_custo'))
        produto_custo_moeda = form.get('produto_custo_moeda', 'R')
        produto_custo_dolar = None
        produto_fornecedor = form.get('produto_fornecedor', '').strip().upper()

        if produto_custo_moeda == 'U':
            ptax = get_ptax_dia_anterior()
            produto_custo_dolar = produto_custo
            produto_custo = round(produto_custo_dolar * Decimal(str(ptax)), 4)

        print(">>> POST recebido")
        print("preco_venda_de bruto:", form.get('preco_venda_de'))

        preco_venda_de = sanitize_decimal(form.get('preco_venda_de'))
        preco_venda_de_fr = sanitize_decimal(form.get('preco_venda_de_fr'))
        preco_venda_fe = sanitize_decimal(form.get('preco_venda_fe'))
        preco_venda_fe_fr = sanitize_decimal(form.get('preco_venda_fe_fr'))

        update_query = """
            UPDATE produtos SET 
                produto_nome=%s, produto_tipoID=%s, produto_categoriaID=%s,
                produto_descricao=%s, produto_peso=%s, produto_validade=%s,
                produto_unidadeID=%s, produto_custo=%s, produto_custo_moeda=%s,
                produto_custo_dolar=%s, produto_fornecedor=%s,
                produto_venda_de=%s, produto_venda_de_fr=%s,
                produto_venda_fe=%s, produto_venda_fe_fr=%s
            WHERE produtoID = %s
        """
        cursor.execute(update_query, (
            produto_nome, produto_tipoID, produto_categoriaID, produto_descricao,
            produto_peso, produto_validade, produto_unidadeID, produto_custo,
            produto_custo_moeda, produto_custo_dolar, produto_fornecedor,
            preco_venda_de, preco_venda_de_fr, preco_venda_fe, preco_venda_fe_fr,
            produtoID
        ))
        conn.commit()
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for('editar_produto_bp.editar_produto', produtoID=produtoID))

    tabela_pagamentos = [
        {'nome': 'Dentro - Sem Frete', **calc_pagamentos(Decimal(produto.get('produto_venda_de') or precs['de'][0]))},
        {'nome': 'Dentro - Com Frete', **calc_pagamentos(Decimal(produto.get('produto_venda_de_fr') or precs['de_fr'][0]))},
        {'nome': 'Fora - Sem Frete', **calc_pagamentos(Decimal(produto.get('produto_venda_fe') or precs['fe'][0]))},
        {'nome': 'Fora - Com Frete', **calc_pagamentos(Decimal(produto.get('produto_venda_fe_fr') or precs['fe_fr'][0]))},
        
    ]

    for campo in ['produto_venda_de', 'produto_venda_de_fr', 'produto_venda_fe', 'produto_venda_fe_fr']:
        valor = produto.get(campo)
        produto[campo] = float(valor) if valor is not None else ''

    cursor.close()
    conn.close()

    return render_template(
        'produtos/editar_produto.html',
        produto=produto,
        tipos=tipos,
        categorias=categorias,
        unidades=unidades,
        parametros=parametros,
        custo_frete=frete,
        custo_producao=producao,
        preco_venda_de=float(produto.get('produto_venda_de') or precs['de'][0]),
        preco_venda_de_fr=float(produto.get('produto_venda_de_fr') or precs['de_fr'][0]),
        preco_venda_fe=float(produto.get('produto_venda_fe') or precs['fe'][0]),
        preco_venda_fe_fr=float(produto.get('produto_venda_fe_fr') or precs['fe_fr'][0]),
        pv_de=precs['de'][0], lucro_liquido_de=precs['de'][1], total_impostos_de=precs['de'][2],
        lucro_liquido_percent_de=precs['de'][3], custo_total_de=precs['de'][4], outros_custos_r_de=precs['de'][5],
        pv_de_fr=precs['de_fr'][0], lucro_liquido_de_fr=precs['de_fr'][1], total_impostos_de_fr=precs['de_fr'][2],
        lucro_liquido_percent_de_fr=precs['de_fr'][3], custo_total_de_fr=precs['de_fr'][4], outros_custos_r_de_fr=precs['de_fr'][5],
        pv_fe=precs['fe'][0], lucro_liquido_fe=precs['fe'][1], total_impostos_fe=precs['fe'][2],
        lucro_liquido_percent_fe=precs['fe'][3], custo_total_fe=precs['fe'][4], outros_custos_r_fe=precs['fe'][5],
        pv_fe_fr=precs['fe_fr'][0], lucro_liquido_fe_fr=precs['fe_fr'][1], total_impostos_fe_fr=precs['fe_fr'][2],
        lucro_liquido_percent_fe_fr=precs['fe_fr'][3], custo_total_fe_fr=precs['fe_fr'][4], outros_custos_r_fe_fr=precs['fe_fr'][5],
        tabela_pagamentos=tabela_pagamentos,
        ptax=ptax_valor,
        ptax_data=ptax_data,
        tabela_pagamentos_revenda=tabela_pagamentos_revenda,
        clonar=False
    )

@editar_produto_bp.route('/clonar_produto/<int:produtoID>')
def clonar_produto_view(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos WHERE produtoID = %s", (produtoID,))
    produto = cursor.fetchone()
    if not produto:
        return "Produto não encontrado", 404

    cursor.execute("SELECT * FROM tipo")
    tipos = cursor.fetchall()
    cursor.execute("SELECT * FROM categoria WHERE categoria_tipoID = %s", (produto['produto_tipoID'],))
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM unidades")
    unidades = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'cadastros/cadastro_produto.html',
        produto=produto,
        tipos=tipos,
        categorias=categorias,
        unidades=unidades,
        clonar=True
    )

@editar_produto_bp.route('/excluir_produto/<int:produtoID>', methods=['POST'])
def excluir_produto(produtoID):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE produtoID = %s", (produtoID,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Produto excluído com sucesso!", "success")
    return redirect(url_for('lista_produtos.lista_produtos'))

@editar_produto_bp.route('/categorias_por_tipo/<int:tipo_id>')
def categorias_por_tipo(tipo_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT categoriaID, categoria FROM categoria WHERE categoria_tipoID = %s", (tipo_id,))
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify([
        {'id': c['categoriaID'], 'nome': c['categoria']} for c in categorias
    ])
