import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Otimização de Processo - ETA Brasília")
st.markdown("### Análise Exclusiva: EQUILÍBRIO QUÍMICO COM CARGA")

# Nome exato do arquivo na raiz
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
else:
    try:
        # Carrega o Excel forçando a leitura SEM cabeçalho de texto para evitar erros de colunas duplicadas
        df_raw = pd.read_excel(EXCEL_FILE, sheet_name="EQUILIBRIO QUIMICO COM CARGA", header=None)
        
        # Remove linhas completamente vazias
        df_raw = df_raw.dropna(how='all', axis=0)
        
        # Tratamento: Usamos a primeira linha como guia de nomes, mas resolvemos as duplicatas imediatamente
        nomes_originais = df_raw.iloc[0].astype(str).str.strip().str.upper().tolist()
        
        colunas_unicas = []
        contagem = {}
        for nome in nomes_originais:
            if nome in contagem:
                contagem[nome] += 1
                colunas_unicas.append(f"{nome}_{contagem[nome]}")
            else:
                contagem[nome] = 1
                colunas_unicas.append(nome)
                
        # Define as colunas tratadas e remove a linha de títulos do corpo dos dados
        df = df_raw[1:].copy()
        df.columns = colunas_unicas
        
        # Limpa colunas fantasmas geradas pelo Excel (Unnamed)
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
        
        # Converte automaticamente todas as vírgulas decimais para ponto antes de processar
        for col in df.columns:
            if not any(x in col for x in ["DATA", "HORA", "TURNO", "OPERADOR", "OBS"]):
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Criação dinâmica de colunas chave para filtros caso venham com nomes levemente alterados
        col_data = next((c for c in df.columns if "DATA" in c), None)
        col_turb = next((c for c in df.columns if "TURB" in c or "TURBIDEZ" in c), None)
        col_vazao = next((c for c in df.columns if "VAZÃO" in c or "VAZAO" in c), None)

        # 🛠️ CONSTRUÇÃO DOS FILTROS NA BARRA LATERAL
        st.sidebar.header("🔍 Filtros de Pesquisa e Processo")
        
        # 1. Filtro por Data (Calendário)
        if col_data:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce').dt.date
            df = df.dropna(subset=[col_data])
            min_d, max_d = min(df[col_data]), max(df[col_data])
            datas_sel = st.sidebar.date_input("Intervalo de Datas:", [min_d, max_d])
            if isinstance(datas_sel, (list, tuple)) and len(datas_sel) == 2:
                df = df[(df[col_data] >= datas_sel[0]) & (df[col_data] <= datas_sel[1])]
        
        # 2. Filtro por Faixas de Turbidez (Água Bruta)
        if col_turb:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🌊 Faixas de Turbidez")
            max_t = float(df[col_turb].max()) if df[col_turb].max() > 0 else 100.0
            turb_min, turb_max = st.sidebar.slider("Selecione a faixa (UT):", 0.0, max_t, (0.0, max_t))
            df = df[(df[col_turb] >= turb_min) & (df[col_turb] <= turb_max)]
            
        # 3. Filtro por Composição de Elevatórias (Vazão Água Bruta)
        if col_vazao:
            st.sidebar.markdown("---")
            st.sidebar.subheader("⚡ Composição das Elevatórias")
            max_v = float(df[col_vazao].max()) if df[col_vazao].max() > 0 else 500.0
            vazao_min, vazao_max = st.sidebar.slider("Faixa de Vazão de Trabalho (L/s):", 0.0, max_v, (0.0, max_v))
            df = df[(df[col_vazao] >= vazao_min) & (df[col_vazao] <= vazao_max)]

        # Exibição segura dos dados tratados
        with st.expander("👀 Tabela de Dados Atual (Filtrada)", expanded=False):
            st.success(f"✅ {len(df)} registros carregados para análise!")
            st.dataframe(df)

        # 📊 RENDERIZAÇÃO DOS GRÁFICOS DE ANÁLISE E OTIMIZAÇÃO
        st.subheader("📉 Painel Gráfico de Otimização")
        
        colunas_numericas = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if len(colunas_numericas) >= 2:
            # Layout de abas para diferentes tipos de estratégias visuais no celular
            tab1, tab2, tab3 = st.tabs(["📈 Gráfico de Linhas (Tendência)", "📊 Gráfico de Colunas (Dosagens)", "🌌 Gráfico de Dispersão (Correlação)"])
            
            with tab1:
                st.markdown("**Análise Temporal/Sequencial das Variáveis**")
                param_y1 = st.selectbox("Selecione a Variável de Controle (Vertical):", colunas_numericas, index=0, key="y1")
                fig1 = px.line(df, x=col_data if col_data else df.index, y=param_y1, markers=True, title=f"Evolução de {param_y1} ao longo do tempo")
                st.plotly_chart(fig1, use_container_width=True)
                
            with tab2:
                st.markdown("**Análise de Distribuição e Faixas Operacionais**")
                param_y2 = st.selectbox("Selecione o Parâmetro de Dosagem/Vazão:", colunas_numericas, index=min(1, len(colunas_numericas)-1), key="y2")
                fig2 = px.bar(df, x=col_data if col_data else df.index, y=param_y2, title=f"Distribuição de Volume/Carga de {param_y2}")
                st.plotly_chart(fig2, use_container_width=True)
                
            with tab3:
                st.markdown("**Cruzamento de Variáveis para Otimização Química (ex: Alcalinidade vs Dosagem)**")
                eixo_x_disp = st.selectbox("Eixo X (Causa/Indicador):", colunas_numericas, index=0, key="x3")
                eixo_y_disp = st.selectbox("Eixo Y (Efeito/Resposta):", colunas_numericas, index=min(1, len(colunas_numericas)-1), key="y3")
                fig3 = px.scatter(df, x=eixo_x_disp, y=eixo_y_disp, trendline="ols", title=f"Correlação Direta: {eixo_y_disp} em função de {eixo_x_disp}")
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("⚠️ Dados carregados, mas não há colunas numéricas suficientes identificadas para montar os cruzamentos.")

    except Exception as e:
        st.error(f"❌ Erro na montagem da planilha de carga: {e}")
