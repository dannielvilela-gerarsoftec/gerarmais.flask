from conexao import get_db_connection

def testar_conexao():
    try:
        # Obtém a conexão com o banco de dados
        connection = get_db_connection()
        cursor = connection.cursor()

        # Realiza uma consulta simples
        cursor.execute("SELECT cargoID, cargo FROM cargos")
        cargos = cursor.fetchall()

        # Imprime os resultados para verificar se os dados estão sendo recuperados
        if cargos:
            for cargo in cargos:
                print(f'Cargo ID: {cargo[0]}, Nome do Cargo: {cargo[1]}')
            print("Conexão e consulta realizadas com sucesso!")
        else:
            print("Nenhum cargo encontrado.")
    except Exception as e:
        print(f"Erro ao conectar ou consultar o banco de dados: {e}")
    finally:
        # Fecha o cursor e a conexão para liberar recursos
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Execute a função de teste
if __name__ == "__main__":
    testar_conexao()