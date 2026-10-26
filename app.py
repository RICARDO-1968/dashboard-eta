import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuração de tela para celular/tablet
st.set_page_config(page_title="ETA Brasília", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    <h1> { font-size: 20px !important; font-weight: bold; color: #0f3460; }
    <h2> { font-size: 16px !important; font-weight: bold; color: #1f77b4; margin-top: 15px; }
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

# 2. Leitura Blindada das Abas e Padronização de Colunas
@st.cache_data(ttl=2)
def carregar_dados_blindados():
    nome_arquivo = "EQUILIBRIO QUIMICO.xlsx"
    try:
        xls = pd.ExcelFile(nome_arquivo)
        listagem_abas = xls.sheet_names
        
        # Carrega as abas por ordem física
        df_quimico = pd.read_excel(nome_arquivo, sheet_name=0)
        df_carga = pd.read_excel(nome_arquivo, sheet_name=1 if len(listagem_abas) > 1 else 0)
        
        # Remove espaços e força colunas para maiúsculas
        df_quimico.columns = df_quimico.columns.str.strip().str.upper()
        df_carga.columns = df_carga.columns.str.strip().str.upper()
        
        # Encontra a coluna de data de forma inteligente
        for df in [df_quimico, df_carga]:
            colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
            if colunas_data:
                df[colunas_data[0]] = pd.to_datetime(df[colunas_data[0]], errors='coerce')
                df.rename(columns={colunas_data[0]: "DATA_PROCESSO"}, inplace=True)
            elif len(df) > 0:
                df.rename(columns={df.columns[0]: "DATA_PROCESSO"}, inplace=True)
                df["DATA_PROCESSO"] = pd.to_datetime(df["DATA_PROCESSO"], errors='coerce')
                
        return df_quimico, df_carga
    except Exception as e:
        st.error(f"Erro ao processar as colunas da planilha: {e}")
        return None, None

df_q, df_c = carregar_dados_blindados()

if df_q is not None and df_c is not None:
    # --- MENUS DE FILTRO NA BARRA LATERAL ---
    st.sidebar.markdown("### 🖥️ Controle de Processo")
    if st.sidebar.button("🔄 Limpar Cache e Recarregar"):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⏳ Filtros do Painel")
    
    if "DATA_PROCESSO" in df_q.columns and df_q["DATA_PROCESSO"].notna().any():
        df_q = df_q[df_q["DATA_PROCESSO"].notna()]
        data_min = df_q["DATA_PROCESSO"].min().date()
        data_max = df_q["DATA_PROCESSO"].max().date()
        
        data_ini = st.sidebar.date_input("Data inicial", data_min)
        data_fim = st.sidebar.date_input("Data final", data_max)
        
        df_q_f = df_q[(df_q["DATA_PROCESSO"].dt.date >= data_ini) & (df_q["DATA_PROCESSO"].dt.date <= data_fim)]
        
        if "DATA_PROCESSO" in df_c.columns:
            df_c = df_c[df_c["DATA_PROCESSO"].notna()]
            df_c_f = df_c[(df_c["DATA_PROCESSO"].dt.date >= data_ini) & (df_c["DATA_PROCESSO"].dt.date <= data_fim)]
        else:
            df_c_f = df_c
    else:
        df_q_f, df_c_f = df_q, df_c

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("Equilíbrio químico integrado")
    st.caption("Gráficos de dispersões e correlações lineares (r) atualizados via GitHub.")
    
    # Função matemática de cruzamento corrigida (plotar_universal)
    def plotar_universal(df, col_x, col_y_par, col_y_impar, lbl_x, lbl_y, tit):
        fig = go.Figure()
        
        cx = col_x.upper()
        cy_p = col_y_par.upper()
        cy_i = col_y_impar.upper()
        
        # Lado Par (Verde)
        if cx in df.columns and cy_p in df.columns:
            df_p = df[[cx, cy_p]].dropna()
            x_arr = pd.to_numeric(df_p[cx], errors='coerce')
            y_arr = pd.to_numeric(df_p[cy_p], errors='coerce')
            validos = np.isfinite(x_arr) & np.isfinite(y_arr)
            x_arr, y_arr = x_arr[validos], y_arr[validos]
            
            if len(x_arr) > 1:
                r_p = np.corrcoef(x_arr, y_arr)[0, 1]
                lbl_p = f'Par (n={len(x_arr)} | r={r_p:.3f})'
            else:
                lbl_p = f'Par (n={len(x_arr)})'
            fig.add_trace(go.Scatter(x=x_arr, y=y_arr, mode='markers', name=lbl_p, marker=dict(color='#009b72', size=5)))
            
        # Lado Ímpar (Roxo)
        if cx in df.columns and cy_i in df.columns:
            df_i = df[[cx, cy_i]].dropna()
            x_arr_i = pd.to_numeric(df_i[cx], errors='coerce')
            y_arr_i = pd.to_numeric(df_i[cy_i], errors='coerce')
            validos_i = np.isfinite(x_arr_i) & np.isfinite(y_arr_i)
            x_arr_i, y_arr_i = x_arr_i[validos_i], y_arr_i[validos_i]
            
            if len(x_arr_i) > 1:
                r_i = np.corrcoef(x_arr_i, y_arr_i)[0, 1]
                lbl_i = f'Ímpar (n={len(x_arr_i)} | r={r_i:.3f})'
            else:
                lbl_i = f'Ímpar (n={len(x_arr_i)})'
            fig.add_trace(go.Scatter(x=x_arr_i, y=y_arr_i, mode='markers', name=lbl_i, marker=dict(color='#6f42c1', size=5)))
            
        fig.update_layout(
            title=dict(text=tit, font=dict(size=13)),
            xaxis_title=lbl_x, yaxis_title=lbl_y,
            margin=dict(l=10, r=10, t=45, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10))
        )
        return fig

    # --- SEÇÃO 1: ABA QUÍMICA ---
    st.markdown("## 📊 Relações Operacionais (Primeira Aba)")
    
    st.plotly_chart(plotar_universal(
        df_q_f, 
        "LADO PAR A/S (RELAÇÃO  MASSA DE AR / MASSA DE SST", 
        "ÁGUA BRUTA TURB (uT)", 
        "ÁGUA BRUTA TURB (uT)", 
        "A/S", "Turbidez Bruta (uT)", "A/S × Turbidez da Água Bruta"
    ), use_container_width=True)
    
    st.plotly_chart(plotar_universal(
        df_q_f, 
        "LADO PAR A/S (RELAÇÃO  MASSA DE AR / MASSA DE SST", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "A/S", "Turbidez Clarificada (uT)", "A/S × Turbidez Clarificada"
    ), use_container_width=True)
    
    st.plotly_chart(plotar_universal(
        df_q_f, 
        "LADO PAR FLOTAÇÃO Pressão Sat. (bar)", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO Pressão Sat. (bar)", 
        "Pressão Sat. (bar)", "Turbidez Clarificada (uT)", "Pressão de Saturação × Clarificada"
    ), use_container_width=True)

    st.plotly_chart(plotar_universal(
        df_q_f, 
        "LADO PAR FLOTAÇÃO Vazão Rec.(L/s)", 
        "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
        "LADO ÍMPAR FLOTAÇÃO Vazão Rec.(L/s)", 
        "Vazão de Recirculação (L/s)", "Turbidez Clarificada (uT)", "Vazão de Recirculação × Clarificada"
    ), use_container_width=True)

    # --- SEÇÃO 2: ABA CARGA ---
    st.markdown("---")
    st.markdown("## 🧪 Relações Químicas e Dosagem (Segunda Aba)")
    
    st.plotly_chart(plotar_universal(
        df_c_f, 
        "DOS PAC (mg/L)", 
        "LADO PAR ÁGUA COAGULADA pH", 
        "LADO ÍMPAR ÁGUA COAGULADA pH", 
        "DOS PAC (mg/L)", "pH Coagulado", "DOS PAC × pH de Coagulação"
    ), use_container_width=True)
    
    # Procura o termo CARGA (CSV) de forma flexível nas colunas da aba de carga
    col_carga_real = [c for c in df_c_f.columns if "CARGA" in c]
    if col_carga_real:
        st.plotly_chart(plotar_universal(
            df_c_f, 
            col_carga_real[0], 
            "LADO PAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
            "LADO ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)", 
            "Carga (CSV)", "Turbidez Clarificada (uT)", "Carga (CSV) × Turbidez Clarificada"
        ), use_container_width=True)
