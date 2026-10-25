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
    h1 { font-size: 24px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# 1. Sistema de Autenticação Simples
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.markdown("<h2 style='text-align: center;'>ETA Brasília</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Acesso ao dashboard integrado</p>", unsafe_allow_html=True)
    with st.form("Login"):
        senha = st.text_input("Senha de Acesso", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            if senha == "eta123":  # Sua senha padrão. Pode mudar depois!
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# 2. Leitura das duas abas do arquivo Excel
@st.cache_data(ttl=30)
def carregar_dados():
    try:
        # Tenta ler o arquivo que você vai subir na mesma pasta
        df_quimico = pd.read_excel("EQUILÍBRIO QUÍMICO H2O.xlsx", sheet_name="EQUILÍBRIO QUÍMICO")
        df_carga = pd.read_excel("EQUILÍBRIO QUÍMICO H2O.xlsx", sheet_name="EQUILÍBRIO QUÍMICO COM CARGA")
        
        # Garante que a coluna de data seja lida corretamente
        for df in [df_quimico, df_carga]:
            if "Data" in df.columns:
                df["Data"] = pd.to_datetime(df["Data"])
        return df_quimico, df_carga
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.info("Certifique-se de que o arquivo 'EQUILÍBRIO QUÍMICO H2O.xlsx' foi enviado corretamente para o GitHub.")
        return None, None

df_q, df_c = carregar_dados()

if df_q is not None and df_c is not None:
    # --- MENUS DE FILTRO NA BARRA LATERAL ---
    st.sidebar.markdown("### 🖥️ Controle de Processo")
    if st.sidebar.button("🔄 Atualizar Painel"):
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⏳ Filtros do Painel")
    
    # Filtro de Data baseado na aba quimica
    data_min = df_q["Data"].min().date() if "Data" in df_q.columns else None
    data_max = df_q["Data"].max().date() if "Data" in df_q.columns else None
    
    if data_min and data_max:
        data_ini = st.sidebar.date_input("Data inicial", data_min)
        data_fim = st.sidebar.date_input("Data final", data_max)
        
        # Filtrando ambos os DataFrames pela data selecionada
        df_q_f = df_q[(df_q["Data"].dt.date >= data_ini) & (df_q["Data"].dt.date <= data_fim)]
        df_c_f = df_c[(df_c["Data"].dt.date >= data_ini) & (df_c["Data"].dt.date <= data_fim)]
    else:
        df_q_f, df_c_f = df_q, df_c

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("Equilíbrio químico integrado")
    st.caption("Visão combinada de captações, coagulação, flotação e clarificação.")
    
    # Função para plotar os gráficos espelhados (Par x Ímpar) com cálculo automático de R
    def plotar_dispersao_lado(df, col_x, col_y_par, col_y_impar, lbl_x, lbl_y, tit):
        fig = go.Figure()
        if col_x in df.columns:
            if col_y_par in df.columns:
                df_p = df[[col_x, col_y_par]].dropna()
                r_p = df_p[col_x].corr(df_p[col_y_par]) if len(df_p) > 1 else 0
                fig.add_trace(go.Scatter(x=df_p[col_x], y=df_p[col_y_par], mode='markers',
                                         name=f'Par (n={len(df_p)} | r={r_p:.3f})', marker=dict(color='#009b72', size=5)))
            if col_y_impar in df.columns:
                df_i = df[[col_x, col_y_impar]].dropna()
                r_i = df_i[col_x].corr(df_i[col_y_impar]) if len(df_i) > 1 else 0
                fig.add_trace(go.Scatter(x=df_i[col_x], y=df_i[col_y_impar], mode='markers',
                                         name=f'Ímpar (n={len(df_i)} | r={r_i:.3f})', marker=dict(color='#6f42c1', size=5)))
        fig.update_layout(title=tit, xaxis_title=lbl_x, yaxis_title=lbl_y, margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        return fig

    # Abas visuais no celular para não sobrecarregar a tela pequena
    aba_graficos, aba_carga = st.columns(2)
    
    st.markdown("### Análise da Aba: EQUILÍBRIO QUÍMICO")
    # Gráficos da primeira planilha (Adaptar colunas conforme seu arquivo real)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "AS_mgmg", "Turbidez_Bruta", "Turbidez_Bruta", "A/S (mg/mg)", "Turbidez bruta (uT)", "A/S × turbidez da água bruta"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "AS_mgmg", "Clarificada_Par", "Clarificada_Impar", "A/S (mg/mg)", "Turbidez clarificada (uT)", "A/S × turbidez clarificada"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "Pressao_Sat", "Clarificada_Par", "Clarificada_Impar", "Pressão Sat. (bar)", "Turbidez clarificada (uT)", "Pressão de saturação × clarificada"), use_container_width=True)

    st.markdown("---")
    st.markdown("### Análise da Aba: EQUILÍBRIO QUÍMICO COM CARGA")
    # Gráficos da segunda planilha
    st.plotly_chart(plotar_dispersao_lado(df_c_f, "PAC_mgL", "pH_Coagulação_Par", "pH_Coagulação_Impar", "PAC (mg/L)", "pH coagulado", "PAC × pH de coagulação"), use_container_width=True)
