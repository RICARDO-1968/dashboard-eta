import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página do Streamlit
st.set_page_config(page_title="Dashboard ETA Brasília", layout="wide")

st.title("📊 Dashboard ETA Brasília - Equilíbrio Químico")
st.markdown("### Análise Comparativa: COM CARGA vs SEM CARGA")

# Nome exato do arquivo validado na raiz do repositório
EXCEL_FILE = "EQUILIBRIO QUIMICO.xlsx"

if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ O arquivo '{EXCEL_FILE}' não foi encontrado na raiz do GitHub.")
else:
    try:
        # Abre o arquivo Excel para ler a estrutura de abas
        excel_obj = pd.ExcelFile(EXCEL_FILE)
        abas_disponiveis = excel_obj.sheet_names
        
        dfs_para_juntar = []
        
        # Mapeamento das duas abas oficiais
        mapeamento_abas = {
            "EQUILIBRIO QUIMICO": "SEM CARGA",
            "EQUILIBRIO QUIMICO COM CARGA": "COM CARGA"
        }
        
        for nome_aba, status in mapeamento_abas.items():
            # Verifica se a aba existe (tratando espaços e maiúsculas)
            aba_real = next((aba for aba in abas_disponiveis if aba.strip().upper() == nome_aba), None)
            
            if aba_real:
                df_aba = pd.read_excel(EXCEL_FILE, sheet_name=aba_real)
                
                if not df_aba.empty:
                    # 1. Padroniza nomes das colunas iniciais da aba
                    df_aba.columns = df_aba.columns.astype(str).str.strip().str.upper()
                    df_aba = df_aba.loc[:, ~df_aba.columns.str.contains('^UNNAMED')]
                    df_aba = df_aba.dropna(how='all', axis=0)
                    
                    # 2. 🔄 RESOLUÇÃO DE COLUNAS DUPLICADAS DENTRO DA PRÓPRIA ABA (Antes de juntar)
                    colunas_ajustadas = []
                    contagem_colunas = {}
                    for col in df_aba.columns:
                        if col in contagem_colunas:
                            contagem_colunas[col] += 1
                            colunas_ajustadas.append(f"{col}_{contagem_colunas[col]}")
                        else:
                            contagem_colunas[col] = 1
                            colunas_ajustadas.append(col)
                    df_aba.columns = colunas_ajustadas
                    
                    # Carimba o status para podermos diferenciar no gráfico
                    df_aba["STATUS_OPERACAO"] = status
                    dfs_para_juntar.append(df_aba)
        
        if not dfs_para_juntar:
            st.error("⚠️ Nenhuma das duas abas específicas foi encontrada ou elas estão vazias.")
            df_consolidado = None
        else:
            # 3. Agora a junção é segura porque nenhuma aba possui colunas duplicadas internamente
            df_consolidado = pd.concat(dfs_para_juntar, ignore_index=True, sort=False)

        if df_consolidado is not None and not df_consolidado.empty:
            # TRATAMENTO E CONVERSÃO DE VÍRGULA PARA PONTO DECIMAL
            colunas_texto = ["DATA", "HORA", "TURNO", "OPERADOR", "OBS", "OBSERVAÇÃO", "OBSERVAÇÕES", "STATUS_OPERACAO"]
            
            for col in df_consolidado.columns:
                if not any(ignorar in col for ignorar in colunas_texto):
                    df_consolidado[col] = df_consolidado[col].astype(str).str.replace(' ', '', regex=False)
                    df_consolidado[col] = df_consolidado[col].str.replace(',', '.', regex=False)
                    df_consolidado[col] = pd.to_numeric(df_consolidado[col], errors='coerce')
            
            # Padroniza a grafia da coluna Ar/Sólido (A/S)
            rename_dict = {}
            for col in df_consolidado.columns:
                if "A/S" in col or "RELAÇÃO" in col or "A / S" in col:
                    sufixo = col.split('_')[-1] if '_' in col else ""
                    nome_base = "A/S (CM3/L)"
                    rename_dict[col] = f"{nome_base}_{sufixo}" if sufixo.isdigit() else nome_base
            df_consolidado = df_consolidado.rename(columns=rename_dict)

            # 1. VISUALIZADOR DA TABELA CONSOLIDADA COLETIVA
            with st.expander("👀 Visualizar Banco de Dados Unificado (Memória)", expanded=True):
                st.success(f"✅ Dados integrados automaticamente! Total de registros combinados: {len(df_consolidado)}")
                st.dataframe(df_consolidado)

            # 2. CONSTRUÇÃO DO GRÁFICO DINÂMICO DE COMPARAÇÃO SIMULTÂNEA
            st.subheader("📈 Gráfico de Análise e Tendência")
            
            # Identifica as colunas numéricas disponíveis para plotagem
            colunas_numericas = df_consolidado.select_dtypes(include=['float64', 'int64']).columns.tolist()
            
            if len(colunas_numericas) >= 2:
                eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
                eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
                
                # O segredo do comparativo simultâneo está no parâmetro 'color'
                fig = px.line(
                    df_consolidado.sort_values(by=[eixo_x]), 
                    x=eixo_x, 
                    y=eixo_y,
                    color="STATUS_OPERACAO",
                    title=f"Variação de {eixo_y} em relação a {eixo_x}",
                    markers=True,
                    color_discrete_map={"SEM CARGA": "#1f77b4", "COM CARGA": "#d62728"} # Azul vs Vermelho
                )
                
                fig.update_traces(mode='markers+lines')
                fig.update_layout(hovermode="x unified", legend_title_text="Operação da ETA")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Nenhuma coluna numérica pura foi encontrada após a consolidação das planilhas.")
                st.write("Colunas identificadas:", list(df_consolidado.columns))
                
    except Exception as e:
        st.error(f"❌ Erro crítico na consolidação das planilhas: {e}")
