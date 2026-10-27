)import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração de Página Otimizada para Celular
st.set_page_config(
    page_title="ETA Brasília - Controle Químico",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Sistema de Proteção por Senha
SENHA_CORRETA = "ETA2026" 

st.title("🧪 Controle ETA Brasília")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
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
    
    # Tratamento de Colunas Duplicadas (Turnos)
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

    # Tratamento de Data
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors='coerce').dt.date
        df = df.dropna(subset=["DATA"]).sort_values("DATA")
    return df

try:
    df_raw = carregar_e_tratar_dados()
    df_filtrado = df_raw.copy()

    # 4. Painel de Filtros Operacionais Concentrados
    st.subheader("🎛️ Filtros de Operação")
    
    # Lista de colunas solicitadas para virarem filtros de seleção
    colunas_filtros = [
        "%TOR", "%SM", "%BNN", "TAXA_RECIR. _PAR", "TAXA_RECIR. _ÍMPAR", 
        "TAXA_REMOÇÃO_ÍMPAR", "TAXA_REMOÇÃO_PAR", "FAIXA_ALC_BRUTA", 
        "FAIXA_COR_BRUTA", "FAIXA_TURB_BRUTA", "TIPO_AGUA_BRUTA", 
        "FAIXA_TURB_PAPEL_FILTRO_PAR", "FAIXA_TURB_PAPEL_FILTRO_ÍMPAR", 
        "FAIXA_TURB_CLAR_PAR", "FAIXA_TURB_CLAR_ÍMPAR", "FAIXA_TURB_FILT."
    ]

    # Renderização dinâmica dos filtros organizados em duas colunas no celular
    f_col1, f_col2 = st.columns(2)
    
    for idx, col_nome in enumerate(colunas_filtros):
        # Localiza a coluna exata (considerando possíveis sufixos de turno)
        col_alvo = next((c for c in df_raw.columns if c.startswith(col_nome)), None)
        
        if col_alvo:
            opcoes = sorted(list(df_raw[col_alvo].dropna().unique()))
            # Distribui os filtros entre as colunas 1 e 2
            with f_col1 if idx % 2 == 0 else f_col2:
                selecionados = st.multiselect(f"{col_nome}", options=opcoes, placeholder="Todos")
                if selecionados:
                    df_filtrado = df_filtrado[df_filtrado[col_alvo].isin(selecionados)]

    # Botão de controle de dados
    if st.button("🔄 Aplicar e Atualizar Dados", use_container_width=True):
        st.toast("Filtros aplicados com sucesso!")

    st.markdown("---")

    # 5. Área Exclusiva dos Gráficos (Sem filtros ou dropdowns internos)
    st.subheader("📊 Gráficos de Avaliação Química")

    # Mapeamento estrito dos parâmetros dos gráficos
    col_bruta = next((c for c in df_raw.columns if "BRUTA" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper()), None)
    col_filtrada = next((c for c in df_raw.columns if "FILT" in c.upper() and "TURB" in c.upper() and "FAIXA" not in c.upper() and "PAPEL" not in c.upper()), None)
    col_par = next((c for c in df_raw.columns if "PAR" in c.upper() and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    col_impar = next((c for c in df_raw.columns if ("IMPAR" in c.upper() or "ÍMPAR" in c.upper()) and "CLAR" in c.upper() and "FAIXA" not in c.upper()), None)
    
    col_pac = next((c for c in df_raw.columns if "PAC" in c.upper()), None)
    col_carga = next((c for c in df_raw.columns if "CARGA" in c.upper() or "CSV" in c.upper()), None)

    # --- GRÁFICO 1: Histórico de Turbidezes vs Período ---
    st.markdown("**Histórico e Tendência de Turbidezes**")
    colunas_linhas = [c for c in [col_bruta, col_filtrada, col_par, col_impar] if c is not None]
    
    if colunas_linhas:
        fig_linhas = px.line(
            df_filtrado, 
            x="DATA", 
            y=colunas_linhas,
            labels={"value": "Turbidez (uT)", "DATA": "Período"}
        )
        # Linhas finas, sem pontos/marcadores
        fig_linhas.update_traces(line=dict(width=1.2), mode='lines')
        fig_linhas.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified"
        )
        st.plotly_chart(fig_linhas, use_container_width=True)
    else:
        st.caption("⚠️ Aguardando dados ou mapeamento de colunas de Turbidez de linha.")

    st.markdown("---")

    # --- GRÁFICO 2: Dispersão PAC vs Carga ---
    st.markdown("**Correlação: Dosagem de PAC vs Carga (CSV)**")
    
    if col_pac and col_carga:
        fig_disp = px.scatter(
            df_filtrado,
            x=col_carga,
            y=col_pac,
            labels={col_carga: "Carga (CSV)", col_pac: "Dosagem de PAC"},
            opacity=0.7
        )
        # Diâmetro reduzido em 1/3 (Tamanho 4) para evitar sobreposição excessiva
        fig_disp.update_traces(marker=dict(size=4, line=dict(width=0.3, color='DarkSlateGrey')))
        fig_disp.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_disp, use_container_width=True)
    else:
        st.caption("⚠️ Aguardando dados ou mapeamento das colunas de PAC e Carga.")

except FileNotFoundError:
    st.error("❌ Arquivo 'EQUILIBRIO QUIMICO.xlsx' não encontrado na raiz.")
except Exception as e:
    st.error(f"⚠️ Erro operacional: {e}")
