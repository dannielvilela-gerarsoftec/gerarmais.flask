document.addEventListener('DOMContentLoaded', function () {
  // 1. Carregamento dinâmico das categorias com base no tipo
  const tipoSelect = document.getElementById('produto_tipoID');
  const categoriaSelect = document.getElementById('produto_categoriaID');

  async function carregarCategorias(tipoIDSelecionado, categoriaPreSelecionada = null) {
    categoriaSelect.innerHTML = '<option disabled selected>Carregando categorias...</option>';

    try {
      const response = await fetch(`/editar_produto/categorias_por_tipo/${tipoIDSelecionado}`);
      const categorias = await response.json();

      categoriaSelect.innerHTML = '<option disabled selected>Selecione a categoria</option>';
      categorias.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.nome;
        if (categoriaPreSelecionada && parseInt(categoriaPreSelecionada) === cat.id) {
          option.selected = true;
        }
        categoriaSelect.appendChild(option);
      });
    } catch (err) {
      categoriaSelect.innerHTML = '<option disabled selected>Erro ao carregar categorias</option>';
      console.error('Erro ao buscar categorias:', err);
    }
  }

  if (tipoSelect) {
    tipoSelect.addEventListener('change', function () {
      const tipoID = tipoSelect.value;
      if (tipoID) {
        carregarCategorias(tipoID);
      }
    });

    const tipoInicial = tipoSelect.value;
    const categoriaAtual = categoriaSelect.getAttribute('data-valor-atual');
    if (tipoInicial) {
      carregarCategorias(tipoInicial, categoriaAtual);
    }
  }

  // 2. Precificação do produto e condições de pagamento
  const blocos = ['de', 'de_fr', 'fe', 'fe_fr'];
  const blocosRev = ['rev_de', 'rev_de_fr', 'rev_fe', 'rev_fe_fr'];
  const jurosDiario = parseFloat(document.getElementById('param_outros_custos')?.getAttribute('data-juros') || 0.001);

  function toDecimal(value) {
    if (!value) return 0;
    value = ('' + value).replace(/\s/g, '').replace('R$', '').trim();
    if (value.includes(',')) {
      return parseFloat(value.replace(/\./g, '').replace(',', '.')) || 0;
    }
    return parseFloat(value) || 0;
  }

  function atualizarCamposBloco(bloco) {
    const input = document.getElementById(`preco_venda_${bloco}`);
    const valorVenda = toDecimal(input?.value);

    const pis = parseFloat(document.getElementById('param_pis').value) || 0;
    const cofins = parseFloat(document.getElementById('param_cofins').value) || 0;
    const irpj = parseFloat(document.getElementById('param_irpj').value) || 0;
    const csll = parseFloat(document.getElementById('param_csll').value) || 0;
    const icms = parseFloat(document.getElementById(`param_icms_${bloco}`).value) || 0;
    const icms_fe = bloco.includes('fe') ? parseFloat(document.getElementById('param_icms_fe_extra').value) || 0 : 0;

    const percentualImpostos = pis + cofins + irpj + csll + icms + icms_fe;
    const impostos = valorVenda * percentualImpostos;

    const custoProduto = toDecimal(document.getElementById('custo_produto').innerText);
    const producao = toDecimal(document.getElementById('custo_producao').innerText);
    const frete = toDecimal(document.getElementById(`custo_frete_${bloco}`).innerText);
    const outrosPct = parseFloat(document.getElementById('param_outros_custos').value) || 0;
    const outrosCustos = valorVenda * outrosPct;
    const custoTotal = custoProduto + producao + frete + outrosCustos + impostos;
    const lucroLiquido = valorVenda - custoTotal;
    const lucroPercentual = valorVenda ? (lucroLiquido / valorVenda) * 100 : 0;

    document.getElementById(`custo_total_${bloco}`).innerText = custoTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`total_impostos_${bloco}`).innerText = impostos.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`lucro_liquido_r_${bloco}`).innerText = lucroLiquido.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`lucro_liquido_percent_${bloco}`).innerText = `${lucroPercentual.toFixed(2)}%`;
    document.getElementById(`outros_custos_${bloco}`).innerText = outrosCustos.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    const juros = {
      'avista': 0,
      '28': jurosDiario * 28,
      '28_56': jurosDiario * 42,
      '56': jurosDiario * 56,
      '84': jurosDiario * 84,
      '3x': jurosDiario * 70
    };

    for (const prazo in juros) {
      const fator = 1 + juros[prazo];
      const campoID = `pagamento_${bloco}_${prazo}`;
      const campo = document.getElementById(campoID);
      if (campo) {
        campo.innerText = (valorVenda * fator).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
      }
    }
  }

  function atualizarCamposBlocoRev(bloco, valorBase) {
    const juros = {
      'avista': 0,
      '28': jurosDiario * 28,
      '28_56': jurosDiario * 42,
      '56': jurosDiario * 56,
      '84': jurosDiario * 84,
      '3x': jurosDiario * 70
    };

    for (const prazo in juros) {
      const fator = 1 + juros[prazo];
      const campoID = `pagamento_${bloco}_${prazo}`;
      const campo = document.getElementById(campoID);
      if (campo) {
        campo.innerText = (valorBase * fator).toLocaleString('pt-BR', {
          style: 'currency',
          currency: 'BRL'
        });
      }
    }
  }

  blocos.forEach(bloco => {
    const input = document.getElementById(`preco_venda_${bloco}`);
    if (input) {
      input.addEventListener('input', () => atualizarCamposBloco(bloco));
      atualizarCamposBloco(bloco);
    }
  });

  blocosRev.forEach(bloco => {
    const base = toDecimal(document.getElementById(`preco_${bloco}`)?.innerText);
    atualizarCamposBlocoRev(bloco, base);
  });

  // 3. Conversão de custo USD via PTAX
  (async function calcularCustoDolarPTAX() {
    const custoInput = document.getElementById('produto_custo');
    const custoProduto = parseFloat(custoInput?.value || 0);
    const moeda = custoInput && document.getElementById('produto_custo_moeda')?.value || 'R';
    const custoDolar = parseFloat("{{ produto.produto_custo_dolar if produto else 0 }}");
    let custoFinal = custoProduto;
    let explicacao = '';

    if (moeda === "U" && custoDolar > 0) {
      try {
        const response = await fetch("/ptax");
        const ptax = await response.json();
        const convertido = custoDolar * ptax.ptax;
        custoFinal = Math.max(convertido, custoProduto);
        explicacao = `Custo convertido (USD): R$ ${convertido.toFixed(4)}<br>
                      Custo em real: R$ ${custoProduto.toFixed(4)}<br>
                      PTAX: ${ptax.ptax.toFixed(4)} (${ptax.data})<br>
                      <strong>Valor utilizado: R$ ${custoFinal.toFixed(4)}</strong>`;
      } catch (e) {
        explicacao = "Não foi possível recuperar a cotação PTAX.";
      }

      const campoTotal = document.getElementById("custo-total-produto");
      const campoExplicacao = document.getElementById("explicacao-conversao-moeda");
      if (campoTotal) campoTotal.textContent = `R$ ${custoFinal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
      if (campoExplicacao) campoExplicacao.innerHTML = explicacao;
    }
  })();
});
