import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard ALR", layout="wide")

# --- Login ---
usuarios = {"admin": "admin123", "alr": "alr2025"}

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔒 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and senha == usuarios[usuario]:
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- Menu lateral ---
st.sidebar.title("📁 Navegação")
pagina = st.sidebar.radio("Ir para:", ["📄 Dados", "📊 Dashboards", "🧪 Qualidade", "💰 DRE", "🧑‍💼 RH"])

# --- Conexão com SQL ---
try:
    senha_segura = quote_plus("Senhaforte123!")  # codifica a senha com "!" corretamente
    engine = create_engine(
        f"mssql+pyodbc://gestaoti:{senha_segura}@alrflorestal.database.windows.net/Tabela_teste"
        "?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
    )
    query = "SELECT TOP 1000 * FROM HISTORICO_BDO ORDER BY ID DESC"
    df = pd.read_sql(query, engine)

except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()

# --- Página: Dados ---
if pagina == "📄 Dados":
    st.title("📄 Dados Brutos - HISTORICO_BDO")
    lideres = df['LIDER'].dropna().unique()
    lider_sel = st.selectbox("Filtrar por LÍDER", ["Todos"] + list(lideres))
    if lider_sel != "Todos":
        df = df[df['LIDER'] == lider_sel]
    st.dataframe(df, use_container_width=True)

# --- Página: Dashboards ---
elif pagina == "📊 Dashboards":
    st.title("📊 Dashboards de Produção")
    if 'PRODUCÃO' in df.columns:
        df['PRODUCÃO'] = pd.to_numeric(df['PRODUCÃO'], errors='coerce')

        # Gráfico de barras
        graf_barra = df.groupby("LIDER")["PRODUCÃO"].sum().reset_index()
        st.subheader("📦 Produção por Líder")
        fig1 = px.bar(graf_barra, x="LIDER", y="PRODUCÃO", text_auto=True)
        st.plotly_chart(fig1, use_container_width=True)

        # Gráfico de pizza
        st.subheader("🥧 Distribuição da Produção (%)")
        fig2 = px.pie(graf_barra, names="LIDER", values="PRODUCÃO")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Coluna 'PRODUCÃO' não encontrada.")

# --- Outras páginas ---
elif pagina == "🧪 Qualidade":
    st.title("🧪 Qualidade")
    st.info("🔧 Em construção...")

elif pagina == "💰 DRE":
    st.title("💰 Demonstrativo de Resultados (DRE)")
    st.info("🔧 Em construção...")

elif pagina == "🧑‍💼 RH":
    st.title("🧑‍💼 Recursos Humanos")
    st.info("🔧 Em construção...")
