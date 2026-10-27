import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")

# Nome exato do arquivo validado (sem acento) na raiz do repositório
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub. Verifique se o nome está idêntico.")
else:
    try:
        # Abre o arquivo Excel para ler a estrutura de abas
        excel_obj = pd.ExcelFile(EXCEL_FILE)
        abas_disponiveis = excel_obj.sheet_names
        
        # Cria uma lista apenas com as abas de foco que você definiu
        abas_foco = ["EQUILIBRIO QUIMICO", "EQUILIBRIO QUIMICO COM CARGA"]
        # Filtra para usar apenas as que realmente existem com o nome exato digitado
        abas_validas = [aba for aba in abas_disponiveis if aba.strip().upper() in abas_foco or aba.strip() in abas_foco]
        
        if not abas_validas:
            st.error("⚠️ As abas específicas não foram encontradas com os nomes exatos.")
            st.write("Abas reais detectadas dentro do seu Excel:", abas_disponiveis)
            df = None
        else:
            # Seletor visual no topo para você alternar entre as duas planilhas pelo celular
            aba_selecionada = st.radio(
                "📂 Selecione a Planilha de Análise:",
                options=abas_validas,
                horizontal=True
            )
            
            # Carrega a planilha escolhida pelo usuário
            df = pd.read_excel(EXCEL_FILE, sheet_name=aba_selecionada)

        if df is not None and not df.empty:
            # Limpa espaços invisíveis e força nomes de colunas em MAIÚSCULAS
            df.columns = df.columns.astype(str).str.strip().str.upper()
            
            # Limpa linhas vazias e colunas fantasmas geradas pelo Excel (Unnamed)
            df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
            df = df.dropna(how='all', axis=0)
            
            # TRATAMENTO E CONVERSÃO DE VÍRGULA PARA PONTO DECIMAL
            colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES"]
            
            for col in df.columns:
                if not any(ignorar in col for ignorar in colunas_texto):
                    # Limpa espaços internos, troca a vírgula pelo ponto e converte em número decimal
                    df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                    df[col] = df[col].str.replace(',', '.', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Padroniza a grafia da coluna A/S (Relação Ar/Sólido)
            rename_dict = {}
            for col in df.columns:
                if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                    rename_dict[col] = "A/S (CM3/L)"
            df = df.rename(columns=rename_dict)

            # 1. VISUALIZADOR DA TABELA DE DADOS CARREGADA
            with st.expander(f"👀 Visualizar Tabela - {aba_selecionada}", expanded=True):
                st.success(f"✅ {len(df)} registros carregados e tratados com sucesso!")
                st.dataframe(df)

            # 2. CONSTRUÇÃO DO GRÁFICO DINÂMICO DE TENDÊNCIAS
            st.subheader("📈 Gráfico de Análise e Tendência")
            
            # Filtra apenas colunas que possuem dados numéricos reais após o tratamento das vírgulas
            colunas_numericas = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            
            if len(colunas_numericas) >= 2:
                eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
                eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
                
                # Desenha o gráfico de dispersão com linha de tendência e marcadores bem visíveis no celular
                fig = px.line(
                    df, 
                    x=eixo_x, 
                    y=eixo_y,
                    title=f"Variação de {eixo_y} em função de {eixo_x} ({aba_selecionada})",
                    markers=True
                )
                
                fig.update_traces(mode='markers+lines')
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Nenhuma coluna numérica pura foi detectada para plotagem gráfica.")
                st.write("Colunas identificadas atualmente na aba:", list(df.columns))
                
        elif df is not None:
            st.error(f"❌ A aba '{aba_selecionada}' foi aberta, mas ela não contém dados preenchidos nas linhas.")
            
    except Exception as e:
        st.error(f"❌ Erro crítico ao abrir a estrutura do arquivo: {e}")
