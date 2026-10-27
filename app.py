import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. Configuração de Página Otimizada para Celular
st.set_page_config(
    page_title="ETA Brasília",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para compactar os títulos das seções/gráficos no celular
st.markdown("""
    <style>
    .stSubheader {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
        margin-bottom: 2px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Sistema de Proteção por Senha
SENHA_CORRETA = "ETA2026" 

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🧪 Controle ETA Brasília")
    with st.form("login_form"):
        st.subheader("🔒 Acesso Restrito")
        senha_input = st.text_input("Insira a senha para acessar:", type="password")
        botao_login = st.form_submit_button("Entrar")
        if botao_login:
            if senha_input == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# 3. Carregamento e Tratamento dos Dados
@st.cache_data
def carregar_e_tratar_dados():
    df = pd.read_excel("EQUILIBRIO QUIMICO.xlsx", sheet_name="EQUILIBRIO QUIMICO COM CARGA", decimal=",")
    
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

    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors='coerce').dt.date
        df = df.dropna(subset=["DATA"]).sort_values("DATA")
    return df

try:
    df_raw = carregar_e_tratar_dados()
    df_filtrado = df_raw.copy()

    # 4. ABA DE FILTROS (Painel Lateral Retrátil)
    st.sidebar.header("🎛️ Aba de Filtros")
    
    st.sidebar.subheader("📅 Período de Análise")
    min_data_val = df_raw["DATA"].min()
    max_data_val = df_raw["DATA"].max()
    
    data_inicio = st.sidebar.date_input("De:", value=min_data_val, min_value=min_data_val, max_value=max_data_val)
    data_fim = st.sidebar.date_input("Até:", value=max_data_val, min_value=min_data_val, max_value=max_data_val)
    
    df_filtrado = df_filtrado[(df_filtrado["DATA"] >= data_inicio) & (df_filtrado["DATA"] <= data_fim)]

    st.sidebar.subheader("📝 Parâmetros Textuais")
    todas_colunas_solicitadas = [
        "%TOR", "%SM", "%BNN", "TAXA_RECIR. _PAR", "TAXA_RECIR. _ÍMPAR", 
        "TAXA_REMOÇÃO_ÍMPAR", "TAXA_REMOÇÃO_PAR", "FAIXA_ALC_BRUTA", 
        "FAIXA_COR_BRUTA", "FAIXA_TURB_BRUTA", "TIPO_AGUA_BRUTA", 
        "FAIXA_TURB_PAPEL_FILTRO_PAR", "FAIXA_TURB_PAPEL_FILTRO_ÍMPAR", 
        "FAIXA_TURB_CLAR_PAR", "FAIXA_TURB_CLAR_ÍMPAR", "FAIXA_TURB_FILT."
    ]

    for col_nome in todas_colunas_solicitadas:
        colunas_alvo = [c for c in df_raw.columns if c.startswith(col_nome)]
        for col_alvo in colunas_alvo:
            if not pd.api.types.is_numeric_dtype(df_raw[col_alvo]):
                opcoes = sorted([str(x) for x in df_raw[col_alvo].dropna().unique()])
                selecionados = st.sidebar.multiselect(
                    label=f"{col_alvo.replace('_', ' ')}", 
                    options=opcoes, 
                    key=f"filter_widget_{col_alvo}"
                )
                if selecionados:
                    df_filtrado = df_filtrado[df_filtrado[col_alvo].astype(str).isin(selecionados)]

    if st.sidebar.button("🔄 Resetar Todos os Filtros"):
        st.clear_cache()
        st.rerun()

    # 5. PÁGINA PRINCIPAL - DESIGN ULTRA COMPACTO
    st.title("🧪 Painel ETA Brasília")
    st.caption(f"Registros exibidos: {len(df_filtrado)} de {len(df_raw)}")

    col_bruta = next((c for c in df_raw.columns if "BRUTA" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper()), None)
    col_filtrada = next((c for c in df_raw.columns if "FILT" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper() and "PAPEL" not in c.upper()), None)
    col_par = next((c for c in df_raw.columns if "PAR" in c.upper() and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    col_impar = next((c for c in df_raw.columns if ("IMPAR" in c.upper() or "ÍMPAR" in c.upper()) and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    
    col_pac = next((c for c in df_raw.columns if "PAC" in c.upper()), None)
    col_carga = next((c for c in df_raw.columns if "CARGA" in c.upper() or "CSV" in c.upper()), None)

    # --- GRÁFICO 1: Histórico de Turbidezes ---
    st.subheader("📉 Tendência de Turbidezes por Período")
    
    mapeamento_legendas = {}
    colunas_linhas = []
    if col_bruta: 
        mapeamento_legendas[col_bruta] = "Água Bruta"
        colunas_linhas.append(col_bruta)
    if col_filtrada: 
        mapeamento_legendas[col_filtrada] = "Água Filtrada"
        colunas_linhas.append(col_filtrada)
    if col_par: 
        mapeamento_legendas[col_par] = "Clarificada Par"
        colunas_linhas.append(col_par)
    if col_impar: 
        mapeamento_legendas[col_impar] = "Clarificada Ímpar"
        colunas_linhas.append(col_impar)
    
    if colunas_linhas and not df_filtrado.empty:
        fig_linhas = px.line(
            df_filtrado, 
            x="DATA", 
            y=colunas_linhas,
            labels={"value": "uT", "DATA": "Período", "variable": "Parâmetro"}
        )
        fig_linhas.for_each_trace(lambda t: t.update(name=mapeamento_legendas.get(t.name, t.name)))
        fig_linhas.update_traces(line=dict(width=1.2), mode='lines')
        fig_linhas.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig_linhas, use_container_width=True)
    else:
        st.info("Aguardando dados dos filtros aplicados.")

    st.markdown("---")

    # --- GRÁFICO 2: Correlação PAC vs Carga ---
    st.subheader("🎯 Correlação: Dosagem PAC vs Carga (CSV)")
    
    if col_pac and col_carga and not df_filtrado.empty:
        df_trend = df_filtrado[[col_carga, col_pac]].dropna().copy()
        df_trend[col_carga] = pd.to_numeric(df_trend[col_carga], errors='coerce')
        df_trend[col_pac] = pd.to_numeric(df_trend[col_pac], errors='coerce')
        df_trend = df_trend.dropna()

        fig_disp = px.scatter(
            df_filtrado,
            x=col_carga,
            y=col_pac,
            labels={col_carga: "Carga (CSV)", col_pac: "Dosagem PAC"},
            opacity=0.7
        )
        fig_disp.update_traces(marker=dict(size=4, line=dict(width=0.3, color='DarkSlateGrey')))

        if len(df_trend) > 1:
            x_vals = df_trend[col_carga].values
            y_vals = df_trend[col_pac].values
            p = np.polyfit(x_vals, y_vals, 1)
            x_range = np.linspace(x_vals.min(), x_vals.max(), 100)
            y_trend = np.polyval(p, x_range)
            
            fig_disp.add_trace(
                go.Scatter(
                    x=x_range,
                    y=y_trend,
                    mode='lines',
                    name='Tendência',
                    line=dict(color='red', width=1.5, dash='dash')
                )
            )

        fig_disp.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_disp, use_container_width=True)
    else:
        st.info("Aguardando dados dos filtros aplicados.")

except FileNotFoundError:
    st.error("Arquivo de dados não encontrado.")
except Exception as e:
    st.error(f"Erro operacional: {e}")
