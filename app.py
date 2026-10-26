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
        # Carrega o arquivo Excel para checar as abas disponíveis
        excel_obj = pd.ExcelFile(EXCEL_FILE)
        abas = excel_obj.sheet_names
        
        df = None
        aba_selecionada = ""
        
        # Varre as abas para encontrar a que realmente tem dados cadastrados
        for aba in abas:
            temp_df = pd.read_excel(EXCEL_FILE, sheet_name=aba)
            # Remove linhas e colunas completamente vazias para checagem real
            temp_df = temp_df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            if not temp_df.empty and len(temp_df) > 0:
                df = temp_df
                aba_selecionada = aba
                break
        
        # Se nenhuma aba funcionou com cabeçalho padrão, tenta ler sem cabeçalho definido
        if df is None:
            for aba in abas:
                temp_df = pd.read_excel(EXCEL_FILE, sheet_name=aba, header=None)
                temp_df = temp_df.dropna(how='all', axis=0).dropna(how='all', axis=1)
                if not temp_df.empty:
                    # Usa a primeira linha válida como cabeçalho
                    nova_primeira_linha = temp_df.iloc[0]
                    df = temp_df[1:]
                    df.columns = nova_primeira_linha
                    aba_selecionada = aba
                    break

        if df is not None and not df.empty:
            # Limpa e padroniza os nomes das colunas em MAIÚSCULAS
            df.columns = df.columns.astype(str).str.strip().str.upper()
            
            # Remove colunas fantasmas geradas pelo Excel
            df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
            df = df.dropna(how='all', axis=0)
            
            # CONVERSÃO AUTOMÁTICA DE VÍRGULA PARA PONTO
            colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
            
            for col in df.columns:
                if not any(ignorar in col for ignorar in colunas_texto):
                    # Força a limpeza de texto e converte vírgula para ponto decimal
                    df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Garante a grafia correta da coluna A/S
            rename_dict = {}
            for col in df.columns:
                if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                    rename_dict[col] = "A/S (CM3/L)"
            df = df.rename(columns=rename_dict)

            # 1. EXPANDER PARA CONFERÊNCIA DA TABELA CARREGADA
            with st.expander("👀 Verificar Tabela de Dados Carregada", expanded=True):
                st.success(f"✅ Dados carregados com sucesso da aba: '{aba_selecionada}'! Total de registros: {len(df)}")
                st.dataframe(df)

            # 2. CONSTRUÇÃO DO GRÁFICO DINÂMICO
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
                st.warning("⚠️ Nenhuma coluna numérica pura foi detectada após a conversão automática.")
                st.write("Colunas identificadas atualmente no arquivo:", list(df.columns))
                st.write("Amostra dos dados brutos para análise:", df.head(3))
        else:
            st.error("❌ O arquivo Excel foi aberto com sucesso, mas o sistema não encontrou nenhuma linha contendo dados em nenhuma das abas. Verifique se os dados foram salvos corretamente.")
            
    except Exception as e:
        st.error(f"❌ Erro crítico na estruturação do Dashboard: {e}")
