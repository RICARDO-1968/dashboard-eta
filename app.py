import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração de Página Otimizada para Celular
st.set_page_config(
    page_title="ETA Brasília - Controle Químico",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Sistema de Proteção por Senha (Bloqueio de Dados)
# Defina a sua senha substituindo a string abaixo
SENHA_CORRETA = "ETA2026" 

st.title("🧪 Controle ETA Brasília")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    with st.form("login_form"):
        st.subheader("🔒 Acesso Restrito")
        senha_input = st.text_input("Insira a senha para acessar os dados operacionais:", type="password")
        botao_login = st.form_submit_button("Entrar")
        
        if botao_login:
            if senha_input == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta. Acesso negado.")
    st.stop()  # Interrompe a execução do script se não estiver autenticado

# --- A partir daqui, o código só executa se o usuário estiver autenticado ---

# 3. Carregamento e Tratamento Inteligente dos Dados
@st.cache_data
def carregar_e_tratar_dados():
    # Carrega a aba específica tratando a vírgula brasileira
    df = pd.read_excel("EQUILIBRIO QUIMICO.xlsx", sheet_name="EQUILIBRIO QUIMICO COM CARGA", decimal=",")
    
    # Tratamento de Colunas Duplicadas (Turnos lado a lado no Excel)
    colunas_novas = []
    contagem_cols = {}
    for col in df.columns:
        col_clean = str(col).strip()
        if col_clean in contagem_cols:
            contagem_cols[col_clean] += 1
            colunas_novas.append(f"{col_clean}_Turno_{contagem_cols[col_clean]}")
        else:
            contagem_cols[col_clean] = 1
            colunas_novas.append(col_clean)
    df.columns = colunas_novas

    # Força a coluna DATA para formato correto (apenas a data)
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors='coerce').dt.date
        df = df.dropna(subset=["DATA"]).sort_values("DATA")
        
    return df

try:
    df_raw = carregar_e_tratar_dados()
    
    # Mapeamento automático de colunas-chave com base nas suas diretrizes
    cols = df_raw.columns
    col_bruta = next((c for c in cols if "BRUTA" in c.upper() and "TURB" in c.upper()), None)
    col_filtrada = next((c for c in cols if "FILTRADA" in c.upper() and "TURB" in c.upper()), None)
    col_par = next((c for c in cols if "PAR" in c.upper() and "TURB" in c.upper()), None)
    col_impar = next((c for c in cols if "IMPAR" in c.upper() or "ÍMPAR" in c.upper() and "TURB" in c.upper()), None)
    
    col_pac = next((c for c in cols if "PAC" in c.upper()), None)
    col_carga = next((c for c in cols if "CARGA" in c.upper() or "CSV" in c.upper()), None)
    
    col_elevatoria = [c for c in cols if "ELEVATORIA" in c.upper() or "COMBINACAO" in c.upper() or "VAZAO" in c.upper()]

    # 4. Painel de Filtros Avançados por Seleção Direta (Sem Sliders/Datas manuais)
    st.subheader("🎛️ Filtros de Operação")
    
    # Criando colunas de filtros lado a lado para poupar espaço no celular
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        # Filtro de Turbidez da Água Bruta por categorias de valores únicos presentes
        opcoes_bruta = sorted(list(df_raw[col_bruta].dropna().unique())) if col_bruta else []
        turb_bruta_sel = st.multiselect("Turbidez Bruta", options=opcoes_bruta, placeholder="Todas")
        
        # Filtro de Combinação de Elevatórias
        if col_elevatoria:
            opcoes_elev = sorted(list(df_raw[col_elevatoria[0]].dropna().unique()))
            elev_sel = st.multiselect("Combinação Elevatórias", options=opcoes_elev, placeholder="Todas")
        else:
            elev_sel = []

    with f_col2:
        # Filtro de Turbidez da Água Clarificada
        opcoes_clar = sorted(list(df_raw[col_par].dropna().unique())) if col_par else []
        turb_clar_sel = st.multiselect("Turbidez Clarificada", options=opcoes_clar, placeholder="Todas")

    # Aplicação Estrita dos Filtros Selecionados
    df_filtrado = df_raw.copy()
    if turb_bruta_sel:
        df_filtrado = df_filtrado[df_filtrado[col_bruta].isin(turb_bruta_sel)]
    if turb_clar_sel and col_par:
        df_filtrado = df_filtrado[df_filtrado[col_par].isin(turb_clar_sel)]
    if elev_sel and col_elevatoria:
        df_filtrado = df_filtrado[df_filtrado[col_elevatoria[0]].isin(elev_sel)]

    # Botão de Controle de Limpeza/Reset de Filtros
    if st.button("🔄 Resetar Filtros e Atualizar Dados"):
        st.rerun()

    st.markdown("---")

    # 5. Área Exclusiva dos Gráficos (Sem filtros ou escolhas internas)
    st.subheader("📊 Gráficos de Avaliação Química")

    # GRÁFICO 1: Tendência de Turbidezes vs Período (Data)
    st.markdown("**Histórico e Tendência de Turbidezes**")
    
    # Coletando as colunas identificadas que existem no arquivo
    colunas_linhas = [c for c in [col_bruta, col_filtrada, col_par, col_impar] if c is not None]
    
    if colunas_linhas:
        fig_linhas = px.line(
            df_filtrado, 
            x="DATA", 
            y=colunas_linhas,
            labels={"value": "Turbidez (uT)", "DATA": "Período"},
            render_mode="svg" # Garante linhas mais limpas e suaves
        )
        # Customização estética estrita: Linhas finas, sem marcadores (pontos)
        fig_linhas.update_traces(line=dict(width=1.5), marker=None, mode='lines')
        
        # Layout adaptado para celular e legenda interativa nativa do Plotly
        fig_linhas.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig_linhas, use_container_width=True)
    else:
        st.warning("Colunas de turbidez não identificadas com os nomes esperados.")

    st.markdown("---")

    # GRÁFICO 2: Dispersão PAC vs Carga (CSV)
    st.markdown("**Correlação: Dosagem de PAC vs Carga (CSV)**")
    
    if col_pac and col_carga:
        fig_disp = px.scatter(
            df_filtrado,
            x=col_carga,
            y=col_pac,
            labels={col_carga: "Carga (CSV)", col_pac: "Dosagem de PAC"},
            opacity=0.7
        )
        # Ajustando estilo para manter o padrão suave e sem ruídos
        fig_disp.update_traces(marker=dict(size=6, line=dict(width=0.5, color='DarkSlateGrey')))
        fig_disp.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_disp, use_container_width=True)
    else:
        st.warning("Colunas de 'PAC' ou 'Carga/CSV' não localizadas na planilha.")

    # Botão de Logout de Segurança no rodapé
    if st.sidebar.button("🔒 Sair do Painel"):
        st.session_state["autenticado"] = False
        st.rerun()

except FileNotFoundError:
    st.error("❌ Arquivo 'EQUILIBRIO QUIMICO.xlsx' não encontrado na raiz.")
except Exception as e:
    st.error(f"⚠️ Ocorreu um erro no processamento: {e}")
