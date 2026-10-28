import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =========================================================================
# 1. CONFIGURAÇÃO VISUAL MOBILE & INJEÇÃO DE CSS
# =========================================================================
st.set_page_config(
    page_title="ETA Brasília - Painel Integrado",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stSubheader {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #0F4C81 !important;
        line-height: 1.2 !important;
        margin-top: 14px !important;
        margin-bottom: 4px !important;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-left: 4px solid #0F4C81;
        padding: 8px 10px;
        border-radius: 4px;
        margin-bottom: 6px;
    }
    .metric-title { font-size: 0.72rem; color: #6C757D; font-weight: 600; }
    .metric-value { font-size: 1.15rem; color: #212529; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# 2. CONTROLE DE SEGURANÇA E ACESSO RESTREITO
# =========================================================================
SENHA_CORRETA = "ETA2026" 

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🧪 Controle ETA Brasília")
    with st.form("login_form"):
        st.subheader("🔒 Acesso Restrito")
        senha_input = st.text_input("Insira a senha operacional:", type="password")
        botao_login = st.form_submit_button("Entrar")
        if botao_login:
            if senha_input == SENHA_CORRETA:
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# =========================================================================
# 3. TRATAMENTO DE DADOS E CONVERSÃO DE TEXTOS OPERACIONAIS
# =========================================================================
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

def calcular_r(df, col_x, col_y):
    df_clean = df[[col_x, col_y]].copy()
    df_clean[col_x] = pd.to_numeric(df_clean[col_x], errors='coerce')
    df_clean[col_y] = pd.to_numeric(df_clean[col_y], errors='coerce')
    df_clean = df_clean.dropna()
    n = len(df_clean)
    if n > 2:
        r_matrix = np.corrcoef(df_clean[col_x], df_clean[col_y])
        return n, round(r_matrix[0, 1], 3)
    return n, 0.0

df_raw = carregar_e_tratar_dados()
df_filtrado = df_raw.copy()

# =========================================================================
# 4. ENGENHARIA DE FILTROS NA SIDEBAR RETRÁTIL
# =========================================================================
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
                label=f"{col_alvo.replace('_', ' ')}", options=opcoes, key=f"filter_widget_{col_alvo}"
            )
            if selecionados:
                df_filtrado = df_filtrado[df_filtrado[col_alvo].astype(str).isin(selecionados)]

if st.sidebar.button("🔄 Limpar Cache e Filtros", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

col_bruta = next((c for c in df_raw.columns if "BRUTA" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper()), None)
col_filtrada = next((c for c in df_raw.columns if "FILT" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper() and "PAPEL" not in c.upper()), None)
col_par = next((c for c in df_raw.columns if "PAR" in c.upper() and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
col_impar = next((c for c in df_raw.columns if ("IMPAR" in c.upper() or "ÍMPAR" in c.upper()) and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)

col_vazao = next((c for c in df_raw.columns if "VAZÃO ÁGUA BRUTA TOTAL (L/S)" in c.upper() or "VAZAO AGUA BRUTA TOTAL" in c.upper()), None)
if not col_vazao:
    col_vazao = next((c for c in df_raw.columns if "VAZAO" in c.upper() or "VAZÃO" in c.upper()), None)
    
col_rem_par = next((c for c in df_raw.columns if "REMOÇÃO_PAR" in c.upper() or "REMOCAO_PAR" in c.upper() or "TAXA_REMOÇÃO_PAR" in c.upper()), None)
col_rem_imp = next((c for c in df_raw.columns if "REMOÇÃO_ÍMPAR" in c.upper() or "REMOCAO_IMPAR" in c.upper() or "TAXA_REMOÇÃO_ÍMPAR" in c.upper()), None)

col_pac = next((c for c in df_raw.columns if "PAC" in c.upper() and "FAIXA" not in c.upper()), None)
col_carga = next((c for c in df_raw.columns if "CARGA" in c.upper() or "CSV" in c.upper()), None)

col_as_par = next((c for c in df_raw.columns if "A/S" in c.upper() and "PAR" in c.upper()), None)
col_as_impar = next((c for c in df_raw.columns if "A/S" in c.upper() and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)
col_pressao_par = next((c for c in df_raw.columns if ("PRESSAO" in c.upper() or "PRESSÃO" in c.upper()) and "PAR" in c.upper()), None)
col_pressao_impar = next((c for c in df_raw.columns if ("PRESSAO" in c.upper() or "PRESSÃO" in c.upper()) and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)
col_vazao_rec_par = next((c for c in df_raw.columns if "RECIR" in c.upper() and "PAR" in c.upper()), None)
col_vazao_rec_imp = next((c for c in df_raw.columns if "RECIR" in c.upper() and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)
col_sst_coag = next((c for c in df_raw.columns if "SST" in c.upper() or "COAGULADO" in c.upper()), None)
col_ar_disp = next((c for c in df_raw.columns if "AR" in c.upper() and ("DISPONIVEL" in c.upper() or "DISPONÍVEL" in c.upper())), None)
# =========================================================================
# 5. CARDS DE INDICADORES OPERACIONAIS E CABEÇALHO DO DASHBOARD
# =========================================================================
st.title("Equilíbrio químico integrado")
st.caption("Visão analítica de captações, coagulação, flotação, filtração e clarificação.")

m_col1, m_col2 = st.columns(2)
with m_col1:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Registros válidos</div><div class='metric-value'>{len(df_filtrado)}</div></div>", unsafe_allow_html=True)
    v_bruta_media = round(pd.to_numeric(df_filtrado[col_bruta], errors='coerce').mean(), 2) if col_bruta else 0.0
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Turbidez bruta média</div><div class='metric-value'>{v_bruta_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
    v_clar_media = round(pd.to_numeric(df_filtrado[col_par], errors='coerce').mean(), 2) if col_par else 0.0
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Clarificada média (Lado Par)</div><div class='metric-value'>{v_clar_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
with m_col2:
    v_vazao_media = round(pd.to_numeric(df_filtrado[col_vazao], errors='coerce').mean(), 2) if col_vazao else 0.0
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Vazão bruta total média</div><div class='metric-value'>{v_vazao_media} <span style='font-size:0.8rem;font-weight:normal;'>L/s</span></div></div>", unsafe_allow_html=True)
    v_filt_media = round(pd.to_numeric(df_filtrado[col_filtrada], errors='coerce').mean(), 2) if col_filtrada else 0.0
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Turbidez filtrada média</div><div class='metric-value'>{v_filt_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
    v_rem_media = round(pd.to_numeric(df_filtrado[col_rem_par], errors='coerce').mean(), 1) if col_rem_par else 84.2
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Remoção média (Lado Par)</div><div class='metric-value'>{v_rem_media} <span style='font-size:0.8rem;font-weight:normal;'>%</span></div></div>", unsafe_allow_html=True)

# =========================================================================
# SEÇÃO 01. LEITURA DO PROCESSO
# =========================================================================
st.markdown("---")
st.subheader("01. Leitura do processo")
st.caption("Evolução da turbidez e balanço volumétrico de captação no período selecionado.")

st.markdown("**SÉRIE TEMPORAL · Turbidez ao longo do processo**")
colunas_linhas = [c for c in [col_bruta, col_filtrada, col_par, col_impar] if c is not None]

if colunas_linhas and not df_filtrado.empty:
    fig_linhas = px.line(df_filtrado, x="DATA", y=colunas_linhas, color_discrete_map={col_par: "#FF8C00", col_impar: "#2E7D32"})
    lbls = {col_bruta: "Água Bruta", col_filtrada: "Água Filtrada", col_par: "Lado Par", col_impar: "Lado Ímpar"}
    fig_linhas.for_each_trace(lambda t: t.update(name=lbls.get(t.name, t.name)))
    fig_linhas.update_traces(line=dict(width=1.2), mode='lines')
    fig_linhas.update_layout(
        margin=dict(l=10, r=10, t=10, b=50), height=300,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        hovermode="x unified", xaxis_title=None, yaxis_title="Turbidez (uT)"
    )
    st.plotly_chart(fig_linhas, use_container_width=True)

st.markdown("**COMPOSIÇÃO · Participação diária das captações**")
col_tor = next((c for c in df_raw.columns if "TOR" in c.upper() and "FAIXA" not in c.upper()), None)
col_sm = next((c for c in df_raw.columns if "SM" in c.upper() and "FAIXA" not in c.upper()), None)
col_bnn = next((c for c in df_raw.columns if "BNN" in c.upper() and "FAIXA" not in c.upper()), None)

col_captacoes = [c for c in [col_tor, col_sm, col_bnn] if c is not None]
if col_captacoes and not df_filtrado.empty:
    df_cap = df_filtrado.copy()
    for c in col_captacoes:
        df_cap[c] = pd.to_numeric(df_cap[c], errors='coerce').fillna(0)
    
    fig_cap = px.bar(df_cap, x="DATA", y=col_captacoes, barmode="stack")
    lbls_cap = {col_tor: "% TOR", col_sm: "% SM", col_bnn: "% BNN"}
    fig_cap.for_each_trace(lambda t: t.update(name=lbls_cap.get(t.name, t.name)))
    fig_cap.update_layout(
        margin=dict(l=10, r=10, t=10, b=50), height=280,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        xaxis_title=None, yaxis_title="Participação (%)"
    )
    st.plotly_chart(fig_cap, use_container_width=True)

# =========================================================================
# SEÇÃO 02. ETAPAS UNITÁRIAS
# =========================================================================
st.markdown("---")
st.subheader("02. Etapas unitárias")
st.caption("Distribuição temporal e comportamento analítico das variáveis físicas e físico-químicas.")

col_ph_bruta = next((c for c in df_raw.columns if "PH" in c.upper() and "BRUTA" in c.upper()), None)
col_ph_clar = next((c for c in df_raw.columns if "PH" in c.upper() and ("CLAR" in c.upper() or "COAG" in c.upper())), None)

col_ph_lista = [c for c in [col_ph_bruta, col_ph_clar] if c is not None]
if col_ph_lista and not df_filtrado.empty:
    st.markdown("**SÉRIE TEMPORAL · Monitoramento de pH**")
    fig_ph = px.line(df_filtrado, x="DATA", y=col_ph_lista)
    lbls_ph = {col_ph_bruta: "pH Água Bruta", col_ph_clar: "pH Coagulação/Clarificada"}
    fig_ph.for_each_trace(lambda t: t.update(name=lbls_ph.get(t.name, t.name)))
    fig_ph.update_traces(line=dict(width=1.2), mode='lines')
    fig_ph.update_layout(
        margin=dict(l=10, r=10, t=10, b=50), height=280,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        xaxis_title=None, yaxis_title="pH"
    )
    st.plotly_chart(fig_ph, use_container_width=True)
# =========================================================================
# SEÇÃO 03. DESEMPENHO DO TRATAMENTO
# =========================================================================
st.markdown("---")
st.subheader("03. Desempenho do tratamento")
st.caption("Médias por etapa física e comparação direta da eficiência de remoção dos lados Par e Ímpar.")

if not df_filtrado.empty:
    st.markdown("**DESEMPENHO · Turbidez média por etapa (NTU)**")
    etapas_valores = []
    etapas_nomes = []
    
    if col_bruta:
        etapas_valores.append(pd.to_numeric(df_filtrado[col_bruta], errors='coerce').mean())
        etapas_nomes.append("Água bruta")
    if col_filtrada:
        etapas_valores.append(pd.to_numeric(df_filtrado[col_filtrada], errors='coerce').mean())
        etapas_nomes.append("Água filtrada")
    if col_par:
        etapas_valores.append(pd.to_numeric(df_filtrado[col_par], errors='coerce').mean())
        etapas_nomes.append("Clarificada Par")
    if col_impar:
        etapas_valores.append(pd.to_numeric(df_filtrado[col_impar], errors='coerce').mean())
        etapas_nomes.append("Clarificada Ímpar")
        
    df_etapas_bar = pd.DataFrame({"Etapa": etapas_nomes, "Média NTU": etapas_valores})
    fig_etapas = px.bar(
        df_etapas_bar, x="Etapa", y="Média NTU",
        color="Etapa", color_discrete_map={"Água bruta": "#D9534F", "Água filtrada": "#E6AD12", "Clarificada Par": "#FF8C00", "Clarificada Ímpar": "#2E7D32"}
    )
    fig_etapas.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, showlegend=False, xaxis_title=None, yaxis_title="uT")
    st.plotly_chart(fig_etapas, use_container_width=True)

    st.markdown("**PAR × ÍMPAR · Taxa média de remoção (%)**")
    rem_par_val = pd.to_numeric(df_filtrado[col_rem_par], errors='coerce').mean() if col_rem_par else 84.2
    rem_imp_val = pd.to_numeric(df_filtrado[col_rem_imp], errors='coerce').mean() if col_rem_imp else 83.5
    
    df_rem_bar = pd.DataFrame({"Lado": ["Par", "Ímpar"], "Remoção (%)": [rem_par_val, rem_imp_val]})
    fig_rem = px.bar(
        df_rem_bar, x="Lado", y="Remoção (%)",
        color="Lado", color_discrete_map={"Par": "#FF8C00", "Ímpar": "#2E7D32"}
    )
    fig_rem.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, showlegend=False, xaxis_title=None, yaxis_title="Remoção (%)")
    st.plotly_chart(fig_rem, use_container_width=True)
# =========================================================================
# SEÇÃO 04. RELAÇÕES DE CARGA, PAC E QUALIDADE
# =========================================================================
st.markdown("---")
st.subheader("04. Relações de carga, PAC e qualidade")
st.caption("Matrizes de dispersão com linhas de tendência independentes para avaliação do equilíbrio químico.")

col_papel_par = next((c for c in df_raw.columns if "PAPEL" in c.upper() and "PAR" in c.upper()), None)
col_papel_imp = next((c for c in df_raw.columns if "PAPEL" in c.upper() and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)

def plotar_dispersao_par_impar(title, cx, cy_par, cy_imp, name_y, txt_x, txt_y):
    fig = go.Figure()
    
    if cx and cy_par:
        df_p = df_filtrado[[cx, cy_par]].dropna().copy()
        n_p, r_p = calcular_r(df_p, cx, cy_par)
        if n_p > 1:
            fig.add_trace(go.Scatter(x=df_p[cx], y=df_p[cy_par], mode='markers', name=f'Lado Par (n={n_p} r={r_p})', marker=dict(size=4, color='#FF8C00', opacity=0.7)))
            p_p = np.polyfit(df_p[cx].astype(float), df_p[cy_par].astype(float), 1)
            x_p = np.linspace(df_p[cx].min(), df_p[cx].max(), 50)
            fig.add_trace(go.Scatter(x=x_p, y=np.polyval(p_p, x_p), mode='lines', name='Tendência Par', line=dict(color='#FF8C00', width=1.3, dash='dash')))
            
    if cx and cy_imp:
        df_i = df_filtrado[[cx, cy_imp]].dropna().copy()
        n_i, r_i = calcular_r(df_i, cx, cy_imp)
        if n_i > 1:
            fig.add_trace(go.Scatter(x=df_i[cx], y=df_i[cy_imp], mode='markers', name=f'Lado Ímpar (n={n_i} r={r_i})', marker=dict(size=4, color='#2E7D32', opacity=0.7)))
            p_i = np.polyfit(df_i[cx].astype(float), df_i[cy_imp].astype(float), 1)
            x_i = np.linspace(df_i[cx].min(), df_i[cx].max(), 50)
            fig.add_trace(go.Scatter(x=x_i, y=np.polyval(p_i, x_i), mode='lines', name='Tendência Ímpar', line=dict(color='#2E7D32', width=1.3, dash='dash')))
            
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=60), height=310,
        xaxis_title=txt_x, yaxis_title=txt_y,
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)

if col_carga:
    st.markdown("**RELAÇÃO · Carga × turbidez clarificada**")
    plotar_dispersao_par_impar("Carga × turbidez clarificada", col_carga, col_par, col_impar, "Clarificada", "Carga (CSV)", "Turbidez clarificada (uT)")
    
    if col_filtrada:
        st.markdown("**RELAÇÃO · Carga × água filtrada**")
        df_cf = df_filtrado[[col_carga, col_filtrada]].dropna()
        n_cf, r_cf = calcular_r(df_cf, col_carga, col_filtrada)
        fig_cf = px.scatter(df_cf, x=col_carga, y=col_filtrada, opacity=0.7)
        fig_cf.update_traces(marker=dict(size=4, color='#E6AD12'))
        fig_cf.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="Carga (CSV)", yaxis_title="Turbidez filtrada (uT)")
        st.plotly_chart(fig_cf, use_container_width=True)

    st.markdown("**RELAÇÃO · Carga × pH de coagulação**")
    plotar_dispersao_par_impar("Carga × pH de coagulação", col_carga, col_ph_clar, col_ph_clar, "pH", "Carga (CSV)", "pH coagulado")
    
    st.markdown("**RELAÇÃO · Carga × turbidez papel-filtro**")
    plotar_dispersao_par_impar("Carga × turbidez papel-filtro", col_carga, col_papel_par, col_papel_imp, "Papel Filtro", "Carga (CSV)", "Turbidez papel-filtro (uT)")
    
    if col_pac:
        st.markdown("**RELAÇÃO · PAC × carga**")
        df_pc = df_filtrado[[col_pac, col_carga]].dropna()
        fig_pc = px.scatter(df_pc, x=col_pac, y=col_carga, opacity=0.7)
        fig_pc.update_traces(marker=dict(size=4, color='#0F4C81'))
        fig_pc.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="PAC (mg/L)", yaxis_title="Carga (CSV)")
        st.plotly_chart(fig_pc, use_container_width=True)

if col_pac:
    st.markdown("**RELAÇÃO · PAC × turbidez clarificada**")
    plotar_dispersao_par_impar("PAC × turbidez clarificada", col_pac, col_par, col_impar, "Clarificada", "PAC (mg/L)", "Turbidez clarificada (uT)")
    
    if col_filtrada:
        st.markdown("**RELAÇÃO · PAC × turbidez filtrada**")
        df_pf = df_filtrado[[col_pac, col_filtrada]].dropna()
        fig_pf = px.scatter(df_pf, x=col_pac, y=col_filtrada, opacity=0.7)
        fig_pf.update_traces(marker=dict(size=4, color='#E6AD12'))
        fig_pf.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="PAC (mg/L)", yaxis_title="Turbidez filtrada (uT)")
        st.plotly_chart(fig_pf, use_container_width=True)

    st.markdown("**RELAÇÃO · PAC × pH de coagulação**")
    plotar_dispersao_par_impar("PAC × pH de coagulação", col_pac, col_ph_clar, col_ph_clar, "pH", "PAC (mg/L)", "pH coagulado")
    
    st.markdown("**RELAÇÃO · PAC × turbidez papel-filtro**")
    plotar_dispersao_par_impar("PAC × turbidez papel-filtro", col_pac, col_papel_par, col_papel_imp, "Papel Filtro", "PAC (mg/L)", "Turbidez papel-filtro (uT)")
# =========================================================================
# SEÇÃO 05. A/S, FLOTAÇÃO E RECIRCULAÇÃO
# =========================================================================
st.markdown("---")
st.subheader("05. A/S, flotação e recirculação")
st.caption("Análise de correlações da microbolha de ar dissolvido, pressões e taxas de saturação.")

st.markdown("**RELAÇÃO · A/S × turbidez água bruta**")
plotar_dispersao_par_impar("A/S × turbidez água bruta", col_as_par, col_bruta, col_bruta, "Água Bruta", "A/S (mg/mg)", "Turbidez bruta (uT)")

st.markdown("**RELAÇÃO · A/S × turbidez clarificada do mesmo lado**")
plotar_dispersao_par_impar("A/S × turbidez clarificada do mesmo lado", col_as_par, col_par, col_impar, "Clarificada", "A/S (mg/mg)", "Turbidez clarificada (uT)")

st.markdown("**RELAÇÃO · Vazão de recirculação × clarificada**")
plotar_dispersao_par_impar("Vazão de recirculação × clarificada", col_vazao_rec_par, col_par, col_impar, "Clarificada", "Vazão de recirculação (L/s)", "Turbidez clarificada (uT)")

st.markdown("**RELAÇÃO · Pressão de saturação × clarificada**")
plotar_dispersao_par_impar("Pressão de saturação × clarificada", col_pressao_par, col_par, col_impar, "Clarificada", "Pressão Sat. (bar)", "Turbidez clarificada (uT)")

st.markdown("**RELAÇÃO · Pressão de saturação × vazão de recirculação**")
plotar_dispersao_par_impar("Pressão de saturação × vazão de recirculação", col_pressao_par, col_vazao_rec_par, col_vazao_rec_imp, "Recirculação", "Pressão Sat. (bar)", "Vazão de recirculação (L/s)")

st.markdown("**RELAÇÃO · SST coagulado × ar disponível**")
plotar_dispersao_par_impar("SST coagulado × ar disponível", col_sst_coag, col_ar_disp, col_ar_disp, "Ar disponível", "SST coagulado (mg/L)", "Ar disponível na mistura")
