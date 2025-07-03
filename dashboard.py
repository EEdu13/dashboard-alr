import streamlit as st
import pandas as pd
from datetime import datetime
from conexao_sql import obter_dados_sharepoint

# ==== CONFIGURAÇÃO VISUAL ====
st.set_page_config("Sistema de Projetos", layout="wide")
st.markdown("""
    <style>
        body { color: white; background-color: #111; }
        .stDataFrame tbody tr td { text-align: center; }
        .stDataFrame { height: auto !important; max-height: none !important; overflow: visible !important; }
    </style>
""", unsafe_allow_html=True)

# ==== LOGIN USANDO SECRETS ====
usuarios_dict = st.secrets["usuarios"]
df_login = pd.DataFrame(usuarios_dict)


df_login["LOGIN"] = df_login["LOGIN"].astype(str).str.lower().str.strip()
df_login["SENHA"] = df_login["SENHA"].astype(str).str.strip()


if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None

if not st.session_state.autenticado:
    st.title("Sistema de Projetos")
    with st.form("login_form"):
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

# ==== DADOS ====
st.title("Sistema de Projetos")
usuario = st.session_state.usuario
df = obter_dados_sharepoint()

# Ajusta colunas
df["Title"] = df["Title"].astype(str).str.strip()
df["PROJETO"] = df["Title"]
df["FAZENDA"] = df["FAZENDA"].astype(str).str.strip()
df["TARIFA"] = pd.to_numeric(df["TARIFA"], errors="coerce").fillna(0)
df["PRODUÇÃO"] = pd.to_numeric(df["PRODU_x00c7__x00c3_O"], errors="coerce").fillna(0)

# Converte datas
df["DATA_EXECUCAO"] = pd.to_datetime(df["DATA_x0020_EXECU_x00c7__x00c3_O"], errors="coerce")
df["FECHAMENTO"] = pd.to_datetime(df["FECHAMENTO"], errors="coerce")
df["FECHAMENTO_FORMATADO"] = df["FECHAMENTO"].dt.strftime("%d/%m/%Y")

# Modalidade
df["MODALIDADE"] = df.get("MOD_x002e_", "").fillna("").replace("None", "")
df["MODALIDADE"] = df["MODALIDADE"].replace("", "—")

# ==== PROJETOS DO USUÁRIO ====
projetos_usuario = (
    df_login[df_login["LOGIN"] == usuario["LOGIN"]]["PROJETO"]
    .astype(str).str.strip().str.split(";").explode().str.strip().unique()
)
projetos_usuario = sorted(p for p in projetos_usuario if p != "")

st.success(f"Bem-vindo, {usuario['USUARIO'].upper()} ({usuario['PERFIL'].upper()})")

# ==== FILTROS ====
st.subheader("Projetos disponíveis")
col1, col2, col3 = st.columns([2, 2, 2])

projetos_opcoes = ["Todos"] + projetos_usuario
with col1:
    projeto = st.selectbox("Selecione um projeto", projetos_opcoes)
with col2:
    data_inicial, data_final = st.date_input(
        "Selecione o intervalo de datas (DATA_EXECUCAO)",
        value=(datetime.today().date(), datetime.today().date()),
        format="DD/MM/YYYY"
    )
with col3:
    fechamento_opcoes = ["Todos"] + sorted(df["FECHAMENTO_FORMATADO"].dropna().unique())
    fechamento = st.selectbox("Filtrar por FECHAMENTO", fechamento_opcoes)

# ==== APLICA FILTROS ====
filtro_data = (df["DATA_EXECUCAO"].dt.date >= data_inicial) & (df["DATA_EXECUCAO"].dt.date <= data_final)

if projeto == "Todos":
    df_filtrado = df[(df["PROJETO"].isin(projetos_usuario)) & filtro_data]
else:
    df_filtrado = df[(df["PROJETO"] == projeto) & filtro_data]

if fechamento != "Todos":
    df_filtrado = df_filtrado[df_filtrado["FECHAMENTO_FORMATADO"] == fechamento]

st.write(f"Total de registros encontrados: {len(df_filtrado)}")

if not df_filtrado.empty:
    df_filtrado["FATURA (R$)"] = df_filtrado["PRODUÇÃO"] * df_filtrado["TARIFA"]

    df_agrupado = (
        df_filtrado.groupby(["PROJETO", "SUPERVISOR", "MODALIDADE", "SERVI_x00c7_O", "MEDIDA"], as_index=False)
        .agg({"PRODUÇÃO": "sum", "FATURA (R$)": "sum"})
        .rename(columns={
            "PROJETO": "Projeto",
            "SUPERVISOR": "Supervisor",
            "MODALIDADE": "Modalidade",
            "SERVI_x00c7_O": "Serviço",
            "MEDIDA": "Medida"
        })
    )

    total_producao = df_agrupado["PRODUÇÃO"].sum()
    total_fatura = df_agrupado["FATURA (R$)"].sum()

    st.markdown(f"""
        <div style='background-color:#004d40;padding:30px;border-radius:15px;text-align:center;color:white;font-size:36px;font-weight:bold;margin-bottom:25px;'>
            💰 TOTAL FATURADO: R$ {total_fatura:,.2f}
        </div>
    """, unsafe_allow_html=True)

    linha_total = pd.DataFrame([{
        "Projeto": "TOTAL GERAL",
        "Supervisor": "",
        "Modalidade": "",
        "Serviço": "",
        "Medida": "",
        "PRODUÇÃO": total_producao,
        "FATURA (R$)": total_fatura
    }])

    df_final = pd.concat([df_agrupado, linha_total], ignore_index=True)
    df_formatado = df_final.style.format({"FATURA (R$)": "R$ {:,.2f}".format, "PRODUÇÃO": "{:,.2f}".format})
    st.dataframe(df_formatado, use_container_width=True)

    # ==== TABELA RESUMO DE MAN E MEC ====
    df_resumo = (
        df_filtrado[df_filtrado["MODALIDADE"].isin(["Man", "Mec"])]
        .groupby("MODALIDADE")
        .agg({"PRODUÇÃO": "sum", "FATURA (R$)": "sum"})
        .reset_index()
    )

    st.markdown("### 💡 Resumo por Modalidade (Man/Mec)")
    st.table(df_resumo.style.format({"FATURA (R$)": "R$ {:,.2f}".format, "PRODUÇÃO": "{:,.2f}".format}))

else:
    st.warning("Nenhum dado encontrado para os filtros aplicados.")
