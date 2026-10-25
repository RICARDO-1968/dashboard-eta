import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Configuração de tela para celular/tablet
st.set_page_config(page_title="ETA Brasília", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 20px !important; font-weight: bold; color: #0f3460; }
    h2 { font-size: 16px !important; font-weight: bold; color: #1f77b4; margin-top: 15px; }
    h3 { font-size: 14px !important; }
    .stSelectbox label { font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# 1. Sistema de Autenticação
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>ETA Brasília</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Acesso ao dashboard integrado</p>", unsafe_allow_html=True)
    with st.form("Login"):
        senha = st.text_input("Senha de Acesso", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            if senha == "eta123":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# 2. Leitura Robusta das duas abas do Excel
@st.cache_data(ttl=10)
def carregar_dados():
    nome_arquivo = "EQUILIBRIO QUIMICO.xlsx"
    try:
        df_quimico = pd.read_excel(nome_arquivo, sheet_name="EQUILÍBRIO QUÍMICO")
        df_carga = pd.read_excel(nome_arquivo, sheet_name="EQUILÍBRIO QUÍMICO COM CARGA")
        
        # Limpeza básica de espaços extras nos nomes das colunas
        df_quimico.columns = df_quimico.columns.str.strip()
        df_carga.columns = df_carga.columns.str.strip()
        
        # Converte coluna DATA para o formato de data do Python
        if "DATA" in df_quimico.columns:
            df_quimico["DATA"] = pd.to_datetime(df_quimico["DATA"])
        if "DATA" in df_carga.columns:
            df_carga["DATA"] = pd.to_datetime(df_carga["DATA"])
            
        return df_quimico, df_carga
    except Exception as e:
        st.error(f"Erro ao ler as abas do Excel: {e}")
        return None, None

df_q, df_c = carregar_dados()

if df_q is not None and df_c is not None:
    # --- MENUS DE FILTRO NA BARRA LATERAL (Acessível via botão '>>' no topo esquerdo do celular) ---
    st.sidebar.markdown("### 🖥️ Controle de Processo")
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⏳ Filtros do Painel")
    
    # Filtro de Período por Data
    if "DATA" in df_q.columns and len(df_q) > 0:
        data_min = df_q["DATA"].min().date()
        data_max = df_q["DATA"].max().date()
        data_ini = st.sidebar.date_input("Data inicial", data_min)
        data_fim = st.sidebar.date_input("Data final", data_max)
        
        df_q_f = df_q[(df_q["DATA"].dt.date >= data_ini) & (df_q["DATA"].dt.date <= data_fim)]
        df_c_f = df_c[(df_c["DATA"].dt.date >= data_ini) & (df_c["DATA"].dt.date <= data_fim)]
    else:
        df_q_f, df_c_f = df_q, df_c

    # Filtros por faixas textuais se existirem na sua planilha
    if "FAIXA_TURB_BRUTA" in df_q_f.columns:
        faixas_turb = ["Todas"] + list(df_q_f["FAIXA_TURB_BRUTA"].dropna().unique())
        fx_turb_sel = st.sidebar.selectbox("Faixa de Turbidez Bruta", faixas_turb)
        if fx_turb_sel != "Todas":
            df_q_f = df_q_f[df_q_f["FAIXA_TURB_BRUTA"] == fx_turb_sel]

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("Equilíbrio químico integrado")
    st.caption("Visão combinada de captações, coagulação, flotação e clarificação baseada nas planilhas operacionais.")
    
    # Função matemática de dispersão para os pares de interesse (Lado Par x Lado Ímpar)
    def plotar_dispersao_real(df, col_x, col_y_par, col_y_impar, lbl_x, lbl_y, tit):
        fig = go.Figure()
        
        # Plotagem do Lado Par (Verde)
        if col_x in df.columns and col_y_par in df.columns:
            df_p = df[[col_x, col_y_par]].dropna()
            df_p = df_p[np.isfinite(df_p[col_x]) & np.isfinite(df_p[col_y_par])]
            if len(df_p) > 1:
                r_p = np.corrcoef(df_p[col_x].astype(float), df_p[col_y_par].astype(float))[0, 1]
                lbl_p = f'Par (n={len(df_p)} | r={r_p:.3f})'
            else:
                lbl_p = f'Par (n={len(df_p)})'
            fig.add_trace(go.Scatter(x=df_p[col_x], y=df_p[col_y_par], mode='markers', name=lbl_p, marker=dict(color='#009b72', size=5)))
            
        # Plotagem do Lado Ímpar (Roxo)
        if col_x in df.columns and col_y_impar in df.columns:
            df_i = df[[col_x, col_y_impar]].dropna()
            df_i = df_i[np.isfinite(df_i[col_x]) & np.isfinite(df_i[col_y_impar])]
            if len(df_i) > 1:
                r_i = np.corrcoef(df_i[col_x].astype(float), df_i[col_y_impar].astype(float))[0, 1]
                lbl_i = f'Ímpar (n={len(df_i)} | r={r_i:.3f})'
            else:
                lbl_i = f'Ímpar (n={len(df_i)})'
            fig.add_trace(go.Scatter(x=df_i[col_x], y=df_i[col_y_impar], mode='markers', name=lbl_i, marker=dict(color='#6f42c1', size=5)))
            
        fig.update_layout(
            title=dict(text=tit, font=dict(size=14)),
            xaxis_title=lbl_x, 
            yaxis_title=lbl_y, 
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11))
        )
        return fig

    # --- SEÇÃO 1: GRÁFICOS DA PLANILHA EQUILÍBRIO QUÍMICO ---
    st.markdown("## 📊 Relações Operacionais (Aba Química)")
    
    # G1: Relação A/S × Turbidez Bruta
    st.plotly_chart(plotar_dispersao_real(
        df_q_f, 
        "LADO PAR A/S (RELAÇÃO  MASSA DE AR / MASSA DE SST", 
        "ÁGUA BRUTA TURB (uT)", 
        "ÁGUA BRUTA TURB (uT)", 
        "A/S", "Turbidez Bruta (uT)", 
        "A/S × Turbidez da Água Bruta"
    ), use_container_width=True)
    
    # G2: Relação A/S × Turbidez Clarificada
    st.plotly_chart(plotar_dispersao_real(
        df_q_f, 
        "LADO PAR A/S (RELAÇÃO  MASSA DE AR / MASSA DE SST", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "A/S", "Turbidez Clarificada (uT)", 
        "A/S × Turbidez Clarificada"
    ), use_container_width=True)
    
    # G3: Pressão Sat. × Turbidez Clarificada
    st.plotly_chart(plotar_dispersao_real(
        df_q_f, 
        "LADO PAR FLOTAÇÃO Pressão Sat. (bar)", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO Pressão Sat. (bar)", 
        "Pressão Sat. (bar)", "Turbidez Clarificada (uT)", 
        "Pressão de Saturação × Clarificada"
    ), use_container_width=True)
    
    # G4: Vazão de Recirculação × Turbidez Clarificada
    st.plotly_chart(plotar_dispersao_real(
        df_q_f, 
        "LADO PAR FLOTAÇÃO Vazão Rec.(L/s)", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO Vazão Rec.(L/s)", 
        "Vazão de Recirculação (L/s)", "Turbidez Clarificada (uT)", 
        "Vazão de Recirculação × Clarificada"
    ), use_container_width=True)

    # --- SEÇÃO 2: GRÁFICOS DA PLANILHA EQUILÍBRIO QUÍMICO COM CARGA ---
    st.markdown("## 🧪 Relações Químicas e Dosagem (Aba Carga)")
    
    # G5: PAC × pH de Coagulação
    st.plotly_chart(plotar_dispersao_real(
        df_c_f, 
        "DOS PAC (mg/L)", 
        "LADO PAR ÁGUA COAGULADA pH", 
        "LADO ÍMPAR ÁGUA COAGULADA pH", 
        "PAC (mg/L)", "pH Coagulado", 
        "DOS PAC × pH de Coagulação"
    ), use_container_width=True)
    
    # G6: Relação com a Carga Específica (Coluna exclusiva)
    if "CARGA (CSV)" in df_c_f.columns:
        st.plotly_chart(plotar_dispersao_real(
            df_c_f, 
            "CARGA (CSV)", 
            "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
            "LADO ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
            "Carga (CSV)", "Turbidez Clarificada (uT)", 
            "Carga (CSV) × Turbidez Clarificada"
        ), use_container_width=True)
