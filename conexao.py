# conexao.py

import mysql.connector

def get_db_connection():
    db_config = {
        'user': 'root',
        'password': 'M@is2021',
        'host': 'localhost',
        'database': 'fabprecifica'
    }
    return mysql.connector.connect(**db_config)