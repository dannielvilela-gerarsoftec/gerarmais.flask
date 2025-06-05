from flask import Blueprint, render_template, session, redirect, url_for, flash
from functools import wraps

# Criação do blueprint do main
main_bp = Blueprint('main', __name__)

# Decorador para checar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar essa página.', 'warning')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar se o usuário é pagante
def pagante_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('plano_ativo') != 1:  # Verifica se o plano é ativo
            flash('Esta área é restrita a usuários pagantes.', 'warning')
            return redirect(url_for('main.pg_inicial'))
        return f(*args, **kwargs)
    return decorated_function

# Rota para a página inicial
@main_bp.route('/pg_inicial')
@login_required
def pg_inicial():
    return render_template('login/pg_inicial.html')

# Rota para área premium
@main_bp.route('/area_premium')
@login_required
@pagante_required
def area_premium():
    return render_template('area_premium.html')  # Suponha que você tenha uma template para usuários pagantes
