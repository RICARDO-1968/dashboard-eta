import streamlit as st
import pandas as pd
import numpy as np

# ==============================================================================
# BLOCO 1: CONTROLE DE ACESSO TOTALMENTE ISOLADO (NOVA SENHA)
# ==============================================================================

# Inicializa o estado de autenticação na memória limpa do app
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Tela de bloqueio rígida
if not st.session_state["autenticado"]:
    st.title("🔒 Acesso Restrito — Dashboard ETA Brasília")
    
    # Campo limpo para digitação
    senha_digitada = st.text_input("Digite a senha de acesso:", type="password", key="campo_senha_exclusivo")
    
    if st.button("Acessar Painel", key="botao_login_exclusivo"):
        # 🔑 DEFINA SUA SENHA DEFINITIVA AQUI (Substitua eta2026 se quiser outra)
        if senha_digitada == "eta2026":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta! Por favor, tente novamente.")
    st.stop() # Garante que nada abaixo desta linha execute sem o login aceito

# --- DAQUI PARA BAIXO O USUÁRIO ESTÁ LOGADO COM SUCESSO ---
