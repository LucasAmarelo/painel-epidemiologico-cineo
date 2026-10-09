import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import chi2_contingency
import math

# ==========================================
# 1. Configuração da Página
# ==========================================
st.set_page_config(page_title="Painel Epidemiológico - CINEO", layout="wide")

# ==========================================
# 2. Carregamento e Preparação dos Dados
# ==========================================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("BASE_MESTRE_POWERBI_2021_2025.csv", sep=';', low_memory=False)
    
    df['OBITO_PRECOCE'] = pd.to_numeric(df['OBITO_PRECOCE'], errors='coerce').fillna(0).astype(int)
    df['PESO'] = pd.to_numeric(df['PESO'], errors='coerce')
    
    condicoes_peso = [
        (df['PESO'] < 1000),
        (df['PESO'] >= 1000) & (df['PESO'] < 1500),
        (df['PESO'] >= 1500) & (df['PESO'] < 2500),
        (df['PESO'] >= 2500)
    ]
    valores_peso = [
        "1. Extremo Baixo Peso (< 1000g)", 
        "2. Muito Baixo Peso (1000-1499g)", 
        "3. Baixo Peso (1500-2499g)", 
        "4. Peso Adequado (>= 2500g)"
    ]
    df['Faixa_Peso'] = np.select(condicoes_peso, valores_peso, default="Não Informado")
    
    df['Status_PreNatal'] = np.where(
        df['CONSULTAS'].isin([1, 2]), "Inadequado (0 a 3)",
        np.where(df['CONSULTAS'].isin([3, 4]), "Adequado (>= 4)", "Ignorado")
    )
    return df

df_mestre = carregar_dados()

# ==========================================
# 3. BARRA LATERAL (Filtros)
# ==========================================
st.sidebar.title("Filtros Epidemiológicos")
lista_anos = ["Todos os Anos"] + sorted(df_mestre['ANO_NASCIMENTO'].dropna().astype(str).unique().tolist())
ano_selecionado = st.sidebar.selectbox("Ano de Nascimento:", lista_anos)

lista_pesos = ["Todas as Faixas"] + sorted(df_mestre['Faixa_Peso'].unique().tolist())
lista_pesos.remove("Não Informado") if "Não Informado" in lista_pesos else None
peso_selecionado = st.sidebar.selectbox("Faixa de Peso:", lista_pesos)

# Filtro Principal
df_filtrado = df_mestre.copy()
if ano_selecionado != "Todos os Anos":
    df_filtrado = df_filtrado[df_filtrado['ANO_NASCIMENTO'].astype(str) == ano_selecionado]
if peso_selecionado != "Todas as Faixas":
    df_filtrado = df_filtrado[df_filtrado['Faixa_Peso'] == peso_selecionado]

# ==========================================
# 4. CABEÇALHO (Cartões de KPI e Matriz)
# ==========================================
st.title("Associação entre Assistência Pré-Natal e Mortalidade Neonatal Precoce (2021-2025)")
st.markdown("---")

total_nascidos = len(df_filtrado)
total_obitos = df_filtrado['OBITO_PRECOCE'].sum()
tmnp = (total_obitos / total_nascidos * 1000) if total_nascidos > 0 else 0

df_validos_prenatal = df_filtrado[df_filtrado['Status_PreNatal'].isin(["Inadequado (0 a 3)", "Adequado (>= 4)"])]
pct_inadequado = (len(df_validos_prenatal[df_validos_prenatal['Status_PreNatal'] == "Inadequado (0 a 3)"]) / len(df_validos_prenatal)) * 100 if len(df_validos_prenatal) > 0 else 0

df_stat = df_validos_prenatal
a = len(df_stat[(df_stat['Status_PreNatal'] == "Inadequado (0 a 3)") & (df_stat['OBITO_PRECOCE'] == 1)])
b = len(df_stat[(df_stat['Status_PreNatal'] == "Inadequado (0 a 3)") & (df_stat['OBITO_PRECOCE'] == 0)])
c = len(df_stat[(df_stat['Status_PreNatal'] == "Adequado (>= 4)") & (df_stat['OBITO_PRECOCE'] == 1)])
d = len(df_stat[(df_stat['Status_PreNatal'] == "Adequado (>= 4)") & (df_stat['OBITO_PRECOCE'] == 0)])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Nascidos Vivos", f"{total_nascidos:,}".replace(',', '.'))
    st.metric("Total de Óbitos Precoces", f"{total_obitos:,}".replace(',', '.'))
with col2:
    st.metric("TMNP (por mil)", f"{tmnp:.1f}")
with col3:
    st.metric("Proporção de Pré-Natal Inadequado", f"{pct_inadequado:.1f}%")
    st.caption("Baseado apenas em registros válidos.")
