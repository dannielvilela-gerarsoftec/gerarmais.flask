const produtoCustoCache = {};
const produtoPerdaCache = {};
const custoOportunidadeCache = {};

async function getProdutoCusto(produtoID) {
    if (produtoCustoCache[produtoID] !== undefined) return produtoCustoCache[produtoID];
    let res = await fetch('/produtos/custo/' + produtoID);
    let data = await res.json();
    produtoCustoCache[produtoID] = data;
    return data;
}
async function getProdutoPerda(produtoID) {
    if (produtoPerdaCache[produtoID] !== undefined) return produtoPerdaCache[produtoID];
    let res = await fetch('/produtos/perda/' + produtoID);
    let data = await res.json();
    produtoPerdaCache[produtoID] = data.produto_perda;
    return data.produto_perda;
}
async function getCustoOportunidade() {
    const categoriaID = 0;
    if (custoOportunidadeCache[categoriaID] !== undefined) return custoOportunidadeCache[categoriaID];
    let res = await fetch('/parametros/custo_oportunidade/0');
    let data = await res.json();
    custoOportunidadeCache[categoriaID] = data.custo_oportunidade;
    return data.custo_oportunidade;
}
let ptaxDataCache = null;
async function getPtaxData() {
    if (!ptaxDataCache) {
        try {
            const resp = await fetch('/ptax');
            ptaxDataCache = await resp.json();
        } catch (e) {
            console.warn('Erro ao buscar PTAX:', e);
            ptaxDataCache = { ptax: 0, data: '' }; // fallback seguro
        }
    }
    return ptaxDataCache;
}

// Atualiza todos os cálculos conforme os percentuais e dado do produto
async function atualizarCustos() {
    const pesoSaco = parseFloat(document.getElementById('peso_sacaria').value) || 0;
    let totalIng = 0;
    let percentualTotal = 0;
    let rows = document.querySelectorAll("#tabela-ingredientes tbody tr");
    let explicacoes = [];
    let rowIndex = 0;

        for (const row of rows) {
        const select = row.querySelector('select');
        const percentual = parseFloat(row.querySelector('.percentual').value) || 0;
        percentualTotal += percentual;

        const pesoSacoItem = pesoSaco * percentual / 100;
        row.querySelector('.peso-saco').textContent = pesoSacoItem.toFixed(4);

        const misturador = parseFloat(document.getElementById('misturador').value) || 0;
        const pesoMisturador = misturador * percentual / 100;
        row.querySelector('.peso-misturador').textContent = pesoMisturador.toFixed(4);

        let perda_percent = 0;
        if (select && select.value) {
            perda_percent = parseFloat(await getProdutoPerda(select.value)) || 0;
        }
        const perda_kg = pesoSacoItem * perda_percent;
        row.querySelector('.perda-kg').textContent = perda_kg.toFixed(4);

        let custo = 0;
        if (select && select.value) {
            const custo_data = await getProdutoCusto(select.value);
            const moeda = custo_data.produto_custo_moeda;
            let custo_real = custo_data.produto_custo;
            const custo_dolar = custo_data.produto_custo_dolar;
            let valor_usado = custo_real;

            if (custo_data.produto_tipoID === 3 && custo_data.produto_peso) {
                valor_usado = valor_usado / custo_data.produto_peso;
            }

            const tipoID = custo_data.produto_tipoID;
            const pesoProduto = custo_data.produto_peso;
            if (tipoID === 3 && pesoProduto > 0) {
                custo_real = custo_real / pesoProduto;
            }

            let explicacao = '';
            if (moeda === "U" && custo_dolar > 0) {
                const ptaxData = await getPtaxData();
                const valor_convertido = custo_dolar * ptaxData.ptax;
                valor_usado = Math.max(valor_convertido, custo_real);
                explicacao = `${select.options[select.selectedIndex].text}: Custo convertido (USD) = R$ ${valor_convertido.toFixed(4)}, Custo em real = R$ ${custo_real.toFixed(4)}, PTAX ${ptaxData.ptax.toFixed(4)} (${ptaxData.data}). Valor utilizado: R$ ${valor_usado.toFixed(4)}.`;
            }

            let custo_oportunidade = await getCustoOportunidade();

            if (custo_oportunidade && valor_usado && custo_oportunidade !== 0) {
                valor_usado += valor_usado * custo_oportunidade;
            }

            let custoMPDisplay = valor_usado;
            row.querySelector('.custo-mp').textContent = custoMPDisplay.toFixed(4);

            console.log(`[Linha ${rowIndex}]`, {
                produto: select.options[select.selectedIndex].text,
                pesoSacoItem,
                perda_kg,
                custoMPDisplay,
                custo: (pesoSacoItem + perda_kg) * custoMPDisplay
            });

            custo = (pesoSacoItem + perda_kg) * custoMPDisplay;
            row.querySelector('.custo-saco').textContent = custo.toFixed(4);
            if (explicacao) explicacoes.push(explicacao);
        }

        totalIng += custo;
        rowIndex++;
    }
    document.getElementById('total-custo-ing').textContent = totalIng.toFixed(2);
    document.getElementById('explicacao-conversao-moeda').innerHTML = explicacoes.join('<br>');
    

    // Validação soma percentual
    document.getElementById('percentual-total').textContent = percentualTotal.toFixed(4);
    if (Math.abs(percentualTotal - 100) > 0.001) {
        document.getElementById('percentual-total-alerta').classList.remove('d-none');
    } else {
        document.getElementById('percentual-total-alerta').classList.add('d-none');
    }

    // Custos extras
    let custo_oportunidade_extra = await getCustoOportunidade();
    let totalExtras = 0;

document.querySelectorAll('#tabela-extras tbody tr').forEach(row => {
    const select = row.querySelector('.extra-sel');
    const quantidade = parseFloat(row.querySelector('.extra-quantidade').value) || 0;
    let valorUnit = 0;

    if (select && select.selectedOptions.length > 0) { 
        valorUnit = parseFloat(select.selectedOptions[0].getAttribute('data-valor')) || 0;
    }

    // Aplica custo de oportunidade se houver
    if (custo_oportunidade_extra && custo_oportunidade_extra !== 0) {
        valorUnit += valorUnit * custo_oportunidade_extra;
    }

    row.querySelector('.valor-unitario').textContent = valorUnit.toFixed(2);
    let total = quantidade * valorUnit;
    row.querySelector('.valor-total-extra').textContent = total.toFixed(2);
    totalExtras += total;
});

    // Custo produção (se existir)
    let custoProducao = 0;
    if (document.getElementById('custo-producao')) {
        custoProducao = parseFloat(document.getElementById('custo-producao').textContent) || 0;
    }
    let totalProdutos = totalIng + totalExtras + custoProducao;
    document.getElementById('custo-total-produto').textContent = 'R$ ' + totalProdutos.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById('total-custo-extras').textContent = totalExtras.toFixed(2);
}

