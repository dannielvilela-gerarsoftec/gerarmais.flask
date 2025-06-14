$(document).ready(function () {
  function carregarProdutos() {
    const nome = $('#filtro-nome').val();
    const categoria = $('#filtro-categoria').val();
    const preco = $('#filtro-preco').val();
    const tipo = $('#filtro-tipo').val();

    $.getJSON('/produtos/api', {
      q: nome,
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
            <td>R$ ${p.preco_venda.toFixed(2)}</td>
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

  carregarProdutos();
});


// 🔁 VISUALIZAR TABELA
window.abrirRelatorio = function () {
  const linhas = document.querySelectorAll("#tabela-produtos tbody tr");
  const now = new Date();
  const dataHora = now.toLocaleString('pt-BR');
  const titulo = "Tabela de Preço";

  const tipo = $('#filtro-tipo option:selected').text().trim();
  const preco = $('#filtro-preco option:selected').text().trim();
  const resumoFiltro = `${tipo} ${preco}`;

  const juros_diario = typeof jurosDiarioGlobal !== 'undefined' ? jurosDiarioGlobal : 0.00066;

  let conteudo = `
    <html>
    <head>
      <title>${titulo}</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h3 { text-align: center; margin-bottom: 0px; }
        p { text-align: center; margin-top: 4px; margin-bottom: 20px; font-size: 12px; color: #666; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 6px; text-align: center; white-space: nowrap; }
        th:first-child, td:first-child { text-align: left; }
      </style>
    </head>
    <body>
      <h3>${titulo}</h3>
      <p>Emitido em: ${dataHora}</p>
      <p><strong>${resumoFiltro}</strong></p>
      <table>
        <thead>
          <tr>
            <th>Produto</th>
            <th>Peso (kg)</th>
            <th>Unidade</th>
            <th>À Vista</th>
            <th>28 Dias</th>
            <th>56 Dias</th>
            <th>28/56</th>
            <th>84 Dias</th>
            <th>3x</th>
            <th>Fornecedor</th>
          </tr>
        </thead>
        <tbody>
  `;

  linhas.forEach(tr => {
    const tds = tr.querySelectorAll("td");

    const produto = tds[0]?.textContent || '';
    const peso = tds[3]?.textContent || '';
    const unidade = tds[2]?.textContent || '';
    const fornecedor = tds[6]?.textContent || '';
    const precoBase = parseFloat((tds[1]?.textContent || '0').replace('R$', '').replace(',', '.').trim()) || 0;

    const calcPrazo = dias => precoBase * (1 + juros_diario * dias);

    const valorAvista = precoBase.toFixed(2);
    const valor28 = calcPrazo(28).toFixed(2);
    const valor56 = calcPrazo(56).toFixed(2);
    const valor28_56 = calcPrazo(84).toFixed(2); // 28 + 56
    const valor84 = calcPrazo(84).toFixed(2);
    const valor3x = calcPrazo(90).toFixed(2); // 3x = 90 dias

    conteudo += `
      <tr>
        <td>${produto}</td>
        <td>${peso}</td>
        <td>${unidade}</td>
        <td>R$ ${valorAvista}</td>
        <td>R$ ${valor28}</td>
        <td>R$ ${valor56}</td>
        <td>R$ ${valor28_56}</td>
        <td>R$ ${valor84}</td>
        <td>R$ ${valor3x}</td>
        <td>${fornecedor}</td>
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
