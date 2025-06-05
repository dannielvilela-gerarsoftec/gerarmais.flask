from flask import Flask, request, jsonify, render_template


from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Configuração do banco de dados
db_config = {
    'user': 'root',
    'password': 'M@is2021',
    'host': 'localhost',
    'database': 'fabprecifica'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular_preco_venda', methods=['POST'])
def calcular_preco_venda():
    data = request.json
    custos_compra = data['custos_compra']
    pis = data['pis']
    conf = data['conf']
    irpj = data['irpj']
    csll = data['csll']
    icms = data['icms']
    frete = data['frete']
    producao = data['producao']
    lucro_desejado = data['lucro_desejado']

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

    return jsonify({
        'preco_venda': preco_venda,
        'total_impostos': total_impostos,
        'lucro_liquido': lucro_liquido
    })

if __name__ == '__main__':
    app.run(debug=True)