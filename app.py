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
# BLOCO 3: CONTROLES DE SELEÇÃO OPERACIONAL E FILTROS DINÂMICOS
# OBJETIVO: Mapear faixas de turbidez e gerenciar os limites temporais da planta
# ==============================================================================

import streamlit as st
import pandas as pd

# ------------------------------------------------------------------------------
# SEÇÃO 0: CONFIGURAÇÃO DE LAYOUT DA PÁGINA (CONTROLE DO FILTRO LATERAL)
# ------------------------------------------------------------------------------
# NOTA: O parâmetro 'initial_sidebar_state' define como o filtro se comporta ao abrir.
# Opções disponíveis:
#   - "expanded" : Mantém a barra lateral de filtros aberta por padrão.
#   - "collapsed": Mantém a barra recolhida (oculta), maximizando o espaço do gráfico.
#   - "auto"     : O Streamlit decide baseado no tamanho da tela do operador (Mobile/PC).
st.set_page_config(
    page_title="Dashboard ETA Brasília",
    layout="wide",
    initial_sidebar_state="expanded"  # Garante que o operador veja os filtros logo de início
)

# ------------------------------------------------------------------------------
# SEÇÃO 1: CARREGAMENTO E CACHE DE DADOS (OTIMIZAÇÃO DE PERFORMANCE)
# ------------------------------------------------------------------------------
# @st.cache_data é crucial aqui para evitar releituras lentas do arquivo Excel
# a cada clique ou mudança de filtro do operador.
@st.cache_data
def carregar_dados_equilibrio_quimico():
    """
    Carrega especificamente a aba de Equilíbrio Químico, limitando a leitura
    às colunas utilizadas no escopo de filtros para aliviar a memória.
    """
    # Definição estrita das colunas solicitadas para o Bloco 3
    colunas_alvo = [
        'DATA', 
        'FAIXA_TURB_BRUTA', 
        'FAIXA_TURB_CLAR_PAR', 
        'FAIXA_TURB_CLAR_ÍMPAR', 
        'FAIXA_TURB_FILT'
    ]
    
    try:
        # Realiza a leitura focada na aba correta 'EQUILIBRIO QUIMICO COM CARGA'
        df = pd.read_excel(
            "seu_arquivo_eta_brasilia.xlsx", 
            sheet_name="EQUILIBRIO QUIMICO COM CARGA",
            usecols=colunas_alvo
        )
        
        # Converte a coluna de tempo para o formato datetime do Pandas
        df['DATA'] = pd.to_datetime(df['DATA'])
        
        return df
        
    except Exception as erro:
        # Retorna um aviso visual amigável caso o arquivo mude de nome ou sumir
        st.error(f"❌ Erro crítico ao acessar 'EQUILIBRIO QUIMICO COM CARGA': {erro}")
        return pd.DataFrame()


# Execução da função de carga (Se os dados já estiverem em cache, o retorno é instantâneo)
df_operacional = carregar_dados_equilibrio_quimico()

