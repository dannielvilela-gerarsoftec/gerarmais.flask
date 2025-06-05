from flask import Flask, render_template, redirect, url_for
import mercadopago
from conexao import get_db_connection

app = Flask(__name__)

# Configurar o Mercado Pago
sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")

@app.route('/')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dados_empresa")
    empresas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('gestao_cliente.html', empresas=empresas)

@app.route('/aprovar/<int:empresa_id>')
def aprovar_empresa(empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dados_empresa SET ativa=1 WHERE dados_empresaID=%s", (empresa_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/rejeitar/<int:empresa_id>')
def rejeitar_empresa(empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE dados_empresa SET ativa=0 WHERE dados_empresaID=%s", (empresa_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/processar_pagamento/<int:empresa_id>')
def processar_pagamento(empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cnpj, razao_social FROM dados_empresa WHERE dados_empresaID=%s", (empresa_id,))
    empresa = cursor.fetchone()

    payment_data = {
        "transaction_amount": 100,  # valor do pagamento
        "description": "Assinatura Anual",
        "payment_method_id": "pix",
        "payer": {
            "email": empresa['cnpj'] + "@exemplo.com"  # Substitua por um campo de email real se disponível
        }
    }
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]

    if payment["status"] == "approved":
        cursor.execute("UPDATE dados_empresa SET pagamento_status='pago' WHERE dados_empresaID=%s", (empresa_id,))
        conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)