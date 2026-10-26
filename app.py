import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo na raiz
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

@st.cache_data
def load_data():
    # Verifica se o arquivo realmente existe no servidor do GitHub
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub. Verifique o nome e a extensão.")
        return None
        
    try:
        # Força a leitura da primeira aba disponível, não importa o nome dela
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        
        # Limpa os nomes das colunas de qualquer espaço invisível ou quebra de linha
        df.columns = df.columns.astype(str).str.strip()
        
        # Força letras maiúsculas para evitar erros de digitação (ex: Data -> DATA)
        df.columns = df.columns.str.upper()
        
        # Mapeia e corrige especificamente a coluna A/S independente de como foi digitada
        rename_dict = {}
        for col in df.columns:
            if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                rename_dict[col] = "A/S (CM3/L)"
        
        df = df.rename(columns=rename_dict)
        return df
    except Exception as e:
        st.error(f"❌ Erro crítico ao abrir o arquivo Excel: {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. EXPANDER COM DADOS BRUTOS (Para checar se o Excel abriu)
    with st.expander("👀 Visualizar Dados Brutos (Tabela do Excel)", expanded=True):
        st.write(f"Planilha carregada com sucesso! Total de linhas: {len(df)}")
        st.dataframe(df)

    # 2. CONFIGURAÇÃO DOS FILTROS (Se houver coluna de data)
    st.sidebar.header("Filtros de Visualização")
    
    # Procura por colunas que possam ser a Data
    colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
    
    if colunas_data:
        col_data = colunas_data[0]
        try:
            df[col_data] = pd.to_datetime(df[col_data]).dt.date
            datas = sorted(df[col_data].unique())
            if len(datas) > 1:
                data_sel = st.sidebar.select_slider("Selecione o período:", options=datas, value=(datas[0], datas[-1]))
                df_filtrado = df[(df[col_data] >= data_sel[0]) & (df[col_data] <= data_sel[1])]
            else:
                df_filtrado = df
        except:
            df_filtrado = df
    else:
        df_filtrado = df

    # 3. CONSTRUÇÃO DO GRÁFICO DINDÂMICO
    st.subheader("📈 Análise Gráfica de Parâmetros")
    
    # Seleciona apenas colunas que possuem números para os eixos
    colunas_numericas = df_filtrado.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    if len(colunas_numericas) >= 2:
        eixo_x = st.selectbox("Escolha o parâmetro para o Eixo X:", colunas_numericas, index=0)
        eixo_y = st.selectbox("Escolha o parâmetro para o Eixo Y:", colunas_numericas, index=min(1, len(colunas_numericas)-1))
        
        # Cria o gráfico com linhas e pontos marcados explicitamente
        fig = px.line(
            df_filtrado, 
            x=eixo_x, 
            y=eixo_y,
            title=f"Tendência: {eixo_y} em relação a {eixo_x}",
            markers=True # Garante que os pontos fiquem visíveis no celular
        )
        
        fig.update_layout(hovermode="x unified", legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ O Excel foi lido, mas não encontramos colunas com dados numéricos suficientes para desenhar o gráfico.")
        st.write("Colunas identificadas na sua planilha:", list(df.columns))

else:
    if df is dict or df is None:
        st.warning("⚠️ Aguardando a correta leitura do arquivo Excel para estruturar os filtros e gráficos.")
