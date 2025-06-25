from flask import Blueprint, render_template, request, flash
from datetime import datetime
from decimal import Decimal
from conexao import get_db_connection

tabela_precos_bp = Blueprint('tabela_precos_bp', __name__, url_prefix='/relatorios')

def ficha_tecnica_detalhada(produto_id, cursor):
    # 1 - Buscar ficha técnica ativa
    cursor.execute("SELECT * FROM ficha_tecnica WHERE produtoID = %s AND ativo = 1", (produto_id,))
    fichas_ativas = cursor.fetchall()
    if not fichas_ativas:
        return {'erro': 'Não há ficha técnica ativa para este produto!'}
    if len(fichas_ativas) > 1:
        return {'erro': 'Mais de uma ficha técnica ativa encontrada! Ajuste na Lista de Formulações.'}
    ficha = fichas_ativas[0]
    ficha_tecnicaID = ficha['ficha_tecnicaID']

    # 2 - Ingredientes
    cursor.execute("SELECT * FROM ficha_tecnica_itens WHERE ficha_tecnicaID = %s", (ficha_tecnicaID,))
    ingredientes_raw = cursor.fetchall()
    ingredientes = []
    total_ingred = 0
    for item in ingredientes_raw:
        cursor.execute("SELECT produto_nome, produto_custo, produto_perdas FROM produtos WHERE produtoID = %s", (item["produtoID"],))
        prod = cursor.fetchone()
        if prod:
            quantidade = float(item.get('ficha_tecnica_quantidade', 0) or item.get('quantidade', 0) or 0)
            custo_unit = float(prod['produto_custo'] or 0)
            perda_pct = float(prod.get('produto_perdas') or 0)
            perda_kg = quantidade * perda_pct
            quantidade_com_perda = quantidade + perda_kg
            custo_total = quantidade_com_perda * custo_unit
            total_ingred += custo_total
            ingredientes.append({
                "nome": prod["produto_nome"],
                "quantidade": quantidade,
                "perda_kg": perda_kg,
                "custo_unit": custo_unit,
                "custo_total": custo_total
            })
    # 3 - Extras
    cursor.execute("SELECT * FROM ficha_tecnica_extras WHERE ficha_tecnicaID = %s", (ficha_tecnicaID,))
    extras_raw = cursor.fetchall()
    extras = []
    total_extras = 0
    for ex in extras_raw:
        cursor.execute("SELECT produto_nome, produto_custo FROM produtos WHERE produtoID = %s", (ex["produtoID"],))
        prod = cursor.fetchone()
        if prod:
            qtd = float(ex.get('extra_quantidade', 0) or ex.get('quantidade', 0) or 0)
            custo_unit = float(prod["produto_custo"] or 0)
            custo_total = qtd * custo_unit
            total_extras += custo_total
            extras.append({
                "nome": prod["produto_nome"],
                "quantidade": qtd,
                "custo_unit": custo_unit,
                "custo_total": custo_total
            })
    return {
        "ingredientes": ingredientes,
        "extras": extras,
        "total_ingredientes": total_ingred,
        "total_extras": total_extras,
        "custo_total": total_ingred + total_extras
    }

