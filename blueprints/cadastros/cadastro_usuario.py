from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from conexao import get_db_connection
import re
from datetime import datetime

cadastro_usuario_bp = Blueprint('cadastro_usuario', __name__, template_folder='templates')

@cadastro_usuario_bp.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    conn = get_db_connection()
    
    # Preenche a lista de cargos a partir do banco de dados
    cursor = conn.cursor()
    cursor.execute("SELECT cargoID, cargo FROM cargos")
    lista_cargos = cursor.fetchall()
    cursor.close()
    
    if request.method == 'POST':
        cpf = request.form['cpf']
        nome = request.form['nome']
        ultimo_nome = request.form['ultimo_nome']
        email = request.form['email']
        confirmar_email = request.form['confirmar_email']
        empresa = request.form['empresa']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        cargo_id = request.form['cargo_id']
        data_cadastro = datetime.now()

        # Validação de dados
        if not re.match(r'^\d{11}$', cpf):
            flash('CPF inválido! Deve conter 11 dígitos.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario'))

        if email != confirmar_email:
            flash('Emails não conferem.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario'))

        if senha != confirmar_senha:
            flash('As senhas não conferem.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario'))

        # Hashing da senha
        senha_hash = generate_password_hash(senha)

        # Conexão com o banco de dados
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO usuarios (cpf, nome, ultimo_nome, email, usuario, senha, empresa, cargo, data) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (cpf, nome, ultimo_nome, email, email, senha_hash, empresa, cargo_id, data_cadastro)
            )
            conn.commit()
            flash('Usuário cadastrado com sucesso!')
        except Exception as err:
            flash(f'Erro ao cadastrar usuário: {err}')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('cadastro_usuario.cadastrar_usuario'))

    return render_template('cadastro_usuario.html', lista_cargos=lista_cargos)