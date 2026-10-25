
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
    h1 { font-size: 22px !important; font-weight: bold; color: #0f3460; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }
    .stSelectbox label { font-weight: bold; }
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
            if senha == "eta123":  # Sua senha de acesso
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# 2. Leitura das duas abas usando o nome exato encontrado no GitHub
@st.cache_data(ttl=10)
def carregar_dados():
    nome_arquivo = "EQUILIBRIO QUIMICO.xlsx"
    try:
        # Lê de forma dinâmica as abas que existirem no seu arquivo
        xls = pd.ExcelFile(nome_arquivo)
        abas_disponiveis = xls.sheet_names
        
        # Define quais abas carregar com base no seu relato
        aba1 = "EQUILÍBRIO QUÍMICO" if "EQUILÍBRIO QUÍMICO" in abas_disponiveis else abas_disponiveis[0]
        aba2 = "EQUILÍBRIO QUÍMICO COM CARGA" if "EQUILÍBRIO QUÍMICO COM CARGA" in abas_disponiveis else (abas_disponiveis[1] if len(abas_disponiveis) > 1 else abas_disponiveis[0])
        
        df_quimico = pd.read_excel(nome_arquivo, sheet_name=aba1)
        df_carga = pd.read_excel(nome_arquivo, sheet_name=aba2)
        
        # Ajusta maiúsculas e minúsculas das colunas para evitar erros de digitação
        df_quimico.columns = df_quimico.columns.str.strip()
        df_carga.columns = df_carga.columns.str.strip()
        
        for df in [df_quimico, df_carga]:
            if "Data" in df.columns:
                df["Data"] = pd.to_datetime(df["Data"])
        return df_quimico, df_carga
    except Exception as e:
        st.error(f"Erro ao ler as abas do Excel: {e}")
        return None, None

df_q, df_c = carregar_dados()

if df_q is not None and df_c is not None:
    # --- MENUS DE FILTRO NA BARRA LATERAL ---
    st.sidebar.markdown("### 🖥️ Controle de Processo")
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⏳ Filtros do Painel")
    
    # Filtro de Data baseado na aba química
    col_data = "Data" if "Data" in df_q.columns else (df_q.select_dtypes(include=['datetime']).columns[0] if len(df_q.select_dtypes(include=['datetime']).columns) > 0 else None)
    
    if col_data and len(df_q) > 0:
        data_min = df_q[col_data].min().date()
        data_max = df_q[col_data].max().date()
        data_ini = st.sidebar.date_input("Data inicial", data_min)
        data_fim = st.sidebar.date_input("Data final", data_max)
        
        df_q_f = df_q[(df_q[col_data].dt.date >= data_ini) & (df_q[col_data].dt.date <= data_fim)]
        
        if "Data" in df_c.columns:
            df_c_f = df_c[(df_c["Data"].dt.date >= data_ini) & (df_c["Data"].dt.date <= data_fim)]
        else:
            df_c_f = df_c
    else:
        df_q_f, df_c_f = df_q, df_c

    # Filtros por colunas comuns se existirem (Origem/Composição)
    for col_filtro, label in [("Origem_Aba", "Origem / aba"), ("Composicao_Captacao", "Composição das captações")]:
        if col_filtro in df_q_f.columns:
            opcoes = ["Todas"] + list(df_q_f[col_filtro].dropna().unique())
            escolha = st.sidebar.selectbox(label, opcoes)
            if escolha != "Todas":
                df_q_f = df_q_f[df_q_f[col_filtro] == escolha]

    # --- CORPO PRINCIPAL DO DASHBOARD ---
    st.title("Equilíbrio químico integrado")
    st.caption("Visão combinada de captações, coagulação, flotação e clarificação.")
    
    # Função inteligente de dispersão lado a lado (Par x Ímpar) com cálculo automático de R
    def plotar_dispersao_lado(df, col_x, col_y_par, col_y_impar, lbl_x, lbl_y, tit):
        fig = go.Figure()
        
        # Encontra os nomes mais próximos na tabela caso haja diferenças de maiúsculas/minúsculas
        def encontrar_coluna(nome, colunas):
            for c in colunas:
                if nome.lower() in c.lower(): return c
            return nome

        cx = encontrar_coluna(col_x, df.columns)
        cy_p = encontrar_coluna(col_y_par, df.columns)
        cy_i = encontrar_coluna(col_y_impar, df.columns)

        if cx in df.columns:
            if cy_p in df.columns:
                df_p = df[[cx, cy_p]].dropna()
                if len(df_p) > 1:
                    r_p = np.corrcoef(df_p[cx].astype(float), df_p[cy_p].astype(float))[0, 1]
                    label_p = f'Par (n={len(df_p)} | r={r_p:.3f})'
                else:
                    label_p = f'Par (n={len(df_p)})'
                fig.add_trace(go.Scatter(x=df_p[cx], y=df_p[cy_p], mode='markers', name=label_p, marker=dict(color='#009b72', size=5)))
            
            if cy_i in df.columns and cy_i != cy_p:
                df_i = df[[cx, cy_i]].dropna()
                if len(df_i) > 1:
                    r_i = np.corrcoef(df_i[cx].astype(float), df_i[cy_i].astype(float))[0, 1]
                    label_i = f'Ímpar (n={len(df_i)} | r={r_i:.3f})'
                else:
                    label_i = f'Ímpar (n={len(df_i)})'
                fig.add_trace(go.Scatter(x=df_i[cx], y=df_i[cy_i], mode='markers', name=label_i, marker=dict(color='#6f42c1', size=5)))
                
        fig.update_layout(title=tit, xaxis_title=lbl_x, yaxis_title=lbl_y, margin=dict(l=10, r=10, t=40, b=10),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        return fig

    # Renderização sequencial dos blocos gráficos idênticos aos prints do Manus
    st.markdown("### 📊 Relações Operacionais (Aba Química)")
    
    # Gráficos adaptáveis que procuram termos como 'as', 'turbidez', 'bruta', 'clarificada' nas suas colunas reais
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "as", "bruta", "bruta", "A/S", "Turbidez Bruta", "A/S × Turbidez da Água Bruta"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "as", "par", "impar", "A/S", "Turbidez Clarificada", "A/S × Turbidez Clarificada"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "sat", "par", "impar", "Pressão Sat. (bar)", "Turbidez Clarificada", "Pressão de Saturação × Clarificada"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_q_f, "recirculacao", "par", "impar", "Vazão de Recirculação (L/s)", "Turbidez Clarificada", "Vazão de Recirculação × Clarificada"), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🧪 Relações Químicas e Dosagem (Aba Carga)")
    st.plotly_chart(plotar_dispersao_lado(df_c_f, "pac", "ph", "ph", "PAC (mg/L)", "pH Coagulado", "PAC × pH de Coagulação"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_c_f, "pac", "clarificada", "clarificada", "PAC (mg/L)", "Turbidez Clarificada", "PAC × Turbidez Clarificada"), use_container_width=True)
    st.plotly_chart(plotar_dispersao_lado(df_c_f, "coagulado", "disponivel", "disponivel", "SST Coagulado (mg/L)", "Ar Disponível", "SST Coagulado × Ar Disponível"), use_container_width=True)