def gerar_tabela_preco(
    tipos, categorias, produtos_filtrados,
    frete_opcao, frete_manual, dentro_fora, modo_preco
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    resultados = {}
    datahora_geracao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    for cat_id in categorias:
        cursor.execute("""
            SELECT p.*, c.categoria, c.categoria_tipoID
            FROM produtos p
            JOIN categoria c ON c.categoriaID = p.produto_categoriaID
            WHERE c.categoriaID = %s AND c.categoria_tipoID NOT IN (1,2)
            ORDER BY p.produto_nome ASC
        """, (cat_id,))
        produtos = cursor.fetchall()
        if not produtos:
            continue

        nome_cat = produtos[0]['categoria']
        resultados[nome_cat] = []

        for produto in produtos:
            if produtos_filtrados and str(produto['produtoID']) not in produtos_filtrados:
                continue

            detalhamento_ficha = None
            erro_ficha = None

            if modo_preco == 'atualizar' and produto['categoria_tipoID'] in (3, 4):
                detalhamento_ficha = ficha_tecnica_detalhada(produto['produtoID'], cursor)
                if 'erro' in detalhamento_ficha:
                    erro_ficha = detalhamento_ficha['erro']
                    detalhamento_ficha = None

            categoria_tipoID = produto['categoria_tipoID']
            if modo_preco == 'atualizar' and categoria_tipoID in (3, 4):
                custo = detalhamento_ficha['custo_total'] if detalhamento_ficha else 0
            else:
                custo = float(produto['produto_custo'] or 0)

            try:
                from precifica_formulacao import get_ptax_dia_anterior
            except Exception:
                get_ptax_dia_anterior = None

            moeda = produto.get('produto_custo_moeda') or 'R'
            custo_dolar = float(produto.get('produto_custo_dolar') or 0)
            msg_dolar = ""

            if modo_preco == 'atualizar' and moeda == 'U' and custo_dolar > 0 and categoria_tipoID not in (3, 4):
                try:
                    ptax_val, ptax_data = get_ptax_dia_anterior() if get_ptax_dia_anterior else (None, None)
                except Exception:
                    ptax_val, ptax_data = (None, None)
                if ptax_val:
                    convertido = custo_dolar * ptax_val
                    if convertido > custo:
                        custo = convertido
                        msg_dolar = f"Conversão pelo PTAX {ptax_val:.2f} ({ptax_data})."
                    else:
                        msg_dolar = "Usado custo em real (maior que valor convertido pelo dólar/PTAX)."
                else:
                    msg_dolar = "Não foi possível obter PTAX."

            peso = float(produto.get('produto_peso') or 0)
            if frete_opcao == 'bd':
                cursor.execute(
                    "SELECT frete FROM parametros WHERE categoriaID = %s",
                    (produto['produto_categoriaID'],)
                )
                param = cursor.fetchone()
                frete_r_ton = float(param.get('frete') or 0) if param else 0
            elif frete_opcao == 'manual':
                frete_r_ton = float(frete_manual or 0)
            else:
                frete_r_ton = 0
            custo_frete = (frete_r_ton / 1000) * peso

            cursor.execute("""
                SELECT producao, outros_custos, lucro_desejado, pis, cofins, irpj, csll, icms, icms_fe
                FROM parametros WHERE categoriaID = %s
            """, (produto['produto_categoriaID'],))
            param = cursor.fetchone() or {}

            cursor.execute("SELECT juros_diario FROM parametros WHERE categoriaID = 0")
            param_geral = cursor.fetchone()
            juros_diarios = float(param_geral.get('juros_diario') or 0.001)

            producao_ton      = float(param.get('producao') or 0)
            outros_custos_pct = float(param.get('outros_custos') or 0)
            lucro_desejado    = float(param.get('lucro_desejado') or 0)
            pis               = float(param.get('pis') or 0)
            cofins            = float(param.get('cofins') or 0)
            irpj              = float(param.get('irpj') or 0)
            csll              = float(param.get('csll') or 0)
            icms              = float(param.get('icms') or 0)
            icms_fe           = float(param.get('icms_fe') or 0)

            custo_producao = (producao_ton / 1000) * peso
            incluir_icms_fe = (dentro_fora == 'fora')

            if modo_preco == "atualizar":
                def calcular_precificacao(produto_custo, custo_producao, lucro_desejado, outros_custos_percent,
                                          pis, cofins, irpj, csll, icms, icms_fe, incluir_icms_fe):
                    produto_custo = Decimal(produto_custo or 0)
                    custo_producao = Decimal(custo_producao or 0)
                    outros_custos_percent = Decimal(outros_custos_percent or 0)
                    lucro_desejado = Decimal(lucro_desejado or 0)
                    pis = Decimal(pis or 0)
                    cofins = Decimal(cofins or 0)
                    irpj = Decimal(irpj or 0)
                    csll = Decimal(csll or 0)
                    icms = Decimal(icms or 0)
                    icms_fe = Decimal(icms_fe) if incluir_icms_fe else Decimal(0)
                    soma_percentuais = (lucro_desejado + outros_custos_percent + pis + cofins +
                                        irpj + csll + icms + icms_fe)
                    base = Decimal(1) - soma_percentuais
                    preco_venda = Decimal(0)
                    if base != 0:
                        preco_venda = (produto_custo + custo_producao) / base
                    return float(preco_venda)

                preco_venda_base = calcular_precificacao(
                    custo, custo_producao, lucro_desejado, outros_custos_pct,
                    pis, cofins, irpj, csll, icms, icms_fe, incluir_icms_fe
                )
            else:
                if dentro_fora == 'dentro':
                    preco_venda_base = float(produto.get('produto_venda_de') or 0)
                else:
                    preco_venda_base = float(produto.get('produto_venda_fe') or 0)
                msg_dolar = "Preço salvo no banco (sem frete)."

            def pagamentos(base, custo_frete, juros_diarios):
                total = base + custo_frete
                return [
                    round(total, 2),
                    round(total + total * (juros_diarios * 28), 2),
                    round(total + total * (juros_diarios * 42), 2),
                    round(total + total * (juros_diarios * 56), 2),
                    round(total + total * (juros_diarios * 84), 2),
                    round(total + total * (juros_diarios * 70), 2),
                ]

            pagamentos_list = pagamentos(preco_venda_base, custo_frete, juros_diarios)

            produto_custo = Decimal(custo)
            custo_frete_dec = Decimal(custo_frete)
            custo_producao_dec = Decimal(custo_producao)
            outros_custos_percent_dec = Decimal(outros_custos_pct)
            lucro_desejado_dec = Decimal(lucro_desejado)
            pis_dec = Decimal(pis)
            cofins_dec = Decimal(cofins)
            irpj_dec = Decimal(irpj)
            csll_dec = Decimal(csll)
            icms_dec = Decimal(icms)
            icms_fe_dec = Decimal(icms_fe) if incluir_icms_fe else Decimal(0)

            soma_percentuais = (lucro_desejado_dec + outros_custos_percent_dec + pis_dec + cofins_dec +
                                irpj_dec + csll_dec + icms_dec + icms_fe_dec)
            base = Decimal(1) - soma_percentuais

            preco_venda = Decimal(preco_venda_base)
            outros_custos_r = preco_venda * outros_custos_percent_dec
            custo_total = produto_custo + custo_producao_dec + outros_custos_r
            total_impostos = preco_venda * (pis_dec + cofins_dec + irpj_dec + csll_dec + icms_dec + icms_fe_dec)
            lucro_liquido = preco_venda - custo_total - total_impostos
            lucro_liquido_percent = (lucro_liquido / preco_venda * 100) if preco_venda else Decimal(0)

            resultados[nome_cat].append({
                'nome': produto['produto_nome'],
                'pagamentos': pagamentos_list,
                'msg_dolar': msg_dolar,
                'lucro_desejado_pct': float(lucro_desejado_dec * 100),
                'lucro_calc_pct': float(lucro_liquido_percent),
                'lucro_liquido_r': float(lucro_liquido),
                'custo_total_r': float(custo_total),
                'total_impostos_r': float(total_impostos),
                'custo_frete_r': float(custo_frete_dec),
                'custo_producao_r': float(custo_producao_dec),
                'outros_custos_r': float(outros_custos_r),
                'custo_produto_r': float(custo),
                'ficha_tecnica': detalhamento_ficha,
                'erro_ficha': erro_ficha,
            })

    cursor.close()
    conn.close()
    return resultados, produtos_filtrados, datahora_geracao

@tabela_precos_bp.route('/tabela_precos', methods=['GET', 'POST'])
def tabela_precos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscar tipos (exceto 1 e 2)
    cursor.execute("SELECT tipoID, tipo as nome FROM tipo WHERE tipoID NOT IN (1, 2)")
    tipos = cursor.fetchall()

    # Relacionamento tipo → categoria
    cursor.execute("SELECT categoriaID, categoria_tipoID FROM categoria WHERE categoria_tipoID NOT IN (1, 2)")
    relacao_tipo_categoria = {str(row['categoriaID']): str(row['categoria_tipoID']) for row in cursor.fetchall()}

    # Produtos por categoria (para terceiro quadro)
    cursor.execute("SELECT produtoID, produto_nome, produto_categoriaID FROM produtos")
    produtos_raw = cursor.fetchall()
    produtos_por_categoria = {}
    for prod in produtos_raw:
        cat_id = str(prod['produto_categoriaID'])
        if cat_id not in produtos_por_categoria:
            produtos_por_categoria[cat_id] = []
        produtos_por_categoria[cat_id].append({'id': prod['produtoID'], 'nome': prod['produto_nome']})

    # Buscar categorias válidas (ignora tipoID 1 e 2)
    cursor.execute("""
        SELECT c.categoriaID, c.categoria 
        FROM categoria c
        WHERE c.categoria_tipoID NOT IN (1,2)
        ORDER BY c.categoria
    """)
    categorias = cursor.fetchall()

    resultados, produtos_selecionados, datahora_geracao = gerar_tabela_preco(
        request.form.getlist("tipos"),
        request.form.getlist("categorias"),
        request.form.getlist("produtos"),
        request.form.get("frete_opcao", "sem"),
        request.form.get("frete_manual"),
        request.form.get("dentro_fora", "dentro"),
        request.form.get("modo_preco", "salvo")
    )
    datahora_geracao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    cursor.close()
    conn.close()

    return render_template(
        'relatorios/filtro_tabela_precos.html',
        categorias=categorias,
        resultados=resultados,
        datahora_geracao=datahora_geracao,
        tipos=tipos,
        relacao_tipo_categoria=relacao_tipo_categoria,
        produtos_por_categoria=produtos_por_categoria,
        produtos_selecionados=produtos_selecionados
    )

@tabela_precos_bp.route('/tabela_precos/imprimir', methods=['POST'])
def imprimir_tabela_precos():
    # Pegue os mesmos dados do form
    tipos = request.form.getlist("tipos")
    categorias = request.form.getlist("categorias")
    produtos_filtrados = request.form.getlist("produtos")
    frete_opcao = request.form.get("frete_opcao", "sem")
    frete_manual = request.form.get("frete_manual")
    dentro_fora = request.form.get("dentro_fora", "dentro")
    modo_preco = request.form.get("modo_preco", "salvo")

    # Execute a mesma lógica de geração de resultados
    resultados, _, datahora_geracao = gerar_tabela_preco(
        tipos, categorias, produtos_filtrados, frete_opcao,
        frete_manual, dentro_fora, modo_preco
    )

    return render_template(
        "relatorios/tabela_precos_impressao.html",
        resultados=resultados,
        datahora_geracao=datahora_geracao
    )
