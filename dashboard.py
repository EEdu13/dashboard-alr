import streamlit as st
import pandas as pd
from datetime import datetime
from conexao_sql import obter_dados_sharepoint, obter_senhas_sql
from st_aggrid import AgGrid, GridOptionsBuilder

# ==== CONFIGURAÇÃO VISUAL ====
st.set_page_config("Sistema de Projetos", layout="wide")
st.markdown("""
    <style>
        body { color: white; background-color: #111; }
        .stDataFrame tbody tr td { text-align: center; }
        .stDataFrame { height: auto !important; max-height: none !important; overflow: visible !important; }
    </style>
""", unsafe_allow_html=True)

# ==== LOGIN USANDO SQL ====
df_login = obter_senhas_sql()
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

# ==== SESSÃO DE LOGIN ====
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
df["PROJETO"] = df["PROJETO"].astype(str).str.strip()
df["FAZENDA"] = df["FAZENDA"].astype(str).str.strip()
df["TARIFA"] = pd.to_numeric(df["TARIFA"], errors="coerce").fillna(0)
df["PRODUÇÃO"] = pd.to_numeric(df["PRODUÇÃO"], errors="coerce").fillna(0)
df["DATA_EXECUÇÃO"] = pd.to_datetime(df["DATA_EXECUÇÃO"], errors="coerce")
df["FECHAMENTO"] = pd.to_datetime(df["FECHAMENTO"], errors="coerce")
df["FECHAMENTO_FORMATADO"] = df["FECHAMENTO"].dt.strftime("%d/%m/%Y")
df["MODALIDADE"] = df.get("MOD", "").fillna("").replace("None", "")
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
        "Selecione o intervalo de datas (DATA_EXECUÇÃO)",
        value=(datetime.today().date(), datetime.today().date()),
        format="DD/MM/YYYY"
    )
with col3:
    fechamento_opcoes = ["Todos"] + df["FECHAMENTO"].dropna().sort_values(ascending=False).dt.strftime("%d/%m/%Y").unique().tolist()
    fechamento = st.selectbox("Filtrar por FECHAMENTO", fechamento_opcoes)

# ==== APLICA FILTROS ====
filtro_data = (df["DATA_EXECUÇÃO"].dt.date >= data_inicial) & (df["DATA_EXECUÇÃO"].dt.date <= data_final)

if projeto == "Todos":
    df_filtrado = df[(df["PROJETO"].isin(projetos_usuario)) & filtro_data]
else:
    df_filtrado = df[(df["PROJETO"] == projeto) & filtro_data]

if fechamento != "Todos":
    df_filtrado = df_filtrado[df_filtrado["FECHAMENTO_FORMATADO"] == fechamento]

st.write(f"Total de registros encontrados: {len(df_filtrado)}")

