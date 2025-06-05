from flask import Flask
from cadastro_empresa import empresa_bp

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Necessário para usar flash messages

# Registra o Blueprint
app.register_blueprint(empresa_bp)

if __name__ == '__main__':
    app.run(debug=True)