# /blueprints/produtos/lista_produtos.py

from flask import Blueprint, render_template, request

# Definindo o Blueprint
lista_produto_bp = Blueprint('lista_produto', __name__, url_prefix='/produtos')

# Dados de exemplo
products_data = [
    {'id': 1, 'name': 'Produto A', 'family': 'Família 1', 'price_avista': 100, 'price_28': 105, 'price_56': 110, 'price_28_56': 107, 'price_card_3x': 115},
    {'id': 2, 'name': 'Produto B', 'family': 'Família 2', 'price_avista': 200, 'price_28': 205, 'price_56': 210, 'price_28_56': 207, 'price_card_3x': 215},
]

@lista_produto_bp.route('/')
def list_products():
    query = request.args.get('q')
    filtered_products = [product for product in products_data if query and query.lower() in product['name'].lower()] if query else products_data
    return render_template('lista_produtos.html', products=filtered_products)

@lista_produto_bp.route('/<int:product_id>')
def product_details(product_id):
    product = next((item for item in products_data if item['id'] == product_id), None)
    if product:
        return render_template('produtos.html', product=product)
    else:
        return render_template('404.html'), 404