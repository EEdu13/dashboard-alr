import pyodbc
import pandas as pd

def obter_dados_sharepoint():
    server = 'alrflorestal.database.windows.net'
    database = 'Tabela_teste'
    username = 'sqladmin'
    password = 'SenhaForte123!'
    driver = '{ODBC Driver 17 for SQL Server}'

    conn = pyodbc.connect(
        f'DRIVER={driver};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )

    query = "SELECT * FROM BOLETIM_DIARIO"  # ou o nome correto da sua tabela
    df = pd.read_sql(query, conn)
    conn.close()
    return df