with col4:
    if b * c != 0 and a > 0:
        or_val = (a * d) / (b * c)
        se = math.sqrt((1/a) + (1/b) + (1/c) + (1/d))
        ln_or = math.log(or_val, 2.71)
        lower = pow(2.71, ln_or - 1.96 * se)
        upper = pow(2.71, ln_or + 1.96 * se)
        chi2, p_val, _, _ = chi2_contingency([[a, b], [c, d]])
        
        st.metric("Odds Ratio (Risco de Óbito)", f"{or_val:.1f}x")
        st.caption(f"**IC 95%:** {lower:.1f} a {upper:.1f} | **p-valor:** {p_val:.4f}")
    else:
        st.metric("Odds Ratio", "Dados Insuficientes")

with st.expander("📊 Ver Matriz de Contingência (Dados absolutos utilizados no modelo)"):
    df_matriz = pd.DataFrame({
        "Óbito Precoce (Casos)": [a, c, a+c],
        "Sobrevida (Casos)": [b, d, b+d],
        "Total": [a+b, c+d, a+b+c+d]
    }, index=["Inadequado (0 a 3)", "Adequado (>= 4)", "Total"])
    st.dataframe(df_matriz, use_container_width=True)

st.markdown("---")

# ==========================================
# 5. BLOCO: Evolução Temporal (2021-2025)
# ==========================================
st.subheader("Evolução Histórica (2021-2025)")
st.caption("Tendência da Taxa de Mortalidade cruzada com a evolução da proporção de pré-natal inadequado.")

df_tendencia = df_mestre.copy()
if peso_selecionado != "Todas as Faixas":
    df_tendencia = df_tendencia[df_tendencia['Faixa_Peso'] == peso_selecionado]

df_ano = df_tendencia.groupby('ANO_NASCIMENTO').agg(Nascimentos=('OBITO_PRECOCE', 'count'), Obitos=('OBITO_PRECOCE', 'sum')).reset_index()
df_ano['TMNP'] = (df_ano['Obitos'] / df_ano['Nascimentos']) * 1000

df_pre = df_tendencia[df_tendencia['Status_PreNatal'].isin(["Inadequado (0 a 3)", "Adequado (>= 4)"])]
df_pre_grp = df_pre.groupby(['ANO_NASCIMENTO', 'Status_PreNatal']).size().unstack(fill_value=0).reset_index()
df_pre_grp['Pct_Inadequado'] = (df_pre_grp['Inadequado (0 a 3)'] / (df_pre_grp['Inadequado (0 a 3)'] + df_pre_grp['Adequado (>= 4)'])) * 100

df_hist = pd.merge(df_ano, df_pre_grp[['ANO_NASCIMENTO', 'Pct_Inadequado']], on='ANO_NASCIMENTO', how='left')

fig_hist = go.Figure()
fig_hist.add_trace(go.Bar(x=df_hist['ANO_NASCIMENTO'].astype(str), y=df_hist['Pct_Inadequado'], name='% Inadequado', marker_color='#F4C145', opacity=0.8))
fig_hist.add_trace(go.Scatter(x=df_hist['ANO_NASCIMENTO'].astype(str), y=df_hist['TMNP'], name='TMNP', yaxis='y2', mode='lines+markers', line=dict(color='red', width=3)))

fig_hist.update_layout(
    yaxis=dict(title='% Inadequado'),
    yaxis2=dict(title='TMNP (por mil)', overlaying='y', side='right'),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
    legend_title_text="",
    margin=dict(l=10, r=10, t=60, b=10)
)
st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
st.markdown("---")

# ==========================================
# 6. BLOCO CENTRAL 1: O Paradoxo
# ==========================================
st.subheader("O Paradoxo da Sobrevida e Cobertura Pré-Natal")
st.caption("Volume de nascimentos segmentado por qualidade do pré-natal, cruzado com o risco de mortalidade.")

df_tmnp = df_filtrado[df_filtrado['Faixa_Peso'] != "Não Informado"].groupby('Faixa_Peso').agg(Nascimentos=('OBITO_PRECOCE', 'count'), Obitos=('OBITO_PRECOCE', 'sum')).reset_index()
df_tmnp['TMNP'] = (df_tmnp['Obitos'] / df_tmnp['Nascimentos']) * 1000
df_peso_prenatal = df_filtrado[df_filtrado['Faixa_Peso'] != "Não Informado"].groupby(['Faixa_Peso', 'Status_PreNatal']).size().reset_index(name='Contagem')

fig1 = go.Figure()
cores_prenatal = {"Adequado (>= 4)": "#4C78A8", "Inadequado (0 a 3)": "#E45756", "Ignorado": "#B0B0B0"}

for status in ["Adequado (>= 4)", "Inadequado (0 a 3)", "Ignorado"]:
    df_temp = df_peso_prenatal[df_peso_prenatal['Status_PreNatal'] == status]
    fig1.add_trace(go.Bar(x=df_temp['Faixa_Peso'], y=df_temp['Contagem'], name=status, marker_color=cores_prenatal[status]))

