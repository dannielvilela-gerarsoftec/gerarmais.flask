$(document).ready(function () {
  function carregarProdutos() {
    const termo = $('#filtro-nome').val();
    const categoria = $('#filtro-categoria').val();
    const preco = $('#filtro-preco').val();

    $.getJSON('/produtos/api', {
      q: termo,
      categoria: categoria,
      preco: preco
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

  $('#btn-filtrar').on('click', carregarProdutos);
  carregarProdutos();

  window.abrirRelatorio = function () {
    const linhas = document.querySelectorAll("#tabela-produtos tbody tr");
    const now = new Date();
    const dataHora = now.toLocaleString('pt-BR');
    const titulo = `Lista de Produtos - ${dataHora}`;

    let conteudo = `
      <html>
      <head>
        <title>${titulo}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h3 { text-align: center; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; font-size: 12px; }
          th, td { border: 1px solid #ccc; padding: 6px; text-align: left; white-space: nowrap; }
        </style>
      </head>
      <body>
        <h3>${titulo}</h3>
        <table>
          <thead>
            <tr>
              <th>Produto</th>
              <th>Preço (R$)</th>
              <th>Unidade</th>
              <th>Peso (kg)</th>
              <th>Categoria</th>
              <th>Fornecedor</th>
            </tr>
          </thead>
          <tbody>
    `;

    linhas.forEach(tr => {
      const tds = tr.querySelectorAll("td");
      conteudo += `
        <tr>
          <td>${tds[0]?.textContent || ''}</td>
          <td>${tds[1]?.textContent || ''}</td>
          <td>${tds[2]?.textContent || ''}</td>
          <td>${tds[3]?.textContent || ''}</td>
          <td>${tds[5]?.textContent || ''}</td>
          <td>${tds[6]?.textContent || ''}</td>
        </tr>
      `;
    });

    conteudo += `
          </tbody>
        </table>
      </body>
      </html>
    `;

    const novaJanela = window.open('', '_blank');
    novaJanela.document.write(conteudo);
    novaJanela.document.close();
  };
});
