import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo validado na raiz do repositório
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
else:
    try:
        # 1. Lê a planilha do Excel diretamente
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        
        # 2. Limpa e padroniza os nomes das colunas em MAIÚSCULAS
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        # Remove colunas e linhas fantasmas vazias
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
        df = df.dropna(how='all', axis=0)
        
        # 3. CONVERSÃO AUTOMÁTICA DE VÍRGULA PARA PONTO
        colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
        
        for col in df.columns:
            if not any(ignorar in col for ignorar in colunas_texto):
                # Limpa e converte para número decimal do Python
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Garante a grafia correta da coluna A/S
        rename_dict = {}
        for col in df.columns:
            if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                rename_dict[col] = "A/S (CM3/L)"
        df = df.rename(columns=rename_dict)

        # 4. EXPANDER PARA CONFERÊNCIA DA TABELA CARREGADA
        with st.expander("👀 Verificar Tabela de Dados Carregada", expanded=True):
            st.success(f"Planilha carregada com sucesso! Total de registros: {len(df)}")
            st.dataframe(df)

        # 5. FILTRO DE DATA ESTILO CALENDÁRIO (Evita travamentos no celular)
        st.sidebar.header("Filtros de Período")
        colunas_data = [c for c in df.columns if "DATA" in c or "DATE" in c]
        
        if colunas_data:
            col_data = colunas_data[0] # Pega a primeira coluna de data identificada
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce').dt.date
            df = df.dropna(subset=[col_data]) # Remove linhas onde a data é inválida
            
            min_data = min(df[col_data])
            max_data = max(df[col_data])
            
            # Seletor simples em formato de calendário para o celular
            periodo = st.sidebar.date_input("Selecione o intervalo de datas:", [min_data, max_data])
            
            if isinstance(periodo, list) or isinstance(periodo, tuple):
                if len(periodo) == 2:
                    df_filtrado = df[(df[col_data] >= periodo[0]) & (df[col_data] <= periodo[1])]
                else:
                    df_filtrado = df
            else:
                df_filtrado = df[df[col_data] == periodo]
        else:
            df_filtrado = df

        # 6. GRÁFICO DINÂMICO DE TENDÊNCIAS
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
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Nenhuma coluna numérica pura foi detectada após a conversão automática.")
            st.write("Colunas identificadas atualmente no arquivo:", list(df.columns))

    except Exception as e:
        st.error(f"❌ Erro crítico na estruturação do Dashboard: {e}")