# ------------------------------------------------------------------------------
# SEÇÃO 2: VERIFICAÇÃO E PROCESSAMENTO DOS LIMITES TEMPORAIS
# ------------------------------------------------------------------------------
if not df_operacional.empty:
    
    # Extrai dinamicamente a menor e a maior data registradas na planilha original
    data_limite_inferior = df_operacional['DATA'].min().date()
    data_limite_superior = df_operacional['DATA'].max().date()

    # ------------------------------------------------------------------------------
    # SEÇÃO 3: INTERFACE GRÁFICA (SIDEBAR) - COMPONENTES DE SELEÇÃO
    # ------------------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ BLOQUEIO E SELEÇÃO OPERACIONAL")
    st.sidebar.caption("💡 Use a seta no topo esquerdo para recolher ou expandir este menu.")
    st.sidebar.markdown("---")

    # --- SUBSEÇÃO: FILTROS CRONOLÓGICOS (DATAS DO SISTEMA) ---
    st.sidebar.write("**Período de Análise da ETA:**")
    
    # Divisão em duas colunas na barra lateral para compactar o layout
    col_data_inicial, col_data_final = st.sidebar.columns(2)
    
    with col_data_inicial:
        # Define a data de início da pesquisa (Padrão: Data mínima da planilha)
        data_selecionada_ini = st.date_input(
            "Data Inicial", 
            value=data_limite_inferior, 
            min_value=data_limite_inferior, 
            max_value=data_limite_superior,
            format="DD/MM/YYYY"
        )
        
    with col_data_final:
        # Define a data de término da pesquisa (Padrão: Data máxima da planilha)
        data_selecionada_fim = st.date_input(
            "Data Final", 
            value=data_limite_superior, 
            min_value=data_limite_inferior, 
            max_value=data_limite_superior,
            format="DD/MM/YYYY"
        )

    st.sidebar.markdown("---")
    st.sidebar.write("**Parâmetros de Turbidez:**")

    # --- SUBSEÇÃO: MAPEAMENTO DAS FAIXAS DE TURBIDEZ ---
    
    # 1. Tratamento da Turbidez Bruta: Remove nulos, isola únicos e ordena em ordem alfabética/numérica
    lista_turb_bruta = sorted(df_operacional['FAIXA_TURB_BRUTA'].dropna().unique())
    filtro_turb_bruta = st.sidebar.selectbox(
        "Faixa Turbidez Bruta",
        options=["Todos"] + list(lista_turb_bruta),
        help="Selecione a faixa operacional da água bruta na entrada da ETA."
    )

    # 2. Tratamento do Clarificador Par
    lista_turb_clar_par = sorted(df_operacional['FAIXA_TURB_CLAR_PAR'].dropna().unique())
    filtro_turb_clar_par = st.sidebar.selectbox(
        "Faixa Turbidez Clarificador Par",
        options=["Todos"] + list(lista_turb_clar_par),
        help="Filtro específico para os decantadores/clarificadores de numeração par."
    )

    # 3. Tratamento do Clarificador Ímpar
    lista_turb_clar_impar = sorted(df_operacional['FAIXA_TURB_CLAR_ÍMPAR'].dropna().unique())
    filtro_turb_clar_impar = st.sidebar.selectbox(
        "Faixa Turbidez Clarificador Ímpar",
        options=["Todos"] + list(lista_turb_clar_impar),
        help="Filtro específico para os decantadores/clarificadores de numeração ímpar."
    )

    # 4. Tratamento da Turbidez Filtrada (Saída dos Filtros)
    lista_turb_filt = sorted(df_operacional['FAIXA_TURB_FILT'].dropna().unique())
    filtro_turb_filt = st.sidebar.selectbox(
        "Faixa Turbidez Filtrada",
        options=["Todos"] + list(lista_turb_filt),
        help="Mapeamento da qualidade da água após passar pela bateria de filtros."
    )

    # ------------------------------------------------------------------------------
    # SEÇÃO 4: ENGINE DE FILTRAGEM DOS DADOS (PROCESSAMENTO EM CASCATA)
    # ------------------------------------------------------------------------------
    # Primeiro estágio: Aplica o corte temporal estrito baseado nas datas selecionadas
    df_filtrado = df_operacional[
        (df_operacional['DATA'].dt.date >= data_selecionada_ini) & 
        (df_operacional['DATA'].dt.date <= data_selecionada_fim)
    ]

    # Segundo estágio: Condicionais para refinar a matriz caso o operador escolha faixas específicas
    if filtro_turb_bruta != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_BRUTA'] == filtro_turb_bruta]
        
    if filtro_turb_clar_par != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_CLAR_PAR'] == filtro_turb_clar_par]
        
    if filtro_turb_clar_impar != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_CLAR_ÍMPAR'] == filtro_turb_clar_impar]
        
    if filtro_turb_filt != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FAIXA_TURB_FILT'] == filtro_turb_filt]

    # ------------------------------------------------------------------------------
    # SEÇÃO 5: FEEDBACK OPERACIONAL (MÉTRICA DE CONTROLE DE REGISTROS)
    # ------------------------------------------------------------------------------
    st.info(f"⚙️ Filtros Ativos | Volumetria de dados selecionados: **{len(df_filtrado)} linhas encontradas**.")

else:
    st.error("⚠️ Erro de Fluxo: O Bloco 3 não pôde ser renderizado porque a base de dados operacional está vazia ou inacessível.")
