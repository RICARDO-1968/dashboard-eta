import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo validado na raiz do repositório
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

def load_data_direct():
    # Verifica a existência física do arquivo no servidor
    if not os.path.exists(EXCEL_FILE):
        st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
        arquivos_raiz = os.listdir(".")
        st.write("Arquivos atualmente detectados na raiz:", arquivos_raiz)
        return None
        
    try:
        # Lê a planilha forçando o formato de tabela comum
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        
        if df.empty:
            st.warning("⚠️ O arquivo Excel foi aberto, mas parece não conter nenhuma linha de dados.")
            return None

        # Limpa espaços e força colunas em MAIÚSCULO
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # Elimina colunas fantasmas geradas pelo Excel (Unnamed)
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
        df = df.dropna(how='all', axis=0)
        
        # CONVERSÃO AUTOMÁTICA DE VÍRGULA PARA PONTO
        colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
        
        for col in df.columns:
            if not any(ignorar in col for ignorar in colunas_texto):
                # Troca a vírgula pelo ponto e remove espaços das células numéricas
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Garante a grafia unificada da coluna A/S
        rename_dict = {}
        for col in df.columns:
            if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                rename_dict[col] = "A/S (CM3/L)"
        df = df.rename(columns=rename_dict)
        
        return df
    except Exception as e:
        st.error(f"❌ Erro crítico ao processar o arquivo Excel: {e}")
        return None

# Carrega os dados diretamente, sem passar pela memória cache travada
df = load_data_direct()

if df is not None and not df.empty:
    # 1. EXPANDER PARA CONFERÊNCIA DOS DADOS HIGIENIZADOS
    with st.expander("👀 Verificar Tabela de Dados Carregada", expanded=True):
        st.success(f"Planilha lida com sucesso! Total de registros encontrados: {len(df)}")
        st.dataframe(df)

    # 2. FILTRO DE DATA NA SIDEBAR
    st.sidebar.header("Filtros de Período")
    colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
    
    if colunas_data:
        col_data = colunas_data[0] # Pega a primeira coluna de data encontrada
        try:
            df[col_data] = pd.to_datetime(df[col_data]).dt.date
            datas = sorted(df[col_data].unique())
            
            if len(datas) > 1:
                data_sel = st.sidebar.select_slider("Selecione o período:", options=datas, value=(datas[0], datas[-1]))
                df_filtrado = df[(df[col_data] >= data_sel[0]) & (df[col_data] <= data_sel[1])]
            else:
                df_filtrado = df
        except Exception as e:
            st.sidebar.warning(f"Não foi possível aplicar o seletor de data: {e}")
            df_filtrado = df
    else:
        df_filtrado = df

    # 3. GRÁFICO DINÂMICO DE TENDÊNCIAS
    st.subheader("📈 Gráfico de Análise e Tendência")
    colunas_numericas = df_filtrado.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    if len(colunas_numericas) >= 2:
        eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
        eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
        
        fig = px.line(
            df_filtrado, 
            x=eixo_x, 
            y=eixo_y,
            title=f"Variação: {eixo_y} em relação a {eixo_x}",
            markers=True
        )
        
        fig.update_traces(mode='markers+lines')
        fig.update_layout(hovermode="x unified", legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Nenhuma coluna numérica pura foi detectada após a conversão automática.")
        st.write("Colunas identificadas atualmente no arquivo:", list(df.columns))
else:
    st.info("⚠️ Aguardando a leitura inicial das linhas do repositório.")
