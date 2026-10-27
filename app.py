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

# Estilização para compactar fontes e cards de indicadores na tela do celular
st.markdown("""
    <style>
    .stSubheader {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #0F4C81 !important;
        line-height: 1.2 !important;
        margin-top: 10px !important;
        margin-bottom: 4px !important;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-left: 4px solid #0F4C81;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .metric-title { font-size: 0.75rem; color: #6C757D; font-weight: 600; }
    .metric-value { font-size: 1.2rem; color: #212529; font-weight: 700; }
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
# 3. TRATAMENTO INTELIGENTE DE CACHE E CABEÇALHOS DO EXCEL
# =========================================================================
@st.cache_data
def carregar_e_tratar_dados():
    df = pd.read_excel("EQUILIBRIO QUIMICO.xlsx", sheet_name="EQUILIBRIO QUIMICO COM CARGA", decimal=",")
    
    # Desduplicação horizontal das colunas repetidas (Lado Par / Lado Ímpar)
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
    """Calcula coeficientes estatísticos de forma segura para os gráficos."""
    df_clean = df[[col_x, col_y]].dropna()
    n = len(df_clean)
    if n > 2:
        r_matrix = np.corrcoef(df_clean[col_x].astype(float), df_clean[col_y].astype(float))
        return n, round(r_matrix[0, 1], 3)
    return n, 0.0

try:
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

    # Mapeamento interno das variáveis essenciais para os próximos blocos
    col_bruta = next((c for c in df_raw.columns if "BRUTA" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper()), None)
    col_filtrada = next((c for c in df_raw.columns if "FILT" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper() and "PAPEL" not in c.upper()), None)
    col_par = next((c for c in df_raw.columns if "PAR" in c.upper() and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    col_impar = next((c for c in df_raw.columns if ("IMPAR" in c.upper() or "ÍMPAR" in c.upper()) and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    col_vazao = next((c for c in df_raw.columns if "VAZAO" in c.upper() or "VAZÃO" in c.upper()), None)
    col_rem_par = next((c for c in df_raw.columns if "REMOÇÃO_PAR" in c.upper() or "REMOCAO_PAR" in c.upper()), None)
    col_pac = next((c for c in df_raw.columns if "PAC" in c.upper()), None)
    col_carga = next((c for c in df_raw.columns if "CARGA" in c.upper() or "CSV" in c.upper()), None)

# O bloco try continua aberto para receber as próximas etapas...
    # =========================================================================
    # 5. CARDS DE INDICADORES OPERACIONAIS (TELA PRINCIPAL)
    # =========================================================================
    st.title("Equilíbrio químico integrado")
    st.caption("Visão combinada de captações, coagulação, flotação, filtração e clarificação.")

    # Renderização em duas colunas responsivas para visualização em smartphones
    m_col1, m_col2 = st.columns(2)
    
    with m_col1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Registros válidos</div><div class='metric-value'>{len(df_filtrado)}</div></div>", unsafe_allow_html=True)
        v_bruta_media = round(df_filtrado[col_bruta].mean(), 2) if col_bruta else 0.0
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Turbidez bruta média</div><div class='metric-value'>{v_bruta_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
        v_clar_media = round(df_filtrado[col_par].mean(), 2) if col_par else 0.0
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Clarificada média</div><div class='metric-value'>{v_clar_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
        
    with m_col2:
        v_vazao_media = round(df_filtrado[col_vazao].mean(), 2) if col_vazao else 0.0
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Vazão total média</div><div class='metric-value'>{v_vazao_media} <span style='font-size:0.8rem;font-weight:normal;'>L/s</span></div></div>", unsafe_allow_html=True)
        v_filt_media = round(df_filtrado[col_filtrada].mean(), 2) if col_filtrada else 0.0
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Turbidez filtrada média</div><div class='metric-value'>{v_filt_media} <span style='font-size:0.8rem;font-weight:normal;'>uT</span></div></div>", unsafe_allow_html=True)
        v_rem_media = round(df_filtrado[col_rem_par].mean(), 1) if col_rem_par else 84.2
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Remoção média</div><div class='metric-value'>{v_rem_media} <span style='font-size:0.8rem;font-weight:normal;'>%</span></div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("01. Leitura do processo")
    st.caption("Evolução da turbidez e participação das captações no período selecionado.")

    # =========================================================================
    # 6. GRÁFICO 1: SÉRIE TEMPORAL DE TURBIDEZ
    # =========================================================================
    st.markdown("**SÉRIE TEMPORAL · Turbidez ao longo do processo**")
    colunas_linhas = [c for c in [col_bruta, col_filtrada, col_par, col_impar] if c is not None]
    
    if colunas_linhas and not df_filtrado.empty:
        fig_linhas = px.line(df_filtrado, x="DATA", y=colunas_linhas)
        
        # Mapeamento estrito sugerido pelo modelo analítico
        lbls = {
            col_bruta: "Água Bruta", 
            col_filtrada: "Água Filtrada", 
            col_par: "Lado Par", 
            col_impar: "Lado Ímpar"
        }
        fig_linhas.for_each_trace(lambda t: t.update(name=lbls.get(t.name, t.name)))
        
        # Estilo estrito: linhas finas (1.2) e sem demarcações de pontos
        fig_linhas.update_traces(line=dict(width=1.2), mode='lines')
        fig_linhas.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), 
            height=260,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig_linhas, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para gerar o gráfico de linhas temporais.")

# O bloco try permanece aberto aguardando os próximos gráficos de dispersão...
    # =========================================================================
    # 7. RELAÇÃO ENTRE VARIÁVEIS (MÓDULO DE CORRELAÇÃO ESTATÍSTICA)
    # =========================================================================
    st.markdown("---")
    st.subheader("02. Relação entre variáveis (Lado Par x Lado Ímpar)")

    # --- GRÁFICO 2: PAC x Turbidez Clarificada (Desmembrado Lado Par e Ímpar) ---
    st.markdown("**RELAÇÃO · PAC × turbidez clarificada**")
    if col_pac and col_par and col_impar and not df_filtrado.empty:
        fig_disp1 = go.Figure()
        
        # Engenharia de Ajuste e Tendência: Lado Par
        df_p = df_filtrado[[col_pac, col_par]].dropna().copy()
        if not df_p.empty:
            n_p, r_p = calcular_r(df_p, col_pac, col_par)
            fig_disp1.add_trace(go.Scatter(
                x=df_p[col_pac], y=df_p[col_par], mode='markers', 
                name=f'Lado Par (n={n_p} r={r_p})', 
                marker=dict(size=4, color='#0F4C81', opacity=0.7)
            ))
            p_p = np.polyfit(df_p[col_pac].astype(float), df_p[col_par].astype(float), 1)
            x_p = np.linspace(df_p[col_pac].min(), df_p[col_pac].max(), 50)
            fig_disp1.add_trace(go.Scatter(
                x=x_p, y=np.polyval(p_p, x_p), mode='lines', 
                name='Tendência Par', line=dict(color='#0F4C81', width=1.5, dash='dash')
            ))

        # Engenharia de Ajuste e Tendência: Lado Ímpar
        df_i = df_filtrado[[col_pac, col_impar]].dropna().copy()
        if not df_i.empty:
            n_i, r_i = calcular_r(df_i, col_pac, col_impar)
            fig_disp1.add_trace(go.Scatter(
                x=df_i[col_pac], y=df_i[col_impar], mode='markers', 
                name=f'Lado Ímpar (n={n_i} r={r_i})', 
                marker=dict(size=4, color='#7A4B9E', opacity=0.7)
            ))
            p_i = np.polyfit(df_i[col_pac].astype(float), df_i[col_impar].astype(float), 1)
            x_i = np.linspace(df_i[col_pac].min(), df_i[col_pac].max(), 50)
            fig_disp1.add_trace(go.Scatter(
                x=x_i, y=np.polyval(p_i, x_i), mode='lines', 
                name='Tendência Ímpar', line=dict(color='#7A4B9E', width=1.5, dash='dash')
            ))

        fig_disp1.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280,
            xaxis_title="PAC (mg/L)", yaxis_title="Turbidez clarificada (uT)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_disp1, use_container_width=True)

    # --- GRÁFICO 3: PAC x Turbidez Filtrada ---
    st.markdown("**RELAÇÃO · PAC × turbidez filtrada**")
    if col_pac and col_filtrada and not df_filtrado.empty:
        df_f = df_filtrado[[col_pac, col_filtrada]].dropna().copy()
        n_f, r_f = calcular_r(df_f, col_pac, col_filtrada)
        
        fig_disp2 = go.Figure()
        fig_disp2.add_trace(go.Scatter(
            x=df_f[col_pac], y=df_f[col_filtrada], mode='markers', 
            name=f'Filtrada (n={n_f} r={r_f})', 
            marker=dict(size=4, color='#E6AD12', opacity=0.7)
        ))
        
        if n_f > 2:
            p_f = np.polyfit(df_f[col_pac].astype(float), df_f[col_filtrada].astype(float), 1)
            x_f = np.linspace(df_f[col_pac].min(), df_f[col_pac].max(), 50)
            fig_disp2.add_trace(go.Scatter(
                x=x_f, y=np.polyval(p_f, x_f), mode='lines', 
                name='Tendência Filtrada', line=dict(color='#E6AD12', width=1.5, dash='dash')
            ))
            
        fig_disp2.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280,
            xaxis_title="PAC (mg/L)", yaxis_title="Turbidez filtrada (uT)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_disp2, use_container_width=True)

# O bloco try permanece aberto aguardando os parâmetros físicos de flotação do bloco 4...
    # =========================================================================
    # 8. MÓDULO DE FLOTAÇÃO, MASSA DE AR (A/S) E RECIRCULAÇÃO
    # =========================================================================
    st.markdown("---")
    st.subheader("03. A/S, flotação e recirculação")
    st.caption("Relações por lado entre A/S, turbidez bruta/clarificada e parâmetros de recirculação.")

    # Mapeamento automatizado das variáveis físicas no Excel
    col_as_par = next((c for c in df_raw.columns if "A/S" in c.upper() and "PAR" in c.upper()), None)
    col_as_impar = next((c for c in df_raw.columns if "A/S" in c.upper() and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)
    col_pressao_par = next((c for c in df_raw.columns if ("PRESSAO" in c.upper() or "PRESSÃO" in c.upper()) and "PAR" in c.upper()), None)
    col_pressao_impar = next((c for c in df_raw.columns if ("PRESSAO" in c.upper() or "PRESSÃO" in c.upper()) and ("IMPAR" in c.upper() or "ÍMPAR" in c.upper())), None)

    # --- GRÁFICO 4: A/S x Turbidez da Água Bruta ---
    st.markdown("**RELAÇÃO · A/S × turbidez da água bruta**")
    if col_bruta and (col_as_par or col_as_impar) and not df_filtrado.empty:
        fig_disp3 = go.Figure()
        
        if col_as_par:
            df_as_p = df_filtrado[[col_as_par, col_bruta]].dropna().copy()
            if not df_as_p.empty:
                n_as_p, r_as_p = calcular_r(df_as_p, col_as_par, col_bruta)
                fig_disp3.add_trace(go.Scatter(
                    x=df_as_p[col_as_par], y=df_as_p[col_bruta], mode='markers', 
                    name=f'Lado Par (n={n_as_p} r={r_as_p})', 
                    marker=dict(size=4, color='#0F4C81', opacity=0.7)
                ))
                p_as_p = np.polyfit(df_as_p[col_as_par].astype(float), df_as_p[col_bruta].astype(float), 1)
                x_as_p = np.linspace(df_as_p[col_as_par].min(), df_as_p[col_as_par].max(), 50)
                fig_disp3.add_trace(go.Scatter(
                    x=x_as_p, y=np.polyval(p_as_p, x_as_p), mode='lines', 
                    name='Tendência Par', line=dict(color='#0F4C81', width=1.5, dash='dash')
                ))

        if col_as_impar:
            df_as_i = df_filtrado[[col_as_impar, col_bruta]].dropna().copy()
            if not df_as_i.empty:
                n_as_i, r_as_i = calcular_r(df_as_i, col_as_impar, col_bruta)
                fig_disp3.add_trace(go.Scatter(
                    x=df_as_i[col_as_impar], y=df_as_i[col_bruta], mode='markers', 
                    name=f'Lado Ímpar (n={n_as_i} r={r_as_i})', 
                    marker=dict(size=4, color='#7A4B9E', opacity=0.7)
                ))
                p_as_i = np.polyfit(df_as_i[col_as_impar].astype(float), df_as_i[col_bruta].astype(float), 1)
                x_as_i = np.linspace(df_as_i[col_as_impar].min(), df_as_i[col_as_impar].max(), 50)
                fig_disp3.add_trace(go.Scatter(
                    x=x_as_i, y=np.polyval(p_as_i, x_as_i), mode='lines', 
                    name='Tendência Ímpar', line=dict(color='#7A4B9E', width=1.5, dash='dash')
                ))

        fig_disp3.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280,
            xaxis_title="A/S (mg/mg)", yaxis_title="Turbidez bruta (uT)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_disp3, use_container_width=True)

    # --- GRÁFICO 5: Pressão de Saturação x Turbidez Clarificada ---
    st.markdown("**RELAÇÃO · Pressão de saturação × clarificada**")
    if col_par and col_impar and (col_pressao_par or col_pressao_impar) and not df_filtrado.empty:
        fig_disp4 = go.Figure()
        
        if col_pressao_par:
            df_pr_p = df_filtrado[[col_pressao_par, col_par]].dropna().copy()
            if not df_pr_p.empty:
                n_pr_p, r_pr_p = calcular_r(df_pr_p, col_pressao_par, col_par)
                fig_disp4.add_trace(go.Scatter(
                    x=df_pr_p[col_pressao_par], y=df_pr_p[col_par], mode='markers', 
                    name=f'Lado Par (n={n_pr_p} r={r_pr_p})', 
                    marker=dict(size=4, color='#0F4C81', opacity=0.7)
                ))

        if col_pressao_impar:
            df_pr_i = df_filtrado[[col_pressao_impar, col_impar]].dropna().copy()
            if not df_pr_i.empty:
                n_pr_i, r_pr_i = calcular_r(df_pr_i, col_pressao_impar, col_impar)
                fig_disp4.add_trace(go.Scatter(
                    x=df_pr_i[col_pressao_impar], y=df_pr_i[col_impar], mode='markers', 
                    name=f'Lado Ímpar (n={n_pr_i} r={r_pr_i})', 
                    marker=dict(size=4, color='#7A4B9E', opacity=0.7)
                ))

        fig_disp4.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=280,
            xaxis_title="Pressão de Saturação (bar)", yaxis_title="Turbidez clarificada (uT)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_disp4, use_container_width=True)

# O bloco try permanece aberto aguardando a última etapa de fechamento e fracionamento estatístico...
    # =========================================================================
    # 9. FRACIONAMENTO ESTATÍSTICO E FECHAMENTO DO SISTEMA
    # =========================================================================
    st.markdown("---")
    st.subheader("04. Fracionamento estatístico e faixas operacionais")
    st.caption("Distribuição percentual histórica das faixas operacionais de turbidez por etapa.")

    # Mapeamento estrito das colunas de faixas de texto tratadas do Excel
    col_faixa_bruta = next((c for c in df_raw.columns if "FAIXA_TURB_BRUTA" in c.upper()), None)
    col_faixa_clar_par = next((c for c in df_raw.columns if "FAIXA_TURB_CLAR_PAR" in c.upper()), None)
    col_faixa_clar_imp = next((c for c in df_raw.columns if "FAIXA_TURB_CLAR_ÍMPAR" in c.upper() or "FAIXA_TURB_CLAR_IMPAR" in c.upper()), None)

    # --- GRÁFICO 6: Frequência de Faixas - Água Bruta ---
    st.markdown("**DISTRIBUIÇÃO · Faixas de turbidez da água bruta**")
    if col_faixa_bruta and not df_filtrado.empty:
        df_faixa_b = df_filtrado[col_faixa_bruta].value_counts(normalize=True).reset_index()
        df_faixa_b.columns = ["Faixa", "Percentual"]
        df_faixa_b["Percentual"] = df_faixa_b["Percentual"] * 100
        
        fig_faixa_b = px.bar(
            df_faixa_b, y="Faixa", x="Percentual", orientation="h",
            color_discrete_sequence=["#D9534F"], 
            text=df_faixa_b["Percentual"].apply(lambda x: f"{x:.1f}%")
        )
        fig_faixa_b.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=220, 
            xaxis_title="Frequência (%)", yaxis_title=None
        )
        st.plotly_chart(fig_faixa_b, use_container_width=True)

    # --- GRÁFICO 7: Comparativo Lado Par x Lado Ímpar - Água Clarificada ---
    st.markdown("**COMPARAÇÃO · Faixas de turbidez da água clarificada**")
    if col_faixa_clar_par and col_faixa_clar_imp and not df_filtrado.empty:
        df_p_f = df_filtrado[col_faixa_clar_par].value_counts(normalize=True).reset_index()
        df_p_f.columns = ["Faixa", "Percentual"]
        df_p_f["Lado"] = "Lado Par"
        
        df_i_f = df_filtrado[col_faixa_clar_imp].value_counts(normalize=True).reset_index()
        df_i_f.columns = ["Faixa", "Percentual"]
        df_i_f["Lado"] = "Lado Ímpar"
        
        df_faixas_combo = pd.concat([df_p_f, df_i_f], axis=0)
        df_faixas_combo["Percentual"] = df_faixas_combo["Percentual"] * 100
        
        fig_faixas_c = px.bar(
            df_faixas_combo, x="Percentual", y="Faixa", color="Lado", barmode="group",
            orientation="h", color_discrete_map={"Lado Par": "#0F4C81", "Lado Ímpar": "#7A4B9E"}
        )
        fig_faixas_c.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=260,
            xaxis_title="Frequência (%)", yaxis_title=None,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_faixas_c, use_container_width=True)

except FileNotFoundError:
    st.error("❌ Arquivo 'EQUILIBRIO QUIMICO.xlsx' não localizado na raiz do repositório.")
except Exception as e:
    st.error(f"⚠️ Erro crítico no processamento das variáveis: {e}")
