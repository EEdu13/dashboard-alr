import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
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
    senha_segura = quote_plus("Senhaforte123!")
    engine = create_engine(
        f"mssql+pyodbc://gestaoti:{senha_segura}@alrflorestal.database.windows.net/Tabela_teste"
        "?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
    )
    query = "SELECT TOP 1000 * FROM HISTORICO_BDO ORDER BY ID DESC"
    df = pd.read_sql(query, engine)

except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()

# --- Página: Dados (com AgGrid) ---
if pagina == "📄 Dados":
    st.title("📄 Dados Brutos - HISTORICO_BDO")

    lideres = df['LIDER'].dropna().unique()
    lider_sel = st.selectbox("Filtrar por LÍDER", ["Todos"] + list(lideres))
    if lider_sel != "Todos":
        df = df[df['LIDER'] == lider_sel]

    # Configurar grade editável
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, resizable=True, filter=True)
    gb.configure_columns(["PRODUCÃO", "FATURADO"], editable=True, type=["numericColumn"])
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        use_container_width=True
    )

    df_editado = grid_response["data"]

    # Totais
    try:
        total_producao = pd.to_numeric(df_editado["PRODUCÃO"], errors="coerce").sum()
        total_faturado = pd.to_numeric(df_editado["FATURADO"], errors="coerce").sum()
        st.markdown(f"**🧾 Total PRODUCÃO:** {total_producao:,.2f}")
        st.markdown(f"**💰 Total FATURADO:** {total_faturado:,.2f}")
    except Exception as e:
        st.warning(f"Erro ao calcular totais: {e}")

    # Atualização em tempo real no SQL
    with engine.begin() as conn:
        for index, row in df_editado.iterrows():
            try:
                conn.execute(
                    text("""
                        UPDATE HISTORICO_BDO
                        SET PRODUCÃO = :producao,
                            FATURADO = :faturado
                        WHERE ID = :id
                    """),
                    {"producao": row["PRODUCÃO"], "faturado": row["FATURADO"], "id": row["ID"]}
                )
            except Exception as e:
                st.error(f"Erro ao atualizar ID {row['ID']}: {e}")

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

# --- Página: Qualidade ---
elif pagina == "🧪 Qualidade":
    st.title("🧪 Qualidade")
    st.info("🔧 Em construção...")

# --- Página: DRE ---
elif pagina == "💰 DRE":
    st.title("💰 Demonstrativo de Resultados (DRE)")
    st.info("🔧 Em construção...")

# --- Página: RH ---
elif pagina == "🧑‍💼 RH":
    st.title("🧑‍💼 Recursos Humanos")
    st.info("🔧 Em construção...")