fig1.add_trace(go.Scatter(x=df_tmnp['Faixa_Peso'], y=df_tmnp['TMNP'], name='TMNP (Risco)', yaxis='y2', mode='lines+markers', line=dict(color='red', width=3)))

fig1.update_layout(
    barmode='stack',
    yaxis=dict(title='Volume'),
    yaxis2=dict(title='TMNP', overlaying='y', side='right'),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
    legend_title_text="",
    margin=dict(l=10, r=10, t=60, b=10)
)
st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
st.markdown("---")

# ==========================================
# 7. BLOCO CENTRAL 2: Contraste de Desfecho
# ==========================================
col_obitos, col_vivos = st.columns(2)

def plotar_barras_percentuais(df_filtrado_alvo, y_title=""):
    df_base = df_filtrado_alvo[(df_filtrado_alvo['Faixa_Peso'] != "Não Informado") & (df_filtrado_alvo['Status_PreNatal'] != "Ignorado")]
    agrupado = df_base.groupby(['Faixa_Peso', 'Status_PreNatal']).size().reset_index(name='Contagem')
    totais_por_peso = agrupado.groupby('Faixa_Peso')['Contagem'].transform('sum')
    agrupado['Percentual'] = (agrupado['Contagem'] / totais_por_peso) * 100
    
    fig = px.bar(agrupado, x='Faixa_Peso', y='Percentual', color='Status_PreNatal', 
                 color_discrete_map={"Inadequado (0 a 3)": "#E45756", "Adequado (>= 4)": "#4C78A8"})
                 
    fig.update_layout(
        yaxis_title=y_title, 
        xaxis_title="", 
        yaxis=dict(range=[0, 100]),
        uniformtext_minsize=12,
        uniformtext_mode='show',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        legend_title_text="",
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    fig.update_traces(
        texttemplate='%{y:.1f}', 
        textposition='inside', 
        insidetextanchor='middle',
        textfont_color='white',
        textangle=0, 
        constraintext='none' 
    )
    return fig

with col_obitos:
    st.markdown("<h5 style='text-align: center;'>Vítimas Fatais (Óbitos)</h5>", unsafe_allow_html=True)
    fig_obitos = plotar_barras_percentuais(df_filtrado[df_filtrado['OBITO_PRECOCE'] == 1], "% de Casos")
    st.plotly_chart(fig_obitos, use_container_width=True, config={'displayModeBar': False})

with col_vivos:
    st.markdown("<h5 style='text-align: center;'>Sobreviventes (Vivos)</h5>", unsafe_allow_html=True)
    fig_vivos = plotar_barras_percentuais(df_filtrado[df_filtrado['OBITO_PRECOCE'] == 0], "")
    st.plotly_chart(fig_vivos, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")

# ==========================================
# 8. BLOCO INFERIOR 1: Top 10 Causas Básicas
# ==========================================
st.subheader("Principais Causas de Mortalidade Neonatal")
st.caption("As 10 Causas Básicas (CID-10) mais frequentes nos óbitos registrados.")

# Dicionário interno para as causas neonatais mais comuns
dicionario_cid = {
    "P369": "Sepse bacteriana do recém-nascido, não especificada",
    "P220": "Síndrome do desconforto respiratório do recém-nascido",
    "P072": "Imaturidade extrema",
    "P219": "Asfixia ao nascer, não especificada",
    "P229": "Desconforto respiratório do recém-nascido, não especificado",
    "P209": "Hipóxia intra-uterina não especificada",
    "P073": "Outros recém-nascidos pré-termo",
    "P290": "Insuficiência cardíaca neonatal",
    "P77" : "Enterocolite necrotizante do feto e do recém-nascido",
    "P524": "Hemorragia ventricular do recém-nascido",
    "P368": "Outras sepses bacterianas do recém-nascido",
    "P362": "Sepse do recém-nascido devida a Staphylococcus aureus",
    "P240": "Aspiração neonatal de mecônio",
    "Q249": "Malformação congênita do coração, não especificada",
    "A500": "Sífilis congênita precoce sintomática",
    "A509": "Sífilis congênita, não especificada",
    "P012": "Feto/RN afetado por oligoidrâmnio",
    "P285": "Falência respiratória do recém-nascido"
}

df_cid = df_filtrado[(df_filtrado['OBITO_PRECOCE'] == 1) & (df_filtrado['CAUSABAS'].notna())].copy()
df_cid['CAUSABAS'] = df_cid['CAUSABAS'].fillna('Não Informada')

# Agrupa, conta e pega os 10 maiores
top10_causas = df_cid['CAUSABAS'].value_counts().reset_index().head(10)
top10_causas.columns = ['Causa Básica', 'Óbitos']


