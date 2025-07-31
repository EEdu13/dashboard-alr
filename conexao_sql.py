from dotenv import load_dotenv
import os
import pyodbc
import pandas as pd

load_dotenv()  # carrega as variáveis do .env

def obter_dados_sharepoint():
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'

    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    query = "SELECT * FROM BOLETIM_DIARIO"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
