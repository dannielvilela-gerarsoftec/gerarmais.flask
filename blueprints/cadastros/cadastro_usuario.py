from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from conexao import get_db_connection
from datetime import datetime
import re

cadastro_usuario_bp = Blueprint('cadastro_usuario', __name__, template_folder='templates')

@cadastro_usuario_bp.route('/cadastros/cadastro_usuario_interno', methods=['GET', 'POST'])
def cadastrar_usuario_interno():
    conn = get_db_connection()

    # Busca cargos no banco
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cargoID, cargo FROM cargos")
    lista_cargos = cursor.fetchall()

    if request.method == 'POST':
        # Coleta os dados
        cpf = request.form.get('cpf', '').replace('.', '').replace('-', '')
        nome = request.form.get('nome', '')
        ultimo_nome = request.form.get('ultimo_nome', '')
        email = request.form.get('email', '')
        conselho = request.form.get('conselho', '')
        numero_conselho = request.form.get('numero_conselho', '')
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        cargo_id = request.form.get('cargo_id')
        empresa_id = session.get('empresa_id')  # empresa já associada ao usuário logado
        data_cadastro = datetime.now()

        # Validações
        if not re.fullmatch(r'\d{11}', cpf):
            flash('CPF inválido! Deve conter 11 dígitos.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario_interno'))

        if senha != confirmar_senha:
            flash('As senhas não conferem.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario_interno'))

        if not empresa_id:
            flash('Erro interno: empresa não identificada.')
            return redirect(url_for('cadastro_usuario.cadastrar_usuario_interno'))

        senha_hash = generate_password_hash(senha)

        try:
            cursor.execute("""
                INSERT INTO usuarios (cpf, nome, ultimo_nome, email, usuario, senha, empresa, cargo, data, conselho, numero_conselho)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cpf, nome, ultimo_nome, email, email, senha_hash, empresa_id, cargo_id, data_cadastro,conselho, numero_conselho
            ))
            conn.commit()
            flash('Usuário cadastrado com sucesso!')
        except Exception as err:
            conn.rollback()
            flash(f'Erro ao cadastrar usuário: {err}')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('cadastro_usuario.cadastrar_usuario_interno'))

    return render_template('cadastros/cadastro_usuario_interno.html', lista_cargos=lista_cargos)
