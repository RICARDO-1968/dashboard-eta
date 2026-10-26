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
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
        return None
        
    try:
        # Lê a primeira aba sem assumir nenhuma linha como cabeçalho ainda
        df_raw = pd.read_excel(EXCEL_FILE, sheet_name=0, header=None)
        
        # Encontra a primeira linha que não seja totalmente vazia para ser nosso cabeçalho
        row_idx = 0
        for i, row in df_raw.iterrows():
            if row.dropna().astype(str).str.strip().any():
                # Se a linha contiver palavras típicas de um cabeçalho, achamos o ponto inicial
                row_str = " ".join(row.dropna().astype(str).upper())
                if "DATA" in row_str or "A/S" in row_str or "RELAÇÃO" in row_str or "ETA" in row_str:
                    row_idx = i
                    break
        
        # Recarrega o arquivo pulando as linhas vazias do topo
        df = pd.read_excel(EXCEL_FILE, sheet_name=0, skiprows=row_idx)
        
        # Limpa os nomes das colunas de qualquer espaço invisível
        df.columns = df.columns.astype(str).str.strip()
        
        # Remove colunas e linhas completamente vazias que possam ter sobrado
        df = df.dropna(how='all', axis=0)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Força letras maiúsculas nas colunas
        df.columns = df.columns.str.upper()
        
        # Ajusta a coluna A/S
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
    # 1. EXPANDER COM DADOS BRUTOS
    with st.expander("👀 Visualizar Dados Brutos (Tabela do Excel)", expanded=False):
        st.write(f"Planilha carregada com sucesso! Total de linhas válidas: {len(df)}")
        st.dataframe(df)

    # 2. CONFIGURAÇÃO DOS FILTROS
    st.sidebar.header("Filtros de Visualização")
    
    colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
    
    if colunas_data:
        col_data = colunas_data[0]
        try:
            df[col_data] = pd.to_datetime(df[col_data]).dt.date
            datas = sorted(df[col_data].unique())
            if len(datas) > 1:
                data_sel = st.sidebar.select_slider("Selecione o período:", options=datas, value=(datas[0], datas[-1]))
                df_filtrado = df[(df[col_data] >= data_sel) & (df[col_data] <= data_sel)]
            else:
                df_filtrado = df
        except:
            df_filtrado = df
    else:
        df_filtrado = df

    # 3. CONSTRUÇÃO DO GRÁFICO DINÂMICO
    st.subheader("📈 Análise Gráfica de Parâmetros")
    
    # Seleciona apenas colunas com dados numéricos reais
    colunas_numericas = df_filtrado.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    if len(colunas_numericas) >= 2:
        eixo_x = st.selectbox("Escolha o parâmetro para o Eixo X:", colunas_numericas, index=0)
        eixo_y = st.selectbox("Escolha o parâmetro para o Eixo Y:", colunas_numericas, index=min(1, len(colunas_numericas)-1))
        
        fig = px.line(
            df_filtrado, 
            x=eixo_x, 
            y=eixo_y,
            title=f"Tendência: {eixo_y} em relação a {eixo_x}",
            markers=True
        )
        
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Encontramos a planilha, mas os dados numéricos internos ainda não foram mapeados como colunas.")
        st.write("Colunas atualmente detectadas pelo sistema:", list(df.columns))
else:
    st.info("⚠️ Aguardando a estruturação correta dos dados da planilha Excel.")
