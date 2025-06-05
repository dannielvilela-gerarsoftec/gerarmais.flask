@bp.route('/categorias_por_tipo/<int:tipo_id>')
def categorias_por_tipo(tipo_id):
    categorias = Categoria.query.filter_by(categoria_tipoID=tipo_id).all()
    return jsonify([
        {'id': c.categoriaID, 'nome': c.categoria}
        for c in categorias
    ])
