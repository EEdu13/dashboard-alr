import streamlit as st
import pandas as pd
from datetime import datetime
from conexao_sql import obter_dados_sharepoint, obter_senhas_sql

# ==== CONFIGURAÇÃO VISUAL ====
st.set_page_config("Sistema de Projetos", layout="wide")
st.markdown("""
    <style>
        body { color: white; background-color: #111; }
        .stDataFrame tbody tr td { text-align: center; }
        .stDataFrame { height: auto !important; max-height: none !important; overflow: visible !important; }
    </style>
""", unsafe_allow_html=True)

# ==== FUNÇÃO PARA CRIAR TABELA HIERÁRQUICA ====
def criar_tabela_hierarquica_projetos(df, nivel1, nivel2=None, nivel3=None):
    """
    Cria tabela hierárquica customizada para dados de projetos
    """
    
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def formatar_numero(valor):
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Calcular estrutura hierárquica com dados detalhados
    estrutura = {}
    
    for _, row in df.iterrows():
        chave_n1 = row[nivel1]
        
        if chave_n1 not in estrutura:
            estrutura[chave_n1] = {
                'producao': 0,
                'faturamento': 0,
                'count': 0,
                'detalhes': [],  # Guardar dados detalhados
                'filhos': {}
            }
        
        estrutura[chave_n1]['producao'] += row['PRODUÇÃO']
        estrutura[chave_n1]['faturamento'] += row['FATURAMENTO']
        estrutura[chave_n1]['count'] += 1
        
        # Adicionar dados detalhados AGRUPADOS (sem FAZENDA)
        detalhe = {
            'supervisor': row.get('SUPERVISOR', '—'),
            'nome_lider': row.get('NOME_DO_LIDER', '—'),
            'modalidade': row.get('MODALIDADE', '—'),
            'servico': row.get('SERVIÇO', '—'),
            'medida': row.get('MEDIDA', '—'),
            'producao': row['PRODUÇÃO'],
            'faturamento': row['FATURAMENTO']
        }
        
        # Criar chave única para agrupamento (sem fazenda)
        chave_agrupamento = f"{detalhe['supervisor']}|{detalhe['nome_lider']}|{detalhe['modalidade']}|{detalhe['servico']}|{detalhe['medida']}"
        
        # Verificar se já existe esse agrupamento
        encontrou = False
        for i, det_existente in enumerate(estrutura[chave_n1]['detalhes']):
            chave_existente = f"{det_existente['supervisor']}|{det_existente['nome_lider']}|{det_existente['modalidade']}|{det_existente['servico']}|{det_existente['medida']}"
            if chave_existente == chave_agrupamento:
                # Somar os valores
                estrutura[chave_n1]['detalhes'][i]['producao'] += detalhe['producao']
                estrutura[chave_n1]['detalhes'][i]['faturamento'] += detalhe['faturamento']
                encontrou = True
                break
        
        if not encontrou:
            estrutura[chave_n1]['detalhes'].append(detalhe)
        
        if nivel2:
            chave_n2 = row[nivel2]
            if chave_n2 not in estrutura[chave_n1]['filhos']:
                estrutura[chave_n1]['filhos'][chave_n2] = {
                    'producao': 0,
                    'faturamento': 0,
                    'count': 0,
                    'detalhes': [],
                    'filhos': {}
                }
            
            estrutura[chave_n1]['filhos'][chave_n2]['producao'] += row['PRODUÇÃO']
            estrutura[chave_n1]['filhos'][chave_n2]['faturamento'] += row['FATURAMENTO']
            estrutura[chave_n1]['filhos'][chave_n2]['count'] += 1
            estrutura[chave_n1]['filhos'][chave_n2]['detalhes'].append(detalhe)

    # Calcular totais gerais
    total_producao = df['PRODUÇÃO'].sum()
    total_faturamento = df['FATURAMENTO'].sum()
    total_registros = len(df)

    # HTML/CSS/JS
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            .container {{
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background: #f8fafc;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: repeating-linear-gradient(
                    45deg,
                    transparent,
                    transparent 10px,
                    rgba(255,255,255,0.05) 10px,
                    rgba(255,255,255,0.05) 20px
                );
                animation: slide 20s linear infinite;
            }}
            
            @keyframes slide {{
                0% {{ transform: translateX(-50px) translateY(-50px); }}
                100% {{ transform: translateX(0px) translateY(0px); }}
            }}
            
            .header h2 {{
                position: relative;
                z-index: 1;
                font-size: 1.5em;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}
            
            .totals-bar {{
                background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                color: white;
                padding: 12px 20px;
                display: flex;
                justify-content: space-around;
                font-size: 0.9em;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            .total-item {{
                text-align: center;
            }}
            
            .total-label {{
                font-size: 0.8em;
                opacity: 0.8;
                margin-bottom: 2px;
            }}
            
            .total-value {{
                font-weight: bold;
                font-size: 1.1em;
            }}
            
            .tabela {{
                width: 100%;
                border-collapse: collapse;
                background: white;
            }}
            
            .nivel1 {{
                background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                border-left: 5px solid #2c5aa0;
            }}
            
            .nivel1:hover {{
                background: linear-gradient(135deg, #3182ce 0%, #2c5aa0 100%);
                transform: translateX(2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            .nivel2 {{
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                border-left: 5px solid #2f855a;
                display: none;
            }}
            
            .nivel2:hover {{
                background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
                transform: translateX(4px);
            }}
            
            .nivel-detalhes {{
                background: #ffffff;
                border-left: 4px solid #667eea;
                border-bottom: 1px solid #e2e8f0;
                font-size: 0.9em;
            }}
            
            .detalhes-grid {{
                display: grid;
                grid-template-columns: 1.5fr 1.5fr 1.5fr 2.5fr 1fr 1.2fr 1.5fr;
                gap: 10px;
                padding: 8px 16px;
                align-items: center;
                border-bottom: 1px solid #f0f0f0;
            }}
            
            .detalhes-header {{
                background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
                font-weight: 600;
                color: #2d3748;
                font-size: 0.85em;
                padding: 8px 16px;
                border-bottom: 2px solid #a0aec0;
            }}
            
            .detalhe-item {{
                padding: 6px 0;
                color: #4a5568;
            }}
            
            .detalhe-valor {{
                font-weight: 600;
                color: #2d3748;
            }}
            
            .detalhe-moeda {{
                color: #38a169;
                font-weight: bold;
            }}
            
            .cell {{
                padding: 12px 16px;
                position: relative;
                border: none;
            }}
            
            .nivel1 .cell {{
                padding: 16px 20px;
            }}
            
            .nivel2 .cell {{
                padding: 12px 16px;
                padding-left: 40px;
            }}
            
            .nivel3 .cell {{
                padding: 10px 16px;
                padding-left: 60px;
            }}
            
            .icone {{
                display: inline-block;
                margin-right: 10px;
                transition: transform 0.3s ease;
                font-size: 0.9em;
            }}
            
            .icone.expandido {{
                transform: rotate(90deg);
            }}
            
            .valores {{
                float: right;
                display: flex;
                gap: 15px;
                align-items: center;
            }}
            
            .valor-item {{
                background: rgba(255,255,255,0.2);
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.85em;
                backdrop-filter: blur(10px);
            }}
            
            .nivel3 .valor-item {{
                background: #667eea;
                color: white;
            }}
            
            .stats {{
                font-size: 0.8em;
                opacity: 0.9;
                margin-top: 4px;
            }}
            
            .badge {{
                background: rgba(255,255,255,0.3);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.7em;
                margin-left: 8px;
            }}
            
            .nivel3 .badge {{
                background: #e2e8f0;
                color: #4a5568;
            }}
            
            .controls {{
                padding: 16px 20px;
                background: #f7fafc;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                align-items: center;
            }}
            
            .btn {{
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.85em;
                transition: all 0.2s ease;
                font-weight: 500;
            }}
            
            .btn-primary {{
                background: #667eea;
                color: white;
            }}
            
            .btn-primary:hover {{
                background: #5a67d8;
                transform: translateY(-1px);
            }}
            
            .btn-secondary {{
                background: #e2e8f0;
                color: #4a5568;
            }}
            
            .btn-secondary:hover {{
                background: #cbd5e0;
            }}
            
            .info-text {{
                margin-left: auto;
                color: #718096;
                font-size: 0.9em;
            }}
            
            @keyframes fadeIn {{
                from {{
                    opacity: 0;
                    transform: translateY(-10px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .show {{
                display: table-row !important;
                animation: fadeIn 0.3s ease-out;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 Análise de Projetos - {nivel1}{f' › {nivel2}' if nivel2 else ''}{f' › {nivel3}' if nivel3 else ''}</h2>
            </div>
            
            <div class="totals-bar">
                <div class="total-item">
                    <div class="total-label">📦 Total de Registros</div>
                    <div class="total-value">{total_registros:,}</div>
                </div>
                <div class="total-item">
                    <div class="total-label">🏭 Produção Total</div>
                    <div class="total-value">{formatar_numero(total_producao)}</div>
                </div>
                <div class="total-item">
                    <div class="total-label">💰 Faturamento Total</div>
                    <div class="total-value">{formatar_moeda(total_faturamento)}</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-primary" onclick="expandirTodos()">📂 Expandir Todos</button>
                <button class="btn btn-secondary" onclick="recolherTodos()">📁 Recolher Todos</button>
                <span class="info-text">
                    Clique nas linhas para expandir/recolher detalhes
                </span>
            </div>
            
            <table class="tabela">
    """
    
    # Gerar linhas da tabela
    for cat1, dados1 in estrutura.items():
        cat1_id = str(cat1).replace(' ', '_').replace('.', '_').replace('&', '_').replace('/', '_')
        
        # Nível 1 (Principal)
        html_content += f"""
                <tr class="nivel1" onclick="toggleNivel1('{cat1_id}')">
                    <td class="cell">
                        <span class="icone" id="icone1_{cat1_id}">▶</span>
                        <strong>{cat1}</strong>
                        <span class="badge">{dados1['count']} registros</span>
                        <div class="valores">
                            <span class="valor-item">🏭 {formatar_numero(dados1['producao'])}</span>
                            <span class="valor-item">💰 {formatar_moeda(dados1['faturamento'])}</span>
                        </div>
                        <div class="stats">
                            Faturamento médio por registro: {formatar_moeda(dados1['faturamento']/dados1['count'] if dados1['count'] > 0 else 0)}
                        </div>
                    </td>
                </tr>
        """
        
        # Dados detalhados (sempre mostrados após expandir o nível 1)
        html_content += f"""
                <tr class="nivel-detalhes grupo1_{cat1_id}" style="display: none;">
                    <td style="padding: 0;">
                        <div class="detalhes-header detalhes-grid">
                            <div><strong>👤 Supervisor</strong></div>   
                            <div><strong>🎯 Nome do Líder</strong></div>
                            <div><strong>📋 Modalidade</strong></div>
                            <div><strong>🔧 Serviço</strong></div>
                            <div><strong>📏 Medida</strong></div>
                            <div><strong>🏭 Produção</strong></div>
                            <div><strong>💰 Faturamento</strong></div>
                        </div>
        """
        
        # Mostrar detalhes agrupados (sem fazenda)
        for detalhe in dados1['detalhes']:
            html_content += f"""
                    <div class="detalhes-grid">
                        <div class="detalhe-item">{detalhe['supervisor']}</div>
                        <div class="detalhe-item">{detalhe['nome_lider']}</div>
                        <div class="detalhe-item">{detalhe['modalidade']}</div>
                        <div class="detalhe-item">{detalhe['servico']}</div>
                        <div class="detalhe-item">{detalhe['medida']}</div>
                        <div class="detalhe-item detalhe-valor">{formatar_numero(detalhe['producao'])}</div>
                        <div class="detalhe-item detalhe-moeda">{formatar_moeda(detalhe['faturamento'])}</div>
                    </div>
            """
        
        html_content += """
                    </td>
                </tr>
        """
        
        # Nível 2 (se configurado)
        if nivel2:
            for cat2, dados2 in dados1['filhos'].items():
                cat2_id = f"{cat1_id}_{str(cat2).replace(' ', '_').replace('.', '_').replace('&', '_').replace('/', '_')}"
                
                html_content += f"""
                <tr class="nivel2 grupo1_{cat1_id}" onclick="toggleNivel2('{cat2_id}')" style="display: none;">
                    <td class="cell">
                        <span class="icone" id="icone2_{cat2_id}">▶</span>
                        {cat2}
                        <span class="badge">{dados2['count']} registros</span>
                        <div class="valores">
                            <span class="valor-item">🏭 {formatar_numero(dados2['producao'])}</span>
                            <span class="valor-item">💰 {formatar_moeda(dados2['faturamento'])}</span>
                        </div>
                    </td>
                </tr>
                """
    
    html_content += """
            </table>
        </div>
        
        <script>
            function toggleNivel1(categoriaId) {
                const elementos = document.querySelectorAll('.grupo1_' + categoriaId);
                const icone = document.getElementById('icone1_' + categoriaId);
                
                let mostrar = elementos.length === 0 || elementos[0].style.display !== 'table-row';
                
                elementos.forEach(function(elemento) {
                    if (mostrar) {
                        elemento.style.display = 'table-row';
                        elemento.classList.add('show');
                    } else {
                        elemento.style.display = 'none';
                        elemento.classList.remove('show');
                        
                        // Recolher filhos também
                        const filhos = elemento.className.match(/grupo2_([^\\s]+)/);
                        if (filhos) {
                            const filhosElementos = document.querySelectorAll('.grupo2_' + filhos[1]);
                            filhosElementos.forEach(function(filho) {
                                filho.style.display = 'none';
                                filho.classList.remove('show');
                            });
                            const iconeFilho = document.getElementById('icone2_' + filhos[1]);
                            if (iconeFilho) {
                                iconeFilho.innerHTML = '▶';
                                iconeFilho.classList.remove('expandido');
                            }
                        }
                    }
                });
                
                if (mostrar) {
                    icone.innerHTML = '▼';
                    icone.classList.add('expandido');
                } else {
                    icone.innerHTML = '▶';
                    icone.classList.remove('expandido');
                }
            }
            
            function toggleNivel2(categoriaId) {
                const elementos = document.querySelectorAll('.grupo2_' + categoriaId);
                const icone = document.getElementById('icone2_' + categoriaId);
                
                if (!icone) return;
                
                let mostrar = elementos.length === 0 || elementos[0].style.display !== 'table-row';
                
                elementos.forEach(function(elemento) {
                    if (mostrar) {
                        elemento.style.display = 'table-row';
                        elemento.classList.add('show');
                    } else {
                        elemento.style.display = 'none';
                        elemento.classList.remove('show');
                    }
                });
                
                if (mostrar) {
                    icone.innerHTML = '▼';
                    icone.classList.add('expandido');
                } else {
                    icone.innerHTML = '▶';
                    icone.classList.remove('expandido');
                }
            }
            
            function expandirTodos() {
                // Expandir nível 1
                document.querySelectorAll('.nivel1').forEach(function(el) {
                    const match = el.onclick.toString().match(/toggleNivel1\\('([^']+)'\\)/);
                    if (match) {
                        const elementos = document.querySelectorAll('.grupo1_' + match[1]);
                        const icone = document.getElementById('icone1_' + match[1]);
                        
                        elementos.forEach(function(elemento) {
                            elemento.style.display = 'table-row';
                            elemento.classList.add('show');
                        });
                        
                        if (icone) {
                            icone.innerHTML = '▼';
                            icone.classList.add('expandido');
                        }
                    }
                });
                
                // Expandir nível 2
                document.querySelectorAll('.nivel2').forEach(function(el) {
                    const match = el.onclick ? el.onclick.toString().match(/toggleNivel2\\('([^']+)'\\)/) : null;
                    if (match) {
                        const elementos = document.querySelectorAll('.grupo2_' + match[1]);
                        const icone = document.getElementById('icone2_' + match[1]);
                        
                        elementos.forEach(function(elemento) {
                            elemento.style.display = 'table-row';
                            elemento.classList.add('show');
                        });
                        
                        if (icone) {
                            icone.innerHTML = '▼';
                            icone.classList.add('expandido');
                        }
                    }
                });
            }
            
            function recolherTodos() {
                // Recolher todos os níveis
                document.querySelectorAll('.nivel-detalhes, .nivel2').forEach(function(el) {
                    el.style.display = 'none';
                    el.classList.remove('show');
                });
                
                // Resetar todos os ícones
                document.querySelectorAll('.icone').forEach(function(icone) {
                    icone.innerHTML = '▶';
                    icone.classList.remove('expandido');
                });
            }
            
            // Auto-expandir primeiro item
            setTimeout(function() {
                const primeiroNivel1 = document.querySelector('.nivel1');
                if (primeiroNivel1) {
                    primeiroNivel1.click();
                }
            }, 500);
        </script>
    </body>
    </html>
    """
    
    return html_content

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
    # --- Calcula FATURAMENTO ---
    df_filtrado["FATURAMENTO"] = df_filtrado["PRODUÇÃO"] * df_filtrado["TARIFA"]

    # ==== CONFIGURAÇÃO DA TABELA HIERÁRQUICA ====
    st.markdown("---")
    
    # Controles para configurar a hierarquia
    col1, col2, col3, col4 = st.columns(4)
    
    colunas_disponiveis = ['PROJETO', 'SUPERVISOR', 'MODALIDADE', 'SERVIÇO', 'MEDIDA']
    colunas_disponiveis = [col for col in colunas_disponiveis if col in df_filtrado.columns]
    
    with col1:
        nivel1 = st.selectbox("📊 Nível Principal", colunas_disponiveis, index=0, key="nivel1")
    
    with col2:
        usar_nivel2 = st.checkbox("Adicionar 2º Nível", value=True, key="nivel2_check")
        nivel2 = None
        if usar_nivel2:
            opcoes_nivel2 = [col for col in colunas_disponiveis if col != nivel1]
            if opcoes_nivel2:
                nivel2 = st.selectbox("2º Nível", opcoes_nivel2, index=0, key="nivel2")
    
    with col3:
        usar_nivel3 = st.checkbox("Adicionar 3º Nível", value=False, disabled=True, key="nivel3_check")
        st.write("_3º nível desabilitado_")
        nivel3 = None
    
    with col4:
        altura_tabela = st.slider("Altura da Tabela", 400, 800, 600, key="altura")
    
    st.markdown("---")
    
    # ======= TABELA HIERÁRQUICA PRINCIPAL =======
    if nivel1:
        html_tabela = criar_tabela_hierarquica_projetos(
            df_filtrado, nivel1, nivel2, nivel3
        )
        st.components.v1.html(html_tabela, height=altura_tabela, scrolling=True)
    
    # ======= DADOS BRUTOS (EXPANSÍVEL) =======
    with st.expander("📋 Ver Dados Detalhados"):
        # Selecionar colunas para exibir (sem FAZENDA)
        colunas_exibir = st.multiselect(
            "Selecione as colunas para exibir:",
            df_filtrado.columns.tolist(),
            default=['PROJETO', 'SUPERVISOR', 'MODALIDADE', 'SERVIÇO', 'PRODUÇÃO', 'FATURAMENTO', 'DATA_EXECUÇÃO']
        )
        
        if colunas_exibir:
            df_exibir = df_filtrado[colunas_exibir].copy()
            
            # Agrupar dados se houver colunas categóricas e numéricas
            colunas_numericas = ['PRODUÇÃO', 'FATURAMENTO', 'TARIFA']
            colunas_numericas_presentes = [col for col in colunas_numericas if col in df_exibir.columns]
            colunas_categoricas = [col for col in df_exibir.columns if col not in colunas_numericas_presentes]
            
            if colunas_numericas_presentes and colunas_categoricas:
                # Agrupar e somar valores numéricos
                df_exibir = df_exibir.groupby(colunas_categoricas, as_index=False)[colunas_numericas_presentes].sum()
            
            # Formatar colunas monetárias e numéricas
            if 'FATURAMENTO' in df_exibir.columns:
                df_exibir['FATURAMENTO'] = df_exibir['FATURAMENTO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            if 'PRODUÇÃO' in df_exibir.columns:
                df_exibir['PRODUÇÃO'] = df_exibir['PRODUÇÃO'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            if 'TARIFA' in df_exibir.columns:
                df_exibir['TARIFA'] = df_exibir['TARIFA'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            st.dataframe(df_exibir, use_container_width=True)
            
            # Mostrar informação sobre agrupamento
            if len(df_exibir) < len(df_filtrado):
                st.info(f"📊 Dados agrupados: {len(df_filtrado)} registros originais → {len(df_exibir)} registros agrupados")
            
            # Botão para download
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV (dados originais)",
                data=csv,
                file_name=f"dados_projetos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # ======= RESUMO ESTATÍSTICO =======
    with st.expander("📊 Resumo Estatístico"):
        # Função para formatar moeda (definir antes de usar)
        def formatar_moeda(valor):
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Métricas Gerais")
            
            # Métricas principais
            total_producao = df_filtrado['PRODUÇÃO'].sum()
            total_faturamento = df_filtrado['FATURAMENTO'].sum()
            media_faturamento = df_filtrado['FATURAMENTO'].mean()
            total_registros = len(df_filtrado)
            
            st.metric("Total de Registros", f"{total_registros:,}")
            st.metric("Produção Total", f"{total_producao:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            st.metric("Faturamento Total", formatar_moeda(total_faturamento))
            st.metric("Faturamento Médio", formatar_moeda(media_faturamento))
        
        with col2:
            st.subheader("🏆 Rankings")
            
            # Top 5 por Projeto
            if 'PROJETO' in df_filtrado.columns:
                st.write("**Top 5 Projetos por Faturamento:**")
                top_projetos = df_filtrado.groupby('PROJETO')['FATURAMENTO'].sum().sort_values(ascending=False).head(5)
                for i, (projeto, valor) in enumerate(top_projetos.items(), 1):
                    st.write(f"{i}. **{projeto}**: {formatar_moeda(valor)}")
            
            # Top 5 por Supervisor (se existir)
            if 'SUPERVISOR' in df_filtrado.columns:
                st.write("**Top 5 Supervisores por Faturamento:**")
                top_supervisores = df_filtrado.groupby('SUPERVISOR')['FATURAMENTO'].sum().sort_values(ascending=False).head(5)
                for i, (supervisor, valor) in enumerate(top_supervisores.items(), 1):
                    st.write(f"{i}. **{supervisor}**: {formatar_moeda(valor)}")
        
        # Gráficos de distribuição
        st.subheader("📊 Distribuições")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'PROJETO' in df_filtrado.columns:
                st.write("**Faturamento por Projeto:**")
                chart_data = df_filtrado.groupby('PROJETO')['FATURAMENTO'].sum().reset_index()
                st.bar_chart(chart_data.set_index('PROJETO')['FATURAMENTO'])
                
                # Mostrar valores formatados
                st.write("**Valores detalhados:**")
                for _, row in chart_data.iterrows():
                    st.write(f"• {row['PROJETO']}: {formatar_moeda(row['FATURAMENTO'])}")
        
        with col2:
            if 'MODALIDADE' in df_filtrado.columns:
                st.write("**Faturamento por Modalidade:**")
                chart_data = df_filtrado.groupby('MODALIDADE')['FATURAMENTO'].sum().reset_index()
                st.bar_chart(chart_data.set_index('MODALIDADE')['FATURAMENTO'])
                
                # Mostrar valores formatados
                st.write("**Valores detalhados:**")
                for _, row in chart_data.iterrows():
                    st.write(f"• {row['MODALIDADE']}: {formatar_moeda(row['FATURAMENTO'])}")

else:
    st.warning("Nenhum dado encontrado para os filtros aplicados.")
    
    # Sugestões quando não há dados
    st.info("""
    **💡 Sugestões:**
    - Verifique se as datas selecionadas estão corretas
    - Tente expandir o intervalo de datas
    - Verifique se há dados para o projeto selecionado
    - Entre em contato com o administrador se o problema persistir
    """)

# ==== RODAPÉ ====
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Atualizar Dados"):
        st.rerun()

with col2:
    if st.button("🚪 Logout"):
        st.session_state.autenticado = False
        st.session_state.usuario = None
        st.rerun()

with col3:
    st.write(f"**Usuário:** {usuario['USUARIO']}")
    st.write(f"**Perfil:** {usuario['PERFIL']}")

# ==== INFORMAÇÕES DE DEBUG (apenas para desenvolvimento) ====
if st.checkbox("🔧 Modo Debug", value=False):
    st.subheader("Debug - Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Colunas do DataFrame:**")
        st.write(list(df.columns))
        st.write("**Projetos do Usuário:**")
        st.write(projetos_usuario)
    
    with col2:
        st.write("**Dados do Usuário:**")
        st.write(usuario)
        st.write("**Filtros Aplicados:**")
        st.write({
            "Projeto": projeto,
            "Data Inicial": data_inicial,
            "Data Final": data_final,
            "Fechamento": fechamento
        })