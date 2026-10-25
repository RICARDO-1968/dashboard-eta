import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ETA Brasília - Diagnóstico", layout="wide")

st.title("🛠️ Diagnóstico do Sistema - ETA Brasília")

# 1. Mostra quais arquivos realmente existem na pasta do GitHub
st.subheader("1. Arquivos encontrados na pasta:")
arquivos_na_pasta = os.listdir(".")
st.write(arquivos_na_pasta)

# 2. Tenta ler o arquivo Excel com variações comuns de nome
nome_esperado = "EQUILÍBRIO QUÍMICO H2O.xlsx"

st.subheader("2. Tentando ler o arquivo Excel:")

if os.path.exists(nome_esperado):
    st.success(f"O arquivo '{nome_esperado}' foi encontrado com sucesso!")
    try:
        # Lê apenas a primeira aba para testar
        xls = pd.ExcelFile(nome_esperado)
        st.write("Abas encontradas no seu arquivo:", xls.sheet_names)
        
        df = pd.read_excel(nome_esperado, sheet_name=xls.sheet_names[0])
        st.write("Colunas encontradas na primeira aba:", list(df.columns))
        st.write("Primeiras 3 linhas dos seus dados:", df.head(3))
    except Exception as e:
        st.error(f"Erro ao abrir o conteúdo do Excel: {e}")
else:
    st.error(f"O sistema não achou o arquivo com o nome exato: '{nome_esperado}'")
    st.info("Olhe na lista do item 1 acima e veja se o nome do seu arquivo está escrito um pouco diferente.")
