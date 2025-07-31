import streamlit as st
import pandas as pd
from datetime import datetime
from conexao_sql import obter_dados_sharepoint
import plotly.express as px

# ================== CONFIGURAÇÃO VISUAL ==================
st.set_page_config("Sistema de Projetos - Gráficos", layout="wide")
st.markdown("""
    <style>
        body { color: white; background-color: #111; }
        .stDataFrame tbody tr td { text-align: center; }
        .stDataFrame { height: auto !important; max-height: none !important; overflow: visible !important; }
        th { font-weight: bold !important; }
        .logo-container { display: flex; justify-content: center; margin-bottom: 10px; }
        .logo-img { max-width: 200px; height: auto; }
    </style>
""", unsafe_allow_html=True)

# ============ LOGO NO TOPO ============
st.markdown(
    "<div class='logo-container'><img src='data:image/png;base64," +
    st.file_uploader("Logo", type=["png"], key="logo", label_visibility="collapsed").getvalue().decode("latin1") if st.session_state.get("logo") else "" +
    "' class='logo-img'></div>", unsafe_allow_html=True
)

# Se não quiser fazer upload manual toda vez, pode usar local:
# st.image("larsil_logo.png", width=170)

# ================== LOGIN USANDO EXCEL ==================
df_login = pd.read_excel("SENHAS.xlsx")
df_login.columns = df_login.columns.str.upper().str.strip()
df_login["LOGIN"] = df_login["LOGIN"].astype(str).str.lower().str.strip()
df_login["SENHA"] = df_login["SENHA"].astype(str).str.strip()
df_login["USUARIO"] = df_login["USUARIO"].astype(str).str.strip().str.title()
df_login["PERFIL"] = df_login["PERFIL"].astype(str).str.upper().str.strip()
df_login["PROJETO"] = df_login["PROJETO"].astype(str).str.strip()
df_login = (
    df_login.groupby(["LOGIN", "SENHA", "USUARIO", "PERFIL"], as_index=False)
    .agg({"PROJETO": lambda x: ";".join(sorted(set(x)))})
)

# ================== SESSÃO DE LOGIN ==================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

if not st.session_state.autenticado:
    st.title("Sistema de Projetos - Gráficos")
    with st.form("login_form_graficos"):
        login = st.text_input("Login").strip().lower()
        senha = st.text_input("Senha", type="password").strip()
        submitted = st.form_submit_button("Entrar")

    if submitted:
        usuario = df_login[(df_login["LOGIN"] == login) & (df_login["SENHA"] == senha)]
        if not usuario.empty:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Login ou senha inválidos.")
    st.stop()

usuario = st.session_state.usuario

# ================== DADOS ==================
df = obter_dados_sharepoint()
df["PROJETO"] = df["PROJETO"].astype(str).str.strip()
df["FAZENDA"] = df["FAZENDA"].astype(str).str.strip()
df["TARIFA"] = pd.to_numeric(df["TARIFA"], errors="coerce").fillna(0)
df["PRODUÇÃO"] = pd.to_numeric(df["PRODUÇÃO"], errors="coerce").fillna(0)
df["DATA_EXECUÇÃO"] = pd.to_datetime(df["DATA_EXECUÇÃO"], errors="coerce")
df["FECHAMENTO"] = pd.to_datetime(df["FECHAMENTO"], errors="coerce")
df["FECHAMENTO_FORMATADO"] = df["FECHAMENTO"].dt.strftime("%d/%m/%Y")
df["MODALIDADE"] = df.get("MOD", "").fillna("").replace("None", "")
df["MODALIDADE"] = df["MODALIDADE"].replace("", "—")

# ================== PROJETOS DO USUÁRIO ==================
projetos_usuario = (
    df_login[df_login["LOGIN"] == usuario["LOGIN"]]["PROJETO"]
    .astype(str).str.strip().str.split(";").explode().str.strip().unique()
)
projetos_usuario = sorted(p for p in projetos_usuario if p != "")

# ================== FILTROS IGUAIS AO DASHBOARD ==================
st.success(f"Bem-vindo, {usuario['USUARIO'].upper()} ({usuario['PERFIL'].upper()})")
with st.sidebar:
    st.markdown("### Filtros")
    projetos_opcoes = ["Todos"] + projetos_usuario
    projeto = st.selectbox("Projeto", projetos_opcoes)
    data_inicial, data_final = st.date_input(
        "Intervalo de datas (DATA_EXECUÇÃO)",
        value=(datetime.today().date(), datetime.today().date()),
        format="DD/MM/YYYY"
    )
    fechamento_opcoes = ["Todos"] + df["FECHAMENTO"].dropna().sort_values(ascending=False).dt.strftime("%d/%m/%Y").unique().tolist()
    fechamento = st.selectbox("Fechamento", fechamento_opcoes)

# ========== FILTROS ==========
filtro_data = (df["DATA_EXECUÇÃO"].dt.date >= data_inicial) & (df["DATA_EXECUÇÃO"].dt.date <= data_final)
if projeto == "Todos":
    df_filtrado = df[(df["PROJETO"].isin(projetos_usuario)) & filtro_data]
else:
    df_filtrado = df[(df["PROJETO"] == projeto) & filtro_data]
if fechamento != "Todos":
    df_filtrado = df_filtrado[df_filtrado["FECHAMENTO_FORMATADO"] == fechamento]

# ================== CRIA FATURAMENTO ==================
if "FATURAMENTO" not in df_filtrado.columns:
    df_filtrado["FATURAMENTO"] = df_filtrado["PRODUÇÃO"] * df_filtrado["TARIFA"]

# ================== GRÁFICO DE PIZZA PEQUENO E NATIVO ==================
st.markdown("### Faturamento por Modalidade")

if not df_filtrado.empty and df_filtrado["FATURAMENTO"].sum() > 0:
    df_graf = (
        df_filtrado.groupby("MODALIDADE")["FATURAMENTO"].sum().reset_index()
        .query("FATURAMENTO > 0")
    )

    fig = px.pie(
        df_graf,
        values="FATURAMENTO",
        names="MODALIDADE",
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    fig.update_traces(
        textinfo="label+percent",
        textfont_size=9,
        marker=dict(line=dict(color='#111', width=1.2))
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        width=180,
        height=180,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#FFF",
    )
    st.plotly_chart(fig, use_container_width=False)
else:
    st.info("Não há dados de faturamento para o filtro selecionado.")
