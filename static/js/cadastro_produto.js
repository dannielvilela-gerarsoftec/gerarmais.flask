document.addEventListener('DOMContentLoaded', function () {
  // === 1. Carregamento dinâmico das categorias com base no tipo ===
  const tipoSelect = document.getElementById('produto_tipoID');
  const categoriaSelect = document.getElementById('produto_categoriaID');

  async function carregarCategorias(tipoIDSelecionado) {
    categoriaSelect.innerHTML = '<option disabled selected>Carregando categorias...</option>';

    try {
      const response = await fetch(`/editar_produto/categorias_por_tipo/${tipoIDSelecionado}`);
      const categorias = await response.json();

      categoriaSelect.innerHTML = '<option disabled selected>Selecione a categoria</option>';
      categorias.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.nome;
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
      if (tipoID) {
        carregarCategorias(tipoID);
      }
    });

    const tipoInicial = tipoSelect.value;
    if (tipoInicial && categoriaSelect.options.length <= 1) {
      carregarCategorias(tipoInicial);
    }
  }

  // === 2. Validação do formulário com Bootstrap ===
  const forms = document.getElementsByClassName('needs-validation');
  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener('submit', function (event) {
      if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
      } else {
        $('#resultModal').modal('show');
      }
      form.classList.add('was-validated');
    }, false);
  });

  // === 3. Exibir modal de sucesso (se aplicável) ===
  if (typeof produtoCadastrado !== 'undefined' && produtoCadastrado) {
    $('#modalPosCadastro').modal('show');
  }
});
