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
            aba_real = next((aba for aba in abas_disponiveis if aba.strip().upper() == nome_aba), None)
            
            if aba_real:
                df_aba = pd.read_excel(EXCEL_FILE, sheet_name=aba_real, header=0)
                
                if not df_aba.empty:
                    df_aba = df_aba.reset_index(drop=True)
                    df_aba.columns = df_aba.columns.astype(str).str.strip().str.upper()
                    df_aba = df_aba.loc[:, ~df_aba.columns.str.contains('^UNNAMED')]
                    
                    # 🔄 CORREÇÃO AGRESSIVA: Renomeia colunas repetidas ANTES de juntar
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
                    
                    # Carimba o status para diferenciar no gráfico simultâneo
                    df_aba["STATUS_OPERACAO"] = status
                    dfs_para_juntar.append(df_aba)
        
        if not dfs_para_juntar:
            st.error("⚠️ Nenhuma das duas abas específicas foi encontrada ou elas estão vazias.")
            df_consolidado = None
        else:
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

            # 🛠️ RETORNO DOS FILTROS NA SIDEBAR
            st.sidebar.header("🔍 Filtros de Pesquisa")
            
            # Identifica a primeira coluna de data disponível (geralmente DATA ou DATA_1)
            colunas_data = [c for c in df_consolidado.columns if "DATA" in c]
            
            if colunas_data:
                col_data_principal = colunas_data[0]
                # Converte para data válida do Python
                df_consolidado[col_data_principal] = pd.to_datetime(df_consolidado[col_data_principal], errors='coerce').dt.date
                df_consolidado = df_consolidado.dropna(subset=[col_data_principal])
                
                min_data = min(df_consolidado[col_data_principal])
                max_data = max(df_consolidado[col_data_principal])
                
                # Seletor de Calendário prático para o celular
                periodo_selecionado = st.sidebar.date_input(
                    "Selecione o intervalo de datas:", 
                    [min_data, max_data],
                    min_value=min_data,
                    max_value=max_data
                )
                
                # Aplica o filtro de data se o usuário selecionou o início e o fim
                if isinstance(periodo_selecionado, list) or isinstance(periodo_selecionado, tuple):
                    if len(periodo_selecionado) == 2:
                        df_filtrado = df_consolidado[
                            (df_consolidado[col_data_principal] >= periodo_selecionado[0]) & 
                            (df_consolidado[col_data_principal] <= periodo_selecionado[1])
                        ]
                    else:
                        df_filtrado = df_consolidado
                else:
                    df_filtrado = df_consolidado[df_consolidado[col_data_principal] == periodo_selecionado]
            else:
                df_filtrado = df_consolidado

            # Filtro adicional por Turno (caso exista a coluna TURNO na planilha)
            colunas_turno = [c for c in df_filtrado.columns if "TURNO" in c]
            if colunas_turno:
                col_turno_principal = colunas_turno[0]
                turnos_disponiveis = ["TODOS"] + list(df_filtrado[col_turno_principal].dropna().unique())
                turno_sel = st.sidebar.selectbox("Filtrar por Turno:", turnos_disponiveis)
                if turno_sel != "TODOS":
                    df_filtrado = df_filtrado[df_filtrado[col_turno_principal] == turno_sel]

            # 1. VISUALIZADOR DA TABELA CONSOLIDADA (AGORA GARANTIDA SEM TRAVAMENTOS)
            with st.expander("👀 Visualizar Banco de Dados Unificado (Memória)", expanded=False):
                st.success(f"✅ Dados integrados automaticamente! Total de registros exibidos: {len(df_filtrado)}")
                st.dataframe(df_filtrado)

            # 2. CONSTRUÇÃO DO GRÁFICO DINÂMICO DE COMPARAÇÃO SIMULTÂNEA
            st.subheader("📈 Gráfico de Análise e Tendência")
            
            # Filtra apenas colunas numéricas que contêm valores válidos após a limpeza
            colunas_numericas = df_filtrado.select_dtypes(include=['float64', 'int64']).columns.tolist()
            
            # Adiciona a coluna de data nas opções do eixo X para fazer análise temporal
            if colunas_data and col_data_principal not in colunas_numericas:
                colunas_numericas.insert(0, col_data_principal)

            if len(colunas_numericas) >= 2:
                eixo_x = st.selectbox("Escolha o parâmetro do Eixo X (Horizontal):", colunas_numericas, index=0)
                eixo_y = st.selectbox("Escolha o parâmetro do Eixo Y (Vertical):", colunas_numericas, index=min(1, len(colunas_numericas)-1))
                
                # Gera o gráfico criando linhas separadas por cores baseado no STATUS (Com vs Sem Carga)
                fig = px.line(
                    df_filtrado.sort_values(by=[eixo_x]), 
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
                st.warning("⚠️ Nenhuma coluna numérica pura foi encontrada após a consolidação para gerar o gráfico.")
                st.write("Colunas identificadas:", list(df_filtrado.columns))
                
    except Exception as e:
        st.error(f"❌ Erro crítico na visualização do Dashboard: {e}")
