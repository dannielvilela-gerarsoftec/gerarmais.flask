// --- Script JS removido de filtro_tabela_precos.html ---

const produtosMarcados = window.produtosMarcados || [];
const relacaoTipoCategoria = window.relacaoTipoCategoria || {};
const produtosPorCategoria = window.produtosPorCategoria || {};

function atualizarCategorias() {
  const tiposSelecionados = Array.from(document.querySelectorAll('.filtro-tipo:checked')).map(cb => cb.value);
  const categoriasFiltradas = [];

  for (const [categoriaID, tipoID] of Object.entries(relacaoTipoCategoria)) {
    if (tiposSelecionados.includes(tipoID.toString())) {
      categoriasFiltradas.push(categoriaID);
    }
  }

  document.querySelectorAll('#categorias-container .categoria-item').forEach(item => {
    const checkbox = item.querySelector('input');
    const cid = checkbox.value;
    if (categoriasFiltradas.includes(cid)) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
      checkbox.checked = false;
    }
  });

  atualizarProdutos();
}

function atualizarProdutos() {
  const categoriasSelecionadas = Array.from(document.querySelectorAll('.filtro-categoria:checked')).map(cb => cb.value);
  const container = document.getElementById('produtos-container');
  container.innerHTML = '';

  categoriasSelecionadas.forEach(catID => {
    const produtos = produtosPorCategoria[catID] || [];
    produtos.forEach(p => {
      const item = document.createElement('div');
      item.className = 'col produto-item';
      const checked = produtosMarcados.includes(String(p.id)) ? 'checked' : '';
      item.innerHTML = `
        <div class="form-check">
            <input class="form-check-input filtro-produto" type="checkbox" name="produtos" value="${p.id}" id="prod${p.id}" ${checked}>
            <label class="form-check-label" for="prod${p.id}">${p.nome}</label>
        </div>
      `;
      container.appendChild(item);
    });
  });

  aplicarFiltroBuscaProduto();
}

function aplicarFiltroBuscaTipo() {
  const termo = document.getElementById('tipo-busca').value.toLowerCase();
  document.querySelectorAll('.tipo-item').forEach(item => {
    item.style.display = item.textContent.toLowerCase().includes(termo) ? '' : 'none';
  });
}
function aplicarFiltroBuscaCategoria() {
  const termo = document.getElementById('categoria-busca').value.toLowerCase();
  document.querySelectorAll('.categoria-item').forEach(item => {
    item.style.display = item.textContent.toLowerCase().includes(termo) ? '' : 'none';
  });
}
function aplicarFiltroBuscaProduto() {
  const termo = document.getElementById('produto-busca').value.toLowerCase();
  document.querySelectorAll('.produto-item').forEach(item => {
    item.style.display = item.textContent.toLowerCase().includes(termo) ? '' : 'none';
  });
}

function abrirImpressao() {
  const form = document.querySelector('form');
  const formData = new FormData(form);

    fetch(window.urlImprimirTabela, {
    method: 'POST',
    body: formData
    }).then(response => response.text())
    .then(html => {
        const novaJanela = window.open('', '_blank');
        novaJanela.document.write(html);
        novaJanela.document.close();
    });
}
    window.abrirImpressao = abrirImpressao;

// Listeners
document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('tipo-select-all').onclick = () => {
    document.querySelectorAll('.filtro-tipo').forEach(cb => cb.checked = true);
    atualizarCategorias();
  };
  document.getElementById('tipo-deselect-all').onclick = () => {
    document.querySelectorAll('.filtro-tipo').forEach(cb => cb.checked = false);
    atualizarCategorias();
  };
  document.getElementById('cat-select-all').onclick = () => {
    document.querySelectorAll('#categorias-container .categoria-item').forEach(item => {
      if (item.style.display !== 'none') {
        item.querySelector('input[type="checkbox"]').checked = true;
      }
    });
    atualizarProdutos();
  };
  document.getElementById('cat-deselect-all').onclick = () => {
    document.querySelectorAll('.filtro-categoria').forEach(cb => cb.checked = false);
    atualizarProdutos();
  };
  document.getElementById('prod-select-all').onclick = () => {
    document.querySelectorAll('#produtos-container .filtro-produto').forEach(cb => cb.checked = true);
  };
  document.getElementById('prod-deselect-all').onclick = () => {
    document.querySelectorAll('#produtos-container .filtro-produto').forEach(cb => cb.checked = false);
  };

  document.getElementById('tipo-busca').addEventListener('input', aplicarFiltroBuscaTipo);
  document.getElementById('categoria-busca').addEventListener('input', aplicarFiltroBuscaCategoria);
  document.getElementById('produto-busca').addEventListener('input', aplicarFiltroBuscaProduto);

  document.querySelectorAll('.filtro-tipo').forEach(cb => cb.addEventListener('change', atualizarCategorias));
  document.querySelectorAll('.filtro-categoria').forEach(cb => cb.addEventListener('change', atualizarProdutos));

  atualizarCategorias();
  atualizarProdutos();
});