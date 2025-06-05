from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from conexao import get_db_connection

cadastro_empresa_bp = Blueprint('cadastro_empresa', __name__, template_folder='../templates')

def obter_cargos():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT cargoID, cargo FROM cargos")
        cargos = cursor.fetchall()
        return cargos
    except Exception as e:
        print(f"Erro ao conectar ou consultar o banco de dados: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@cadastro_empresa_bp.route('/cadastro_empresa', methods=['GET', 'POST'])
def cadastro_empresa():
    if request.method == 'POST':
        cnpj = request.form['cnpj']
        razao_social = request.form['razao_social']
        fantasia = request.form['fantasia']
        cargo = request.form['cargo']
        nome = request.form['nome']
        ultimo_nome = request.form['ultimo_nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']
        confirma_senha = request.form['confirma_senha']
        data = request.form['data']

        # Validação de senha
        if senha != confirma_senha:
            flash('As senhas não coincidem.')
            return redirect(url_for('cadastro_empresa.cadastro_empresa'))

        # Gera o hash da senha
        senha_hash = generate_password_hash(senha)

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Insere os dados na tabela dados_empresa
            cursor.execute("""
                INSERT INTO dados_empresa (cnpj, razao_social, fantasia, ativa) VALUES (%s, %s, %s, %s)
            """, (cnpj, razao_social, fantasia, "0"))

            # Obtém o ID da empresa recém-criada
            empresa_id = cursor.lastrowid

            # Insere os dados do usuário associado à empresa
            cursor.execute("""
                INSERT INTO usuarios (nome, ultimo_nome, cpf, email, senha, cargo, empresa, data, usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nome, ultimo_nome, cpf, email, senha_hash, cargo, empresa_id, data, email))
            
            connection.commit()
            flash('Cadastro realizado com sucesso!')
            return redirect(url_for('login'))
        except Exception as e:
            connection.rollback()
            flash('Cadastro não realizado: ' + str(e))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    cargos = obter_cargos()
    return render_template('cadastro_empresa.html', cargos=cargos)