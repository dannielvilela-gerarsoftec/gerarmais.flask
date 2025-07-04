document.addEventListener('DOMContentLoaded', function () {

  // === [SEÇÃO 0] Definições iniciais ===
  const jurosDiario = parseFloat(document.getElementById('param_outros_custos')?.getAttribute('data-juros') || 0.001);
  const blocos = ['de', 'de_fr', 'fe', 'fe_fr'];
  const blocosRev = ['rev_de', 'rev_de_fr', 'rev_fe', 'rev_fe_fr'];

  // === [SEÇÃO 1] Carregamento dinâmico de categorias com base no tipo ===
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

  if (tipoSelect && categoriaSelect) {
    tipoSelect.addEventListener('change', function () {
      const tipoID = tipoSelect.value;
      if (tipoID) carregarCategorias(tipoID);
    });

    const tipoInicial = tipoSelect.value;
    const categoriaAtual = categoriaSelect.getAttribute('data-valor-atual');
    if (tipoInicial && categoriaSelect.options.length <= 1) {
      carregarCategorias(tipoInicial, categoriaAtual);
    }
  }

  // === [SEÇÃO 2] Funções auxiliares ===
  function getJurosParcelas() {
    return {
      'avista': 0,
      '28': jurosDiario * 28,
      '28_56': jurosDiario * 42,
      '56': jurosDiario * 56,
      '84': jurosDiario * 84,
      '3x': jurosDiario * 70
    };
  }

  function getInputNumber(id) {
    const el = document.getElementById(id);
    return parseFloat(el?.value || 0);
  }

  function toDecimal(value) {
    if (!value) return 0;
    value = ('' + value).replace(/\s/g, '').replace('R$', '').trim();
    if (value.includes(',')) {
      return parseFloat(value.replace(/\./g, '').replace(',', '.')) || 0;
    }
    return parseFloat(value) || 0;
  }

  // === [SEÇÃO 3] Precificação do produto ===
  function atualizarCamposBloco(bloco) {
    const input = document.getElementById(`preco_venda_${bloco}`);
    const valorVenda = toDecimal(input?.value);

    const pis = getInputNumber('param_pis');
    const cofins = getInputNumber('param_cofins');
    const irpj = getInputNumber('param_irpj');
    const csll = getInputNumber('param_csll');
    const icms = getInputNumber(`param_icms_${bloco}`);
    const icms_fe = bloco.includes('fe') ? getInputNumber('param_icms_fe_extra') : 0;

    const percentualImpostos = pis + cofins + irpj + csll + icms + icms_fe;
    const impostos = valorVenda * percentualImpostos;

    const custoProduto = toDecimal(document.getElementById('custo_produto')?.innerText);
    const frete = toDecimal(document.getElementById(`custo_frete_${bloco}`)?.innerText);
    const outrosPct = getInputNumber('param_outros_custos');
    const outrosCustos = valorVenda * outrosPct;
    const custoTotal = custoProduto + frete + outrosCustos + impostos;
    const lucroLiquido = valorVenda - custoTotal;
    const lucroPercentual = valorVenda ? (lucroLiquido / valorVenda) * 100 : 0;

    document.getElementById(`custo_total_${bloco}`).innerText = custoTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`total_impostos_${bloco}`).innerText = impostos.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`lucro_liquido_r_${bloco}`).innerText = lucroLiquido.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    document.getElementById(`lucro_liquido_percent_${bloco}`).innerText = `${lucroPercentual.toFixed(2)}%`;
    document.getElementById(`outros_custos_${bloco}`).innerText = outrosCustos.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    const juros = getJurosParcelas();
    for (const prazo in juros) {
      const fator = 1 + juros[prazo];
      const campo = document.getElementById(`pagamento_${bloco}_${prazo}`);
      if (campo) {
        campo.innerText = (valorVenda * fator).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
      }
    }
  }

  // === [SEÇÃO 4] Precificação de revenda ===
  function atualizarCamposBlocoRev(bloco, valorBase) {
    const juros = getJurosParcelas();
    for (const prazo in juros) {
      const fator = 1 + juros[prazo];
      const campo = document.getElementById(`pagamento_${bloco}_${prazo}`);
      if (campo) {
        campo.innerText = (valorBase * fator).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
      }
    }
  }

  // === [SEÇÃO 5] Aplicar precificação ao carregar ===
  blocos.forEach(bloco => {
    const input = document.getElementById(`preco_venda_${bloco}`);
    if (input) {
      ['input', 'change'].forEach(evento => {
        input.addEventListener(evento, () => atualizarCamposBloco(bloco));
      });
      atualizarCamposBloco(bloco);
    }
  });

  blocosRev.forEach(bloco => {
    const base = parseFloat(document.getElementById(`preco_${bloco}`)?.value || 0);
    atualizarCamposBlocoRev(bloco, base);
  });

  // === [SEÇÃO 6] Conversão de custo USD via PTAX ===
  (async function calcularCustoDolarPTAX() {
    const custoInput = document.getElementById('produto_custo');
    const moeda = document.getElementById('produto_custo_moeda')?.value || 'R';
    const custoDolar = parseFloat(custoInput?.dataset?.custoDolar || 0);
    const custoProduto = parseFloat(custoInput?.value || 0);

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

  // === [SEÇÃO 7] Modal de exclusão ===
  const modalExcluir = document.getElementById('modalExcluir');
  if (modalExcluir) {
    modalExcluir.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const produtoID = button.getAttribute('data-produto-id');
      const form = modalExcluir.querySelector('#form-excluir-produto');
      if (form && produtoID) {
        form.setAttribute('action', `/editar_produto/excluir_produto/${produtoID}`);
      }
    });
  }

  // === [SEÇÃO 8] Atualização forçada no submit ===
  document.getElementById('form-editar-produto').addEventListener('submit', function () {
    blocos.forEach(bloco => atualizarCamposBloco(bloco));
  });

});
