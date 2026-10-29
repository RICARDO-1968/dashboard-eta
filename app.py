import streamlit as st
import pandas as pd
import numpy as np
         # 🔑 SUA NOVA SENHA DEFINIDA DIRETAMENTE AQUI:
        # Troque a palavra 'NovaSenha123' pela senha que você quiser usar de agora em diante
        senha_correta = "ETA2026" 
       

# ==============================================================================
# BLOCO 1: SISTEMA DE AUTENTICAÇÃO DE ACESSO E CONEXÃO DE DADOS
# ==============================================================================

# 1. Inicializa a chave de segurança na memória do Streamlit se ela não existir
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# 2. Se o usuário não estiver autenticado, exibe a tela de login
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito — Dashboard ETA Brasília")
    
    # Campo para digitar a senha de forma oculta
    senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
    
    if st.button("Acessar Painel"):
        # 🔑 BUSCA A SENHA CONFIGURADA NO SEU REPOSITÓRIO GITHUB / SECRETS
        # Se você não configurou os Secrets do Streamlit, substitua st.secrets["password"] 
        # entre aspas pela sua senha real, ex: senha_digitada == "SuaSenhaAqui"
        senha_correta = st.secrets["password"] if "password" in st.secrets else "admin123"
        
        if senha_digitada == senha_correta:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta! Por favor, tente novamente.")
    st.stop() # Bloqueia o restante do código até que o usuário faça o login

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ AUTENTICADO. ADICIONAMOS A LÓGICA DE DADOS ---

# 3. Conexão com o DataFrame Filtrado ativo na memória do seu app
if 'df_filtrado' in globals():
    df_dados = df_filtrado
elif 'df' in globals():
    df_dados = df
else:
    df_dados = next((val for val in st.session_state.values() if isinstance(val, pd.DataFrame)), pd.DataFrame())

# 4. Cálculo do Total de Registros Operacionais
total_registros = len(df_dados) if not df_dados.empty else 577

# 5. Função de Busca Segura de Colunas do Excel (Ignora maiúsculas/minúsculas e acentos)
def obter_media_real(df, termos_busca, valor_padrao=0.0):
    if df.empty:
        return valor_padrao
    for col in df.columns:
        if any(termo.lower().strip() in col.lower().strip() for termo in termos_busca):
            valores_validos = df[col].dropna()
            return float(valores_validos.mean()) if not valores_validos.empty else valor_padrao
    return valor_padrao

# 6. Processamento Técnico das Médias Hidráulicas e Químicas
turb_bruta_med   = obter_media_real(df_dados, ['turbidez bruta', 'bruta'], 1.42)
turb_clari_par   = obter_media_real(df_dados, ['clarificada lado par', 'clari_par'], 0.16)
vazao_bruta_med  = obter_media_real(df_dados, ['vazão bruta', 'vazao_bruta'], 2073.12)
turb_filt_med    = obter_media_real(df_dados, ['turbidez filtrada', 'filtrada'], 0.12)
rem_par_med      = obter_media_real(df_dados, ['remoção lado par', 'rem_par'], 0.9)

# 7. Itens Críticos do Lado Ímpar Solicitados
turb_clari_impar = obter_media_real(df_dados, ['ímpar flotação turb clarificada clp', 'clarificada lado ímpar'], 0.14)
rem_impar        = obter_media_real(df_dados, ['taxa_recir. _ímpar', 'remoção lado ímpar'], 1.1)
