def extrair_dados_formulario(form):
    # Extrai os dados do formulário e converte para float
    custos_compra = float(form['custos_compra'])
    pis = float(form['pis'])
    conf = float(form['conf'])
    irpj = float(form['irpj'])
    csll = float(form['csll'])
    icms = float(form['icms'])
    frete = float(form['frete'])
    producao = float(form['producao'])
    lucro_desejado = float(form['lucro_desejado'])

    return custos_compra, pis, conf, irpj, csll, icms, frete, producao, lucro_desejado

def calcular_precificacao(custos_compra, pis, conf, irpj, csll, icms, frete, producao, lucro_desejado):
    # Cálculo do custo total
    custo_total = custos_compra + frete + producao

    # Cálculo do preço de venda
    preco_venda = custo_total / (1 - (lucro_desejado + pis + conf + irpj + csll + icms) / 100)

    # Cálculo dos impostos em R$
    valor_pis = preco_venda * (pis / 100)
    valor_conf = preco_venda * (conf / 100)
    valor_irpj = preco_venda * (irpj / 100)
    valor_csll = preco_venda * (csll / 100)
    valor_icms = preco_venda * (icms / 100)

    total_impostos = valor_pis + valor_conf + valor_irpj + valor_csll + valor_icms

    # Cálculo do lucro líquido em R$
    lucro_liquido = preco_venda - custo_total - total_impostos

    return {
        'preco_venda': preco_venda,
        'total_impostos': total_impostos,
        'lucro_liquido': lucro_liquido
    }