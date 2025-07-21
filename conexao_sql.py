import pyodbc

# Conexão com SQL Server
server = 'alrflorestal.database.windows.net'
database = 'Tabela_teste'
username = 'sqladmin'
password = 'SenhaForte123!'
driver = '{ODBC Driver 17 for SQL Server}'  # ou ODBC Driver 18 se estiver instalado

conn = pyodbc.connect(
    f'DRIVER={driver};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

cursor = conn.cursor()
