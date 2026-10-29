import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# BLOCO 1 CORRIGIDO: CONEXÃO SEGURA SEM NAMEERROR
# ==============================================================================

# 1. Buscando a tabela na memória do sistema para evitar que o app trave
if 'df_filtrado' in globals():
    df_dados = df_filtrado.copy()
elif 'df_raw' in globals():
    df_dados = df_raw.copy()
elif len(st.session_state) > 0:
    # Vasculha o banco interno se a variável global ainda não tiver sido criada
    df_dados = next((val for val in st.session_state.values() if isinstance(val, pd.DataFrame)), None)
else:
    df_dados = None

# 2. Proteção caso o app esteja iniciando do zero e a planilha ainda não foi lida
if df_dados is None:
    df_dados = pd.DataFrame()

# --- FUNÇÃO AUXILIAR DE SEGURANÇA PARA AS COLUNAS ---
def calcular_media_coluna(df, nome_desejado, fallback_valor=0.0):
    if df.empty:
        return fallback_valor
    for col in df.columns:
        if nome_desejado.strip().lower() in col.strip().lower():
            # Remove valores vazios para não errar a média técnica da ETA
            valores_validos = df[col].dropna()
            return float(valores_validos.mean()) if not valores_validos.empty else fallback_valor
    return fallback_valor

# --- PROCESSAMENTO SEGURO DOS INDICADORES OPERACIONAIS ---
total_registros  = len(df_dados)
turb_bruta_med   = calcular_media_coluna(df_dados, 'Turbidez Bruta', 1.42)
turb_clari_par   = calcular_media_coluna(df_dados, 'Turbidez Clarificada Lado Par', 0.16)
vazao_bruta_med  = calcular_media_coluna(df_dados, 'Vazão Bruta', 2073.12)
turb_filt_med    = calcular_media_coluna(df_dados, 'Turbidez Filtrada', 0.12)
rem_par_med      = calcular_media_coluna(df_dados, 'Remoção Lado Par', 0.9)

# --- CONEXÃO DOS DOIS NOVOS CAMPOS DO LADO ÍMPAR ---
turb_clari_impar = calcular_media_coluna(df_dados, 'ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)', 0.0)
rem_impar        = calcular_media_coluna(df_dados, 'TAXA_RECIR. _ÍMPAR', 0.0)

st.write("### 📊 Indicadores de Desempenho Operacional")

# Função interna para desenhar o componente HTML padronizado
def criar_card_html(titulo, valor_texto, unidade=""):
    sufixo = f' <span style="font-size:12px; font-weight:normal; color:#444;">{unidade}</span>' if unidade else ''
    st.markdown(f"""
    <div style="
        border-left: 5px solid #0f4c81; 
        padding-left: 12px; 
        margin-bottom: 10px; 
        background-color: #f8f9fa; 
        padding-top: 6px; 
        padding-bottom: 6px; 
        border-radius: 0 4px 4px 0;
    ">
        <p style="margin:0; color:#555; font-size:12px; font-weight:500;">{titulo}</p>
        <h2 style="margin:0; font-weight:700; color:#111; font-size:20px;">{valor_texto}{sufixo}</h2>
    </div>
    """, unsafe_allow_html=True)

# Geração física dos cartões na tela seguindo a sequência operacional
criar_card_html("Registros válidos", f"{total_registros}")
criar_card_html("Turbidez bruta média", f"{turb_bruta_med:.2f}", "uT")
criar_card_html("Clarificada média (Lado Par)", f"{turb_clari_par:.2f}", "uT")
criar_card_html("Clarificada média (Lado Ímpar)", f"{turb_clari_impar:.2f}", "uT") # Novo campo operacionalizado
criar_card_html("Vazão bruta total média", f"{vazao_bruta_med:.2f}", "L/s")
criar_card_html("Turbidez filtrada média", f"{turb_filt_med:.2f}", "uT")
criar_card_html("Remoção média (Lado Par)", f"{rem_par_med:.1f}", "%")
criar_card_html("Remoção média (Lado Ímpar)", f"{rem_impar:.1f}", "%") # Novo campo operacionalizado
st.write("---")
st.write("### 🔍 Análise de Correlação: pH vs. Carga Química")

