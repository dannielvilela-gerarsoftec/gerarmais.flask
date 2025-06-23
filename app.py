from flask import Flask, render_template, request

#Login
from blueprints.login.login import login_bp
from blueprints.login.main import main_bp

#Cadastros
from blueprints.cadastros.cadastro_usuario import cadastro_usuario_bp
from blueprints.cadastros.cadastro_empresa import cadastro_empresa_bp
from blueprints.cadastros.cadastro_produto import cadastro_produto_bp

#produtos
from blueprints.produtos.lista_produtos import lista_produtos_bp
from precifica_produtos import calcular_precificacao, extrair_dados_formulario
from blueprints.produtos.editar_produto import editar_produto_bp
from blueprints.produtos.precifica_formulacao import precifica_formulacao_bp
from blueprints.produtos.lista_formulacoes import lista_formulacoes_bp

#relatorios
from blueprints.relatorios.tabela_precos import tabela_precos_bp

#ingredientes
from blueprints.ingredientes_lista import ingredientes_bp

#parametros
from blueprints.parametros import parametros_bp
from blueprints.impostos import impostos_bp
from blueprints.categorias import categorias_bp
from blueprints.tipos import tipos_bp
from blueprints.unidades import unidades_bp
import os

app = Flask(__name__)

# Utilize variáveis de ambiente para segurança
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'sua_chave_secreta_padrao')

# Registre os blueprints

#login
app.register_blueprint(login_bp)
app.register_blueprint(main_bp)

#cadastros
app.register_blueprint(cadastro_usuario_bp)
app.register_blueprint(cadastro_empresa_bp)
app.register_blueprint(cadastro_produto_bp)

#produtos
app.register_blueprint(lista_produtos_bp)
app.register_blueprint(editar_produto_bp, url_prefix='/editar_produto')
app.register_blueprint(precifica_formulacao_bp)
app.register_blueprint(lista_formulacoes_bp)

#relatorios
app.register_blueprint(tabela_precos_bp)

#ingredientes
app.register_blueprint(ingredientes_bp)

#parametros
app.register_blueprint(parametros_bp)
app.register_blueprint(impostos_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(tipos_bp)
app.register_blueprint(unidades_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/precifica_produtos', methods=['GET', 'POST'])
def precifica_produtos():
    if request.method == 'POST':
        # Extraia dados do formulário
        dados = extrair_dados_formulario(request.form)
        
        # Calcule a precificação
        resultado = calcular_precificacao(*dados)
        return render_template('precifica_produtos.html', resultado=resultado)

    return render_template('precifica_produtos.html')

# Código para rodar o app
if __name__ == '__main__':
    app.run(debug=True)