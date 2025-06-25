import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Plataforma ALR", layout="wide")

# --- USUÁRIOS PERMITIDOS ---
usuarios = {
    "admin": "admin123",
    "alr": "alr2025"
}

# --- LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

def login():
    st.title("🔐 Login - Plataforma ALR")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in usuarios and senha == usuarios[usuario]:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.experimental_rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

if not st.session_state.logado:
    login()

# --- MENU LATERAL ---
st.sidebar.title("📁 Menu")
opcao = st.sidebar.radio("Ir para:", ["📋 Produção", "📊 Dashboards", "✅ Qualidade", "📉 DRE", "👥 RH"])
st.sidebar.markdown(f"👤 Logado como: **{st.session_state.usuario}**")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.experimental_rerun()

# --- CONEXÃO COM SQL E LEITURA DOS DADOS ---
@st.cache_data
def carregar_dados():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=alrflorestal.database.windows.net;'
        'DATABASE=Tabela_teste;'
        'UID=gestaoti;'
        'PWD=Senhaforte123!;'
        'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    )
    query = "SELECT TOP 1000 * FROM HISTORICO_BDO ORDER BY ID DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = carregar_dados()

# --- PÁGINAS ---
if opcao == "📋 Produção":
    st.title("📋 Produção - Histórico de Dados")
    lideres = df['LIDER'].dropna().unique()
    lider_sel = st.selectbox("Filtrar por LÍDER", ["Todos"] + list(lideres))
    if lider_sel != "Todos":
        df = df[df['LIDER'] == lider_sel]
    st.dataframe(df)

elif opcao == "📊 Dashboards":
    st.title("📊 Dashboards de Produção")
    df['PRODUCÃO'] = pd.to_numeric(df['PRODUCÃO'], errors='coerce')
    graf = df.groupby("LIDER")["PRODUCÃO"].sum().reset_index()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Produção por Líder - Barras")
        fig_bar = px.bar(graf, x="LIDER", y="PRODUCÃO", text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("🥧 Participação por Líder - Pizza")
        fig_pizza = px.pie(graf, names="LIDER", values="PRODUCÃO", hole=0.3)
        st.plotly_chart(fig_pizza, use_container_width=True)

elif opcao == "✅ Qualidade":
    st.title("✅ Qualidade")
    st.info("🔧 Em construção...")

elif opcao == "📉 DRE":
    st.title("📉 Demonstração de Resultados")
    st.info("🔧 Em construção...")

elif opcao == "👥 RH":
    st.title("👥 Recursos Humanos")
    st.info("🔧 Em construção...")
