import pyodbc
import pandas as pd

# Dados de conexão
server = 'alrflorestal.database.windows.net'
database = 'Tabela_teste'
username = 'gestaoti'
password = 'Senhaforte123!'
driver = '{ODBC Driver 17 for SQL Server}'

try:
    # Montar string de conexão
    conn_str = f'''
        DRIVER={driver};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
    '''

    # Conectar ao banco
    conn = pyodbc.connect(conn_str)
    print("✅ Conexão bem-sucedida!")

    # Consulta de teste (ajuste a tabela se quiser)
    df = pd.read_sql("SELECT TOP 10 * FROM HISTORICO_BDO ORDER BY ID DESC", conn)

    # Mostrar resultado
    print("\n🧾 Resultados:")
    print(df)

    conn.close()

except Exception as e:
    print(f"❌ Erro na conexão: {e}")
