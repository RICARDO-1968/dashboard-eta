import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo validado na raiz do repositório
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub. Verifique o nome.")
        return None
        
    try:
        # 1. Lê a planilha em formato de tabela comum (a primeira linha já é o cabeçalho)
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        
        # 2. Limpa os nomes das colunas de espaços invisíveis e força MAIÚSCULAS
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # Remove colunas fantasmas geradas pelo Excel (Unnamed)
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
        df = df.dropna(how='all', axis=0)
        
        # 3. CONVERSÃO AUTOMÁTICA DE VÍRGULA PARA PONTO
        # Lista de colunas comuns que sabemos que não são números decimais para o gráfico
        colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
        
        for col in df.columns:
            # Se não for uma coluna de texto/data conhecida, processa como número
            if not any(ignorar in col for ignorar in colunas_texto):
                # Substitui a vírgula pelo ponto e força a transformação em número decimal
                df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 4. Ajusta especificamente a grafia da coluna A/S se necessário
        rename_dict = {}
        for col in df.columns:
            if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                rename_dict[col] = "A/S (CM3/L)"
        df = df.rename(columns=rename_dict)
        
        return df
    except Exception as e:
        st.error(f"❌ Erro crítico ao processar o arquivo Excel: {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    # 1. EXPANDER PARA CONFERÊNCIA DOS DADOS HIGIENIZADOS
    with st.expander("👀 Verificar Tabela de Dados Carregada", expanded=False):
        st.success(f"Planilha 'tabela comum' lida com sucesso! Total de linhas: {len(df)}")
        st.dataframe(df)

    # 2. FILTRO DE DATA NA SIDEBAR (BARRA LATERAL)
    st.sidebar.header("Filtros de Período")
    
    # Procura por uma coluna que contenha a palavra DATA
    colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
    
    if colunas_data:
        col_data = colunas_data[0]
        try:
            # Converte para o formato de data simples do Python para o seletor funcionar
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

    # 3. GRÁFICO DINÂMICO DE TENDÊNCIAS
    st.subheader("📈 Gráfico de Análise e Tendência")
    
    # Seleciona apenas as colunas que viraram números legítimos após a troca da vírgula
    colunas_numericas = df_filtrado.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    if len(colunas_numericas) >= 2:
        eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
        eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
        
        # Gera o gráfico de linhas conectando os pontos medidos
        fig = px.line(
            df_filtrado, 
            x=eixo_x, 
            y=eixo_y,
            title=f"Variação: {eixo_y} em relação a {eixo_x}",
            markers=True # Garante que os pontos fiquem visíveis como marcadores na tela do celular
        )
        
        # Ajustes visuais para o layout mobile do celular
        fig.update_traces(mode='markers+lines')
        fig.update_layout(hovermode="x unified", legend_orientation="h")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Nenhuma coluna numérica pura foi detectada após a conversão.")
        st.write("Colunas identificadas atualmente:", list(df.columns))
else:
    st.info("⚠️ Aguardando a sincronização dos dados com o repositório.")