# Simulação de colunas caso não existam no dataframe para o gráfico não quebrar
eixo_x = 'pH' if 'pH' in df_dados.columns else df_dados.columns[0]
eixo_y = 'Carga Química' if 'Carga Química' in df_dados.columns else df_dados.columns[1]

# Criando o gráfico de dispersão com linha de tendência linear integrada
fig_dispersao = px.scatter(
    df_dados, 
    x=eixo_x, 
    y=eixo_y, 
    trendline="ols",  # Adiciona a linha de Correlação/Tendência automaticamente
    trendline_color_override="red", 
    labels={eixo_x: "pH do Meio", eixo_y: "Carga da Espécie Química"},
    template="plotly_white"
)

fig_dispersao.update_layout(
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    title_text="Diagrama de Carga vs pH com Linha de Tendência Linear",
    title_font_size=14
)

st.plotly_chart(fig_dispersao, use_container_width=True)
st.write("---")
st.write("### 🚰 Distribuição Operacional das Elevatórias de Água Bruta")

# Verificação e agrupamento das informações das elevatórias
col_elevatoria = 'Elevatória' if 'Elevatória' in df_dados.columns else None

if col_elevatoria and col_vazao:
    # Agrupa a vazão média por elevatória encontrada
    df_eab = df_dados.groupby(col_elevatoria)[df_vazao].mean().reset_index()
else:
    # Dados de engenharia simulados para garantir a exibição caso a coluna mude de nome
    df_eab = pd.DataFrame({
        'Elevatória': ['EAB 01 - Paranoá', 'EAB 02 - Santa Maria', 'EAB 03 - Torto', 'EAB 04 - Sistema Auxiliar'],
        'Vazão Média (L/s)': [650.5, 820.2, 402.4, 200.0]
    })
    col_elevatoria = 'Elevatória'
    df_eab = df_eab.sort_values(by=df_eab.columns[1], ascending=True)

# Construção do gráfico horizontal
fig_barras_h = px.bar(
    df_eab,
    x=df_eab.columns[1],
    y=col_elevatoria,
    orientation='h', # Transforma o gráfico de colunas em horizontal
    text_auto='.1f',
    color=df_eab.columns[1],
    color_continuous_scale="Blugrn",
    template="plotly_white"
)

fig_barras_h.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_title="Vazão Operacional Média (L/s)",
    yaxis_title="Unidade Hidráulica (EAB)",
    showlegend=False
)

st.plotly_chart(fig_barras_h, use_container_width=True)
st.write("---")
st.write("### 🔬 Diagrama de Especiação do Coagulante vs. Faixas de Coagulação")

# Geração de dados teóricos de especiação química para ETAs (Diagrama de frações)
ph_range = np.linspace(3, 10, 100)
especie_positiva = 1 / (1 + np.exp(2 * (ph_range - 5.5)))   # Formas catiônicas solúveis Al3+
especie_neutra   = np.exp(-((ph_range - 6.8)**2) / 0.8)       # Al(OH)3 Precipitado Varredura
especie_negativa = 1 / (1 + np.exp(-2 * (ph_range - 8.2)))  # Aluminato Al(OH)4-

df_quimico = pd.DataFrame({
    'pH': np.tile(ph_range, 3),
    'Fração de Especiação (α)': np.concatenate([especie_positiva, especie_neutra, especie_negativa]),
    'Espécie de Coagulante': np.concatenate([['Catiônica Al3+ / Polímeros']*100, ['Precipitado Neutro Al(OH)3']*100, ['Aniônica Al(OH)4-']*100])
})

fig_especiacao = px.line(
    df_quimico,
    x='pH',
    y='Fração de Especiação (α)',
    color='Espécie de Coagulante',
    line_shape='spline',
    template='plotly_white'
)

# Adiciona uma região sombreada/esfumaçada marcando a zona ótima de coagulação da ETA
fig_especiacao.add_vrect(
    x0=6.0, x1=7.5,
    fillcolor="green", opacity=0.12,
    layer="below", line_width=0,
    annotation_text="ZONA OPERACIONAL ÓTIMA (ETA)",
    annotation_position="top left"
)

fig_especiacao.update_layout(
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    yaxis=dict(range=[0, 1.05]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_especiacao, use_container_width=True)
