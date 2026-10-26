import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo na raiz
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
else:
    try:
        # Abre o Excel diretamente na aba correta que nosso código descobriu
        df = pd.read_excel(EXCEL_FILE, sheet_name="MODELO EQUÍL. E CARGA")
        
        # 1. VISUALIZAÇÃO CRUA IMEDIATA (Sem nenhum filtro para não zerar os dados)
        with st.expander("👀 Verificar Tabela de Dados Carregada", expanded=True):
            st.success(f"✅ Arquivo aberto na aba 'MODELO EQUÍL. E CARGA'. Linhas detectadas: {len(df)}")
            st.dataframe(df)

        # 2. SEGUNDA TENTATIVA DE LEITURA (Caso a primeira linha esteja vazia e oculte os dados)
        with st.expander("🔍 Segunda Opção de Leitura (Caso a de cima falhe)", expanded=False):
            df_alternativo = pd.read_excel(EXCEL_FILE, sheet_name="MODELO EQUÍL. E CARGA", header=None)
            st.dataframe(df_alternativo)

        # Limpa e padroniza os nomes das colunas em MAIÚSCULAS
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # CONVERSÃO AUTOMÁTICA DE VÍRGULA PARA PONTO
        colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
        
        for col in df.columns:
            if not any(ignorar in col for ignorar in colunas_texto):
                # Substitui a vírgula pelo ponto e remove espaços
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Garante a grafia correta da coluna A/S
        rename_dict = {}
        for col in df.columns:
            if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                rename_dict[col] = "A/S (CM3/L)"
        df = df.rename(columns=rename_dict)

        # 3. CONSTRUÇÃO DO GRÁFICO DINÂMICO
        st.subheader("📈 Gráfico de Análise e Tendência")
        colunas_numericas = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if len(colunas_numericas) >= 2:
            eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
            eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
            
            fig = px.line(
                df, 
                x=eixo_x, 
                y=eixo_y,
                title=f"Variação: {eixo_y} em relação a {eixo_x}",
                markers=True
            )
            
            fig.update_traces(mode='markers+lines')
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Aguardando a identificação das colunas numéricas para gerar o gráfico.")
            
    except Exception as e:
        st.error(f"❌ Erro crítico ao processar a aba: {e}")
