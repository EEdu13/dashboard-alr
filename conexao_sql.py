from dotenv import load_dotenv
import os
import pyodbc
import pandas as pd

# Carrega variáveis do .env (recomendado)
load_dotenv()

def obter_conexao_sql():
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    return conn

def obter_dados_sharepoint():
    conn = obter_conexao_sql()
    query = "SELECT * FROM BOLETIM_DIARIO"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obter_senhas_sql():
    conn = obter_conexao_sql()
    query = "SELECT * FROM USUARIOS"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
