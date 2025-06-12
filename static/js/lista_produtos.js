$(document).ready(function () {
  function carregarProdutos() {
    const termo = $('#filtro-nome').val();
    const categoria = $('#filtro-categoria').val();
    const preco = $('#filtro-preco').val();
    const tipo = $('#filtro-tipo').val();

    $.getJSON('/produtos/api', {
      q: termo,
      categoria: categoria,
      preco: preco,
      tipo: tipo
    }, function (produtos) {
      const tbody = $('#tabela-produtos tbody');
      tbody.empty();

      if (produtos.length === 0) {
        tbody.append('<tr><td colspan="8" class="text-center">Nenhum produto encontrado.</td></tr>');
        return;
      }

      produtos.forEach(p => {
        tbody.append(`
          <tr>
            <td><a href="/editar_produto/editar_produto/${p.produtoID}">${p.produto_nome}</a></td>
            <td>${p.preco_venda.toFixed(2)}</td>
            <td>${p.unidade || ''}</td>
            <td>${p.produto_peso || ''}</td>
            <td>${p.produto_validade || ''}</td>
            <td>${p.categoria || ''}</td>
            <td>${p.produto_fornecedor || ''}</td>
            <td>${p.produto_descricao || ''}</td>
          </tr>
        `);
      });
    });
  }

  $('#filtro-nome').on('input', carregarProdutos);
  $('#filtro-categoria, #filtro-preco, #filtro-tipo').on('change', carregarProdutos);

  carregarProdutos(); // chamada inicial
});
