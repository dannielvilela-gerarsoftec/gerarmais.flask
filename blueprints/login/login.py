from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import check_password_hash
from conexao import get_db_connection
from blueprints.login.main import login_required

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Consulta o usuário pela coluna de email
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['senha'], password):
                cargo = user['cargo']
                empresa_id = user.get('empresa')

                # Verifica o plano da empresa
                cursor.execute("SELECT ativa FROM dados_empresa WHERE dados_empresaID = %s", (empresa_id,))
                empresa_info = cursor.fetchone()

                if empresa_info:
                    plano_ativo = empresa_info['ativa']
                    session['cargo'] = cargo
                    session['plano_ativo'] = plano_ativo
                    session['user_id'] = user['usuarioID']
                    session['empresa_id'] = user.get('empresa')
                    session['nome_usuario'] = user.get('nome')
                    session['sobrenome_usuario'] = user.get('ultimo_nome')
                    session['usuario_email'] = user['email']
                    session['usuario_foto'] = user.get('foto')
                    flash('Login bem-sucedido!', 'success')

                    # Redireciona para a página login/pg_inicial.html
                    return redirect(url_for('login.pg_inicial'))
                else:
                    flash('Não foi possível verificar o plano da empresa.', 'danger')
            else:
                flash('Credenciais inválidas. Por favor, tente novamente.', 'danger')

        except mysql.connector.Error as err:
            flash(f'Ocorreu um erro ao acessar o banco de dados: {str(err)}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('login/login.html')

@login_bp.route('/logout')
def logout():
    session.clear()  # Limpa toda a sessão!
    flash('Você saiu com sucesso!', 'success')
    return redirect(url_for('login.login'))

# Nova rota para a página inicial
@login_bp.route('/pg_inicial')
@login_required
def pg_inicial():
    return render_template('login/pg_inicial.html')