// Cálculo SACOS POR BATIDA ---------------------------
function atualizarSacosBatida() {
    const misturador = parseFloat(document.getElementById('misturador').value) || 0;
    const pesoSaco = parseFloat(document.getElementById('peso_sacaria').value) || 0;
    let sacos = 0;
    if (misturador > 0 && pesoSaco > 0) {
        sacos = misturador / pesoSaco;
    }
    document.getElementById('sacos_batida').value = sacos > 0 ? sacos.toFixed(2) : '';
}
// -----------------------------------------------------

function adicionarLinha() {
    const tabela = document.querySelector('#tabela-ingredientes tbody');
    const rowCount = tabela.rows.length;
    const newRow = tabela.insertRow();

    const selectOptions = ingredientesData.map(i => 
        `<option value="${i.produtoID}">${i.produto_nome}</option>`
    ).join('');

    newRow.innerHTML = `
        <td>
            <button type="button" class="btn btn-link text-danger" onclick="removerLinha(this)">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
        <td class="text-center">
            <select name="ingrediente_${rowCount}" class="form-select ingrediente-sel" required>
                ${selectOptions}
            </select>
        </td>
        <td class="text-center">
            <input type="number" name="percentual_${rowCount}" class="form-control percentual text-center"
                min="0" max="100" step="0.0001" required>
        </td>
        <td class="peso-misturador text-center">0</td>
        <td class="peso-saco text-center">0</td>
        <td class="perda-kg text-center">0</td>
        <td class="custo-mp text-center">0</td>
        <td class="custo-saco text-center">0</td>`;
    
    atualizarCustos();
}

function adicionarLinhaExtra() {
    const tabela = document.querySelector('#tabela-extras tbody');
    const rowCount = tabela.rows.length;
    const newRow = tabela.insertRow();

    const selectOptions = extrasData.map(i => 
        `<option value="${i.produtoID}" data-valor="${i.produto_custo}">${i.produto_nome}</option>`
    ).join('');

    newRow.innerHTML = `
        <td>
            <button type="button" class="btn btn-link text-danger" onclick="removerLinhaExtra(this)">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
        <td>
            <select name="extra_produto_${rowCount}" class="form-select extra-sel" required>
                ${selectOptions}
            </select>
        </td>
        <td>
            <input type="number" name="extra_quantidade_${rowCount}" class="form-control extra-quantidade" step="0.001" min="0" required>
        </td>
        <td><span class="valor-unitario"></span></td>
        <td><span class="valor-total-extra"></span></td>`;
    
    atualizarCustos();
}

function removerLinhaExtra(btn) {
    var row = btn.closest('tr');
    row.remove();
    atualizarCustos();
}

document.addEventListener('input', function(e) {
    if (
        e.target.classList.contains('percentual') || 
        e.target.id === 'peso_sacaria' || 
        e.target.id === 'misturador' || // agora também responde ao atualizar misturador!
        e.target.classList.contains('ingrediente-sel') || 
        e.target.classList.contains('extra-quantidade') ||
        e.target.classList.contains('extra-sel')
    ) {
        atualizarCustos();
        atualizarSacosBatida();
    }
});
document.addEventListener('DOMContentLoaded', function() {
    atualizarCustos();
    atualizarSacosBatida();
});