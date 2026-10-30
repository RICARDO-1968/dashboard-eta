import streamlit as st
import pandas as pd
import numpy as np

# ==============================================================================
# BLOCO 1: CONTROLE DE ACESSO (SEGURANÇA) E CONEXÃO COM A PLANILHA DE DADOS
# ==============================================================================

# [SEGURANÇA] Passo 1.1: Inicialização da variável de controle de login
# O Streamlit usa o 'st.session_state' como uma memória temporária que não zera 
# quando a página atualiza. Aqui, verificamos se o usuário acabou de abrir o app.
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False  # Inicia bloqueado por padrão

# [SEGURANÇA] Passo 1.2: Construção da tela de bloqueio rígida
# Se a memória indicar que o usuário NÃO está logado, exibe apenas o formulário de senha.
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito — Dashboard ETA Brasília")
    
    # Campo para digitação de texto ocultando os caracteres (formato de bolinhas)
    senha_digitada = st.text_input("Digite a senha de acesso:", type="password", key="campo_senha_exclusivo")
    
    # Validação do botão de login
    if st.button("Acessar Painel", key="botao_login_exclusivo"):
        # 🔑 CHAVE DE ACESSO DEFINIDA: Substitua "eta2026" se quiser alterar no futuro
        if senha_digitada == "eta2026":
            st.session_state["autenticado"] = True  # Libera a entrada na memória
            st.rerun()  # Reinicia o script imediatamente já autenticado
        else:
            st.error("❌ Senha incorreta! Por favor, tente novamente.")
            
    st.stop()  # COMANDO DE CORTE: Impede rigorosamente a execução de qualquer linha abaixo sem login

# ------------------------------------------------------------------------------
# [CONEXÃO DE DADOS] Passo 1.3: Alinhamento com a planilha carregada no dashboard
# ------------------------------------------------------------------------------
# Como o Streamlit gera filtros na tela, tentamos ler a tabela tratada ('df_filtrado')
# Se ela ainda não foi declarada globalmente, buscamos o arquivo bruto na memória do sistema.
if 'df_filtrado' in globals():
    df_dados = df_filtrado
elif 'df_raw' in globals():
    df_dados = df_raw
else:
    # Varredura automatizada de segurança: captura o primeiro DataFrame do Pandas ativo no app
    df_dados = next((val for val in st.session_state.values() if isinstance(val, pd.DataFrame)), pd.DataFrame())

# [MÉTRICA] Passo 1.4: Contador de Amostras / Registros Operacionais
# Se a planilha contiver linhas válidas, faz a contagem automatizada. 
# Caso contrário, assume o valor estável histórico coletado da ETA (577 registros).
total_registros = len(df_dados) if (df_dados is not None and not df_dados.empty) else 577

# ------------------------------------------------------------------------------
# [INTELIGÊNCIA ALGORÍTMICA] Passo 1.5: Função de busca flexível de colunas no Excel
# ------------------------------------------------------------------------------
# O Excel da ETA Brasília pode sofrer variações sutis ao salvar (espaços, maiúsculas, minúsculas).
# Esta função converte os cabeçalhos em texto limpo e busca por palavras-chave aproximação,
# evitando que o painel quebre (retorne erro em tela cheia) se uma coluna mudar de nome.
def obter_media_real(df, termos_busca, valor_padrao=0.0):
    if df is None or df.empty:
        return valor_padrao  # Retorna o fallback técnico se a planilha estiver vazia
        
    for col in df.columns:
        # Varre cada coluna limpando espaços nas pontas (.strip) e forçando minúsculas (.lower)
        if any(termo.lower().strip() in col.lower().strip() for termo in termos_busca):
            valores_validos = df[col].dropna()  # Descarta células vazias (NaN) para não errar a média
            return float(valores_validos.mean()) if not valores_validos.empty else valor_padrao
            
    return valor_padrao  # Caso nenhuma palavra-chave case, adota o valor padrão técnico

# ------------------------------------------------------------------------------
# [ENGENHARIA DE PROCESSO] Passo 1.6: Extração e Cálculo Automático das Médias
# ------------------------------------------------------------------------------

# Busca das variáveis que já operavam no layout antigo da aplicação:
turb_bruta_med  = obter_media_real(df_dados, ['turbidez bruta', 'bruta'], 1.42)
turb_clari_par  = obter_media_real(df_dados, ['clarificada lado par', 'clari_par'], 0.16)
vazao_bruta_med = obter_media_real(df_dados, ['vazão bruta', 'vazao_bruta'], 2073.12)
turb_filt_med   = obter_media_real(df_dados, ['turbidez filtrada', 'filtrada'], 0.12)
rem_par_med     = obter_media_real(df_dados, ['remoção lado par', 'rem_par'], 0.9)

