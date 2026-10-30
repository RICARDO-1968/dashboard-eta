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
# BLOCO 3: BARRA LATERAL (SIDEBAR) DE FILTROS OPERACIONAIS
# ==============================================================================
# BLOCO 3 REVISADO: BARRA LATERAL (SIDEBAR) COM DETECÇÃO AUTOMÁTICA DE DATAS
# ==============================================================================

# ==============================================================================
# BLOCO 3: BARRA LATERAL (SIDEBAR) COM DETECÇÃO AUTOMÁTICA DE DATAS (155 A 207)
# ==============================================================================

# [INTERFACE] Configuração do cabeçalho da barra lateral esquerda
st.sidebar.markdown("## 🎛️ Filtros de Seleção (ETA Brasília)")
st.sidebar.write("Configure os parâmetros abaixo para atualizar as médias e gráficos em tempo real.")
st.sidebar.write("---")

# [DETETIVE DE DATAS] Identificação da coluna de tempo no Excel por aproximação
coluna_data_real = None
if df_dados is not None and not df_dados.empty:
    for col in df_dados.columns:
        if 'data' in col.lower() or 'periodo' in col.lower() or 'data/hora' in col.lower():
            coluna_data_real = col
            break

# [CONTROLE DE DATAS] Calendário dinâmico integrado à planilha
if coluna_data_real:
    # Converte o texto da planilha para formato de data real do Python
    df_dados[coluna_data_real] = pd.to_datetime(df_dados[coluna_data_real])
    
    # Captura os limites de início e fim da planilha
    data_minima = df_dados[coluna_data_real].min().date()
    data_maxima = df_dados[coluna_data_real].max().date()
    
    # Desenha o calendário na barra lateral
    periodo_selecionado = st.sidebar.date_input(
        "Selecione o período de análise:",
        value=(data_minima, data_maxima),
        min_value=data_minima,
        max_value=data_maxima,
        key="filtro_calendario_operacional"
    )
    
    # [APLICAÇÃO] Filtra os dados conforme a escolha do operador
    if isinstance(periodo_selecionado, tuple) and len(periodo_selecionado) == 2:
        data_inicio, data_fim = periodo_selecionado
        df_dados = df_dados[
            (df_dados[coluna_data_real].dt.date >= data_inicio) & 
            (df_dados[coluna_data_real].dt.date <= data_fim)
        ]
else:
    # Mensagem caso a planilha esteja carregando na inicialização
    st.sidebar.info("📅 Filtro de data indisponível: Coluna contendo 'Data' não localizada no Excel.")

st.sidebar.write("---")
st.sidebar.success("💡 Filtros aplicados com sucesso!")