# ==== RESULTADOS ====
if not df_filtrado.empty:
    # --- Corrigido o nome da coluna e padronizado para FATURAMENTO ---
    df_filtrado["FATURAMENTO"] = df_filtrado["PRODUÇÃO"] * df_filtrado["TARIFA"]

    # ======= Detalhamento por Projeto =======
    df_agrupado = (
        df_filtrado.groupby(["PROJETO", "SUPERVISOR", "MODALIDADE", "SERVIÇO", "MEDIDA"], as_index=False)
        .agg({"PRODUÇÃO": "sum", "FATURAMENTO": "sum"})
        .rename(columns={
            "PROJETO": "Projeto",
            "SUPERVISOR": "Supervisor",
            "MODALIDADE": "Modalidade",
            "SERVIÇO": "Serviço",
            "MEDIDA": "Medida"
        })
    )

    df_agrupado["PRODUÇÃO"] = df_agrupado["PRODUÇÃO"].astype(float)
    df_agrupado["FATURAMENTO"] = df_agrupado["FATURAMENTO"].astype(float)

    total_fatura = df_agrupado["FATURAMENTO"].sum()

    st.markdown(f"""
        <div style='background-color:#004d40;padding:30px;border-radius:15px;text-align:center;color:white;font-size:36px;font-weight:bold;margin-bottom:25px;'>
            💰 TOTAL FATURADO: R$ {total_fatura:,.2f}
        </div>
    """, unsafe_allow_html=True)

    # Subtotais por projeto
    subtotais = df_agrupado.groupby("Projeto").agg({"PRODUÇÃO": "sum", "FATURAMENTO": "sum"}).reset_index()
    subtotais["Supervisor"] = "TOTAL PROJETO"
    subtotais["Modalidade"] = ""
    subtotais["Serviço"] = ""
    subtotais["Medida"] = ""
    df_agrupado_total = pd.concat([df_agrupado, subtotais], ignore_index=True)

    st.markdown("### 📊 Detalhamento por Projeto")
    gb = GridOptionsBuilder.from_dataframe(df_agrupado_total)
    gb.configure_default_column(groupable=True, enableRowGroup=True)
    gb.configure_column("Projeto", rowGroup=True, hide=True)
    gb.configure_column("FATURAMENTO", header_name="FATURAMENTO", type=["numericColumn"], precision=2, valueFormatter="x.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })")
    gb.configure_column("PRODUÇÃO", header_name="PRODUÇÃO", type=["numericColumn"], precision=2, valueFormatter="x.toLocaleString('pt-BR')")
    grid_options = gb.build()
    grid_options["groupIncludeFooter"] = True

    AgGrid(
        df_agrupado_total,
        gridOptions=grid_options,
        use_container_width=True,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True
    )

    # ====== RESUMO AGRUPADO POR PROJETO E MODALIDADE (COM TOTAL) ======

    df_resumo = (
        df_filtrado
        .groupby(["PROJETO", "MODALIDADE"], as_index=False)
        .agg({"PRODUÇÃO": "sum", "FATURAMENTO": "sum"})
        .rename(columns={"PROJETO": "Projeto", "MODALIDADE": "Modalidade"})
    )

    df_resumo["Modalidade"] = df_resumo["Modalidade"].str.upper().str.strip()
    df_resumo["PRODUÇÃO"] = df_resumo["PRODUÇÃO"].astype(float)
    df_resumo["FATURAMENTO"] = df_resumo["FATURAMENTO"].astype(float)
    df_resumo["Projeto"] = df_resumo["Projeto"].fillna("").astype(str)
    df_resumo["Modalidade"] = df_resumo["Modalidade"].fillna("").astype(str)

    # Subtotais
    subtotais_resumo = df_resumo.groupby("Projeto")[["PRODUÇÃO", "FATURAMENTO"]].sum().reset_index()
    subtotais_resumo["Modalidade"] = "TOTAL PROJETO"
    df_resumo_total = pd.concat([df_resumo, subtotais_resumo], ignore_index=True)
    df_resumo_total["ordem"] = df_resumo_total["Modalidade"].apply(lambda x: "ZZZ" if x == "TOTAL PROJETO" else x)
    df_resumo_total = df_resumo_total.sort_values(["Projeto", "ordem"]).drop(columns="ordem").reset_index(drop=True)

    st.markdown("### 💡 Resumo agrupado por Projeto e Modalidade")
    gb2 = GridOptionsBuilder.from_dataframe(df_resumo_total)
    gb2.configure_default_column(groupable=True, enableRowGroup=True, filter=True)
    gb2.configure_column("Projeto", rowGroup=True, hide=True)
    gb2.configure_column("Modalidade", header_name="Modalidade")
    gb2.configure_column("PRODUÇÃO", header_name="PRODUÇÃO", type=["numericColumn"], precision=2, valueFormatter="x.toLocaleString('pt-BR')")
    gb2.configure_column("FATURAMENTO", header_name="FATURAMENTO", type=["numericColumn"], precision=2, valueFormatter="x.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })")
    grid_options2 = gb2.build()
    grid_options2["groupIncludeFooter"] = False

    AgGrid(
        df_resumo_total,
        gridOptions=grid_options2,
        use_container_width=True,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True
    )
else:
    st.warning("Nenhum dado encontrado para os filtros aplicados.")