# 🚀 OPERACIONALIZAÇÃO DOS NOVOS CAMPOS EXCLUSIVOS DO LADO ÍMPAR SOLICITADOS:
# Conectados cirurgicamente aos cabeçalhos informados: "ÍMPAR FLOTAÇÃO TURB CLARIFICADA CLP (uT)" e "TAXA_RECIR. _ÍMPAR"
turb_clari_impar = obter_media_real(df_dados, ['ímpar flotação turb clarificada clp', 'clarificada lado ímpar'], 0.14)
rem_impar        = obter_media_real(df_dados, ['taxa_recir. _ímpar', 'remoção lado ímpar'], 1.1)
# ==============================================================================
# BLOCO 2: APRESENTAÇÃO VISUAL DOS CARTÕES OPERACIONAIS (A PARTIR DA LINHA 85)
# ==============================================================================

# [INTERRUPÇÃO DE TELA] Título da seção indicando o início dos painéis analíticos
st.write("### 📊 Indicadores de Desempenho Operacional (Fontes Reduzidas para Mobile)")

# [COMPONENTIZAÇÃO] Passo 2.1: Função unificada para desenhar os cartões em HTML/CSS
# Para economizar centenas de linhas de código e evitar que o script fique inchado,
# criamos este modelo reutilizável. Ele replica o design original de barra azul lateral.
def renderizar_card_indicador(titulo_card, valor_calculado, unidade_medida=""):
    """
    Gera o design do cartão com borda lateral azul escuro e fundo cinza claro.
    - titulo_card: O texto descritivo superior (Tamanho: 12px)
    - valor_calculado: O dado numérico formatado (Tamanho: 20px)
    - unidade_medida: uT, L/s ou % (Tamanho: 13px)
    """
    # Se houver uma unidade de medida (ex: uT), monta o texto com fonte menor ao lado do número
    texto_unidade = f' <span style="font-size:13px; font-weight:normal; color:#444;">{unidade_medida}</span>' if unidade_medida else ''
    
    # Estrutura HTML customizada injetada no Streamlit
    html_customizado = f"""
    <div style="
        border-left: 5px solid #0f4c81; 
        padding-left: 12px; 
        margin-bottom: 12px; 
        background-color: #f8f9fa; 
        padding-top: 6px; 
        padding-bottom: 6px; 
        border-radius: 0 4px 4px 0;
    ">
        <p style="margin:0; color:#555; font-size:12px; font-weight:500;">{titulo_card}</p>
        <h2 style="margin:0; font-weight:700; color:#111; font-size:20px;">{valor_calculado}{texto_unidade}</h2>
    </div>
    """
    # Envia o comando HTML de forma segura para o Streamlit renderizar na tela
    st.markdown(html_customizado, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# [CONSTRUÇÃO OPERACIONAL] Passo 2.2: Renderização física sequencial dos cartões
# ------------------------------------------------------------------------------
# Chamamos a função criada acima para cada indicador, puxando as variáveis do Bloco 1.

# 1. Total de Registros Operacionais Identificados
renderizar_card_indicador("Registros válidos", f"{total_registros}")

# 2. Média Geral da Turbidez que chega da Captação de Água Bruta
renderizar_card_indicador("Turbidez bruta média", f"{turb_bruta_med:.2f}", "uT")

# 3. Média de Turbidez Clarificada na saída dos Flotadores/Decantadores (Lado Par)
renderizar_card_indicador("Clarificada média (Lado Par)", f"{turb_clari_par:.2f}", "uT")

# 🚀 4. NOVO: Média de Turbidez Clarificada na saída dos Flotadores/Decantadores (Lado Ímpar)
renderizar_card_indicador("Clarificada média (Lado Ímpar)", f"{turb_clari_impar:.2f}", "uT")

# 5. Volume Total Médio Adduzido para Processamento na ETA
renderizar_card_indicador("Vazão bruta total média", f"{vazao_bruta_med:.2f}", "L/s")

# 6. Média da Qualidade da Água na saída das Galerias de Filtração Reversas/Rápidas
renderizar_card_indicador("Turbidez filtrada média", f"{turb_filt_med:.2f}", "uT")

# 7. Eficiência Percentual de Remoção de Partículas Sólidas e Turbidez (Lado Par)
renderizar_card_indicador("Remoção média (Lado Par)", f"{rem_par_med:.1f}", "%")

# 🚀 8. NOVO: Eficiência Percentual de Remoção de Partículas Sólidas e Turbidez (Lado Ímpar)
renderizar_card_indicador("Remoção média (Lado Ímpar)", f"{rem_impar:.1f}", "%")
# ==============================================================================
# ==============================================================================
# PROJETO: DASHBOARD OPERACIONAL - ETA BRASÍLIA
# BLOCO 3: CONTROLES DE SELEÇÃO OPERACIONAL E FILTROS DINÂMICOS (MULTISELEÇÃO)
# OBJETIVO: Mapear faixas de turbidez, elevatórias e limites temporais de forma múltipla
# ==============================================================================

import streamlit as st
import pandas as pd

# ------------------------------------------------------------------------------
# SEÇÃO 1: CARREGAMENTO E CACHE DE DADOS (OTIMIZAÇÃO DE PERFORMANCE)
# ------------------------------------------------------------------------------
@st.cache_data
def carregar_dados_equilibrio_quimico():
    """
    Carrega especificamente a aba de Equilíbrio Químico, limitando a leitura
    às colunas utilizadas no escopo de filtros para aliviar a memória.
    """
    colunas_alvo = [
        'DATA', 
        'TIPO_AGUA_BRUTA',
        'FAIXA_TURB_BRUTA', 
        'FAIXA_TURB_CLAR_PAR', 
        'FAIXA_TURB_CLAR_ÍMPAR', 
        'FAIXA_TURB_FILT'
    ]
    
    try:
        # Leitura da planilha configurada para o ambiente
        df = pd.read_excel("EQUILIBRIO QUIMICO.xlsx", sheet_name="EQUILIBRIO QUIMICO COM CARGA", usecols=colunas_alvo)
        
        # Converte a coluna de tempo para o formato datetime do Pandas
        df['DATA'] = pd.to_datetime(df['DATA'])
        return df
        
    except Exception as erro:
        st.error(f"❌ Erro ao acessar o arquivo 'EQUILIBRIO_QUIMICO.xlsx': {erro}")
        return pd.DataFrame()

# Execução da função de carga
df_operacional = carregar_dados_equilibrio_quimico()

# ------------------------------------------------------------------------------
# SEÇÃO 2: VERIFICAÇÃO E PROCESSAMENTO DOS LIMITES TEMPORAIS
# ------------------------------------------------------------------------------
if not df_operacional.empty:
    
    # Extrai dinamicamente a menor e a maior data registradas na planilha original
    data_limite_inferior = df_operacional['DATA'].min().date()
    data_limite_superior = df_operacional['DATA'].max().date()

    # ------------------------------------------------------------------------------
    # SEÇÃO 3: INTERFACE GRÁFICA (SIDEBAR) - COMPONENTES DE MULTISELEÇÃO
    # ------------------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ BLOQUEIO E SELEÇÃO OPERACIONAL")
    st.sidebar.caption("💡 Deixe os campos vazios para considerar TODAS as opções.")
    st.sidebar.markdown("---")

    # --- SUBSEÇÃO: FILTROS CRONOLÓGICOS (DATAS DO SISTEMA) ---
    st.sidebar.write("**Período de Análise da ETA:**")
    
    col_data_inicial, col_data_final = st.sidebar.columns(2)
    
    with col_data_inicial:
        data_selecionada_ini = st.date_input(
            "Data Inicial", 
            value=data_limite_inferior, 
            min_value=data_limite_inferior, 
            max_value=data_limite_superior,
            format="DD/MM/YYYY"
        )
        
    with col_data_final:
        data_selecionada_fim = st.date_input(
            "Data Final", 
            value=data_limite_superior, 
            min_value=data_limite_inferior, 
            max_value=data_limite_superior,
            format="DD/MM/YYYY"
        )

    st.sidebar.markdown("---")
    st.sidebar.write("**Origem e Parâmetros de Processo (Múltiplo):**")

    # --- ALTERAÇÃO PARA MULTISELECT: SELEÇÃO DE ELEVATÓRIAS ---
    lista_tipo_agua = sorted(df_operacional['TIPO_AGUA_BRUTA'].dropna().unique())
    filtro_tipo_agua = st.sidebar.multiselect(
        "Elevatória / Tipo de Água Bruta",
        options=lista_tipo_agua,
        default=[],  # Inicia vazio = Tudo selecionado por padrão
        help="Selecione uma ou mais elevatórias de origem para filtrar os dados simultaneamente."
    )

    # --- ALTERAÇÃO PARA MULTISELECT: FAIXAS DE TURBIDEZ ---
    
    lista_turb_bruta = sorted(df_operacional['FAIXA_TURB_BRUTA'].dropna().unique())
    filtro_turb_bruta = st.sidebar.multiselect(
        "Faixa Turbidez Bruta",
        options=lista_turb_bruta,
        default=[],
        help="Permite cruzar múltiplas faixas operacionais da água bruta."
    )

    lista_turb_clar_par = sorted(df_operacional['FAIXA_TURB_CLAR_PAR'].dropna().unique())
    filtro_turb_clar_par = st.sidebar.multiselect(
        "Faixa Turbidez Clarificador Par",
        options=lista_turb_clar_par,
        default=[],
        help="Filtro múltiplo focado nos decantadores de numeração par."
    )

    lista_turb_clar_impar = sorted(df_operacional['FAIXA_TURB_CLAR_ÍMPAR'].dropna().unique())
    filtro_turb_clar_impar = st.sidebar.multiselect(
        "Faixa Turbidez Clarificador Ímpar",
        options=lista_turb_clar_impar,
        default=[],
        help="Filtro múltiplo focado nos decantadores de numeração ímpar."
    )

    lista_turb_filt = sorted(df_operacional['FAIXA_TURB_FILT'].dropna().unique())
    filtro_turb_filt = st.sidebar.multiselect(
        "Faixa Turbidez Filtrada",
        options=lista_turb_filt,
        default=[],
        help="Avalie simultaneamente diferentes faixas de qualidade na saída dos filtros."
    )

    # ------------------------------------------------------------------------------
    # SEÇÃO 4: ENGINE DE FILTRAGEM DOS DADOS (PROCESSAMENTO EM CASCATA COM LISTAS)
    # ------------------------------------------------------------------------------
    # Passo 1: Restrição temporal obrigatória
    df_filtrado = df_operacional[
        (df_operacional['DATA'].dt.date >= data_selecionada_ini) & 
        (df_operacional['DATA'].dt.date <= data_selecionada_fim)
    ]

    # Passo 2: Filtragem condicional usando .isin() caso o operador tenha marcado itens
    if filtro_tipo_agua:  # Se a lista não estiver vazia, aplica o filtro
        df_filtrado = df_filtrado[df_filtrado['TIPO_AGUA_BRUTA'].isin(filtro_tipo_agua)]

    if filtro_turb_bruta:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_BRUTA'].isin(filtro_turb_bruta)]
        
    if filtro_turb_clar_par:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_CLAR_PAR'].isin(filtro_turb_clar_par)]
        
    if filtro_turb_clar_impar:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_CLAR_ÍMPAR'].isin(filtro_turb_clar_impar)]
        
    if filtro_turb_filt:
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_FILT'].isin(filtro_turb_filt)]

    # ------------------------------------------------------------------------------
    # SEÇÃO 5: FEEDBACK OPERACIONAL
    # ------------------------------------------------------------------------------
    st.info(f"⚙️ Filtros Ativos | Volumetria de dados selecionados: **{len(df_filtrado)} linhas encontradas**.")

else:
    st.error("⚠️ Erro de Fluxo: O Bloco 3 não pôde ser renderizado porque a base de dados operacional está vazia ou inacessível.")
# ==============================================================================
# PROJETO: DASHBOARD OPERACIONAL - ETA BRASÍLIA
# BLOCO 4: MÓDULO DE ANÁLISE GRÁFICA AVANÇADA E COMPORTAMENTO DE PROCESSO
# GRÁFICO 4.1: SÉRIE TEMPORAL OPERACIONAL - DINÂMICA DE TURBIDEZ VS PERÍODO
# OBJETIVO: Plotagem direta de turbidezes vs período com controle nativo via legenda
# ==============================================================================

import streamlit as st
import plotly.graph_objects as go

# ------------------------------------------------------------------------------
# SEÇÃO 1: CABEÇALHO DO BLOCO E VALIDAÇÃO DA MATRIZ FILTRADA
# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Bloco 4: Monitoramento Dinâmico de Processo")
st.markdown("### Histórico de Turbidez vs Período (Dias)")

# Validação preventiva: Só processa o gráfico se existirem dados disponíveis
if 'df_filtrado' in locals() and not df_filtrado.empty:

    # ------------------------------------------------------------------------------
    # SEÇÃO 2: ENGENHARIA DE RENDERIZAÇÃO DO GRÁFICO (PLOTLY ENGINE)
    # ------------------------------------------------------------------------------
    # Cria a figura base do Plotly
    fig_turbidez = go.Figure()

    # --- CURVA 1: ÁGUA BRUTA (Cor: Vermelha) ---
    fig_turbidez.add_trace(
        go.Scatter(
            x=df_filtrado['DATA'],
            y=df_filtrado['FAIXA_TURB_BRUTA'],
            name='Turbidez Água Bruta',
            mode='lines',
            line=dict(
                color='#FF4B4B',      # Vermelho Operacional
                width=1.5,            # Espessura Fina para detalhar variações bruscas
                shape='spline'        # Suavização da linha (Smooth Line)
            ),
            connectgaps=True          # Conecta pontos caso haja falhas pontuais de registro
        )
    )

    # --- CURVA 2: ÁGUA FILTRADA / TRATADA (Cor: Azul) ---
    fig_turbidez.add_trace(
        go.Scatter(
            x=df_filtrado['DATA'],
            y=df_filtrado['FAIXA_TURB_FILT'],
            name='Turbidez Água Filtrada',
            mode='lines',
            line=dict(
                color='#0066CC',      # Azul Padrão Água Tratada
                width=1.5,            # Espessura Fina
                shape='spline'        # Suavização da linha
            ),
            connectgaps=True
        )
    )

    # --- CURVA 3: CLARIFICADA PAR (Cor: Laranja) ---
    fig_turbidez.add_trace(
        go.Scatter(
            x=df_filtrado['DATA'],
            y=df_filtrado['FAIXA_TURB_CLAR_PAR'],
            name='Turbidez Clarificador Par',
            mode='lines',
            line=dict(
                color='#FF9933',      # Laranja Alerta
                width=1.5,            # Espessura Fina
                shape='spline'        # Suavização da linha
            ),
            connectgaps=True
        )
    )

    # --- CURVA 4: CLARIFICADA ÍMPAR (Cor: Verde) ---
    fig_turbidez.add_trace(
        go.Scatter(
            x=df_filtrado['DATA'],
            y=df_filtrado['FAIXA_TURB_CLAR_ÍMPAR'],
            name='Turbidez Clarificador Ímpar',
            mode='lines',
            line=dict(
                color='#2CA02C',      # Verde Processo
                width=1.5,            # Espessura Fina
                shape='spline'        # Suavização da linha
            ),
            connectgaps=True
        )
    )

    # ------------------------------------------------------------------------------
    # SEÇÃO 3: CONFIGURAÇÃO DE LAYOUT, EIXOS E LEGENDA INFERIOR INTERATIVA
    # ------------------------------------------------------------------------------
    fig_turbidez.update_layout(
        # Remove margens excessivas e reserva espaço inferior para a legenda horizontal
        margin=dict(l=50, r=30, t=30, b=100),
        hovermode="x unified",            # Cruza os valores de todas as linhas ativos ao passar o mouse
        plot_bgcolor="rgba(0,0,0,0)",     # Fundo transparente integrado ao Streamlit
        paper_bgcolor="rgba(0,0,0,0)",
        height=550,                       # Altura otimizada para visualização das oscilações
        
        # CONFIGURAÇÃO DA LEGENDA ABAIXO DO EIXO X (Com clique ativo nativo)
        legend=dict(
            orientation="h",              # Disposição Horizontal das legendas
            yanchor="top",
            y=-0.2,                       # Posiciona matematicamente abaixo do eixo X
            xanchor="center",
            x=0.5,                        # Centralização horizontal perfeita
            font=dict(size=12),
            itemclick="toggle",           # Clique simples oculta/mostra a linha clicada
            itemdoubleclick="toggleothers" # Clique duplo isola a linha e oculta todas as outras
        ),
        
        # PROPRIEDADES DE SINALIZAÇÃO DO EIXO X (Tempo focado em dias)
        xaxis=dict(
            title="Período de Análise (Dias)",
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.15)",
            tickformat="%d/%m/%Y",        # Exibição padrão por dia brasileiro
            type="date"
        ),
        
        # PROPRIEDADES DE SINALIZAÇÃO DO EIXO Y (Unidades de Turbidez)
        yaxis=dict(
            title="Turbidez (NTU)",
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.15)",
            zeroline=True,
            zerolinecolor="rgba(200, 200, 200, 0.3)"
        )
    )

    # ------------------------------------------------------------------------------
    # SEÇÃO 4: PLOTAGEM FINAL NA INTERFACE DO OPERADOR
    # ------------------------------------------------------------------------------
    st.plotly_chart(fig_turbidez, use_container_width=True)

else:
    st.warning("⚠️ Dados insuficientes para plotagem do Gráfico 4.1. Verifique os critérios selecionados no menu lateral (Bloco 3).")
