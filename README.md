# Painel Epidemiológico - CINEO 📊

Dashboard interativo desenvolvido para análise epidemiológica da associação entre a assistência pré-natal e a mortalidade neonatal precoce, utilizando dados unificados do SIM e SINASC (DATASUS). 

Projeto desenvolvido para apresentação no **CINEO**.

## 🎯 Objetivo
Substituir análises estáticas por uma solução exploratória, permitindo que profissionais de saúde e pesquisadores cruzem, em tempo real, variáveis como:
- Faixa de peso ao nascer.
- Quantidade de consultas pré-natais (adequado vs. inadequado).
- Risco de óbito precoce (TMNP e Odds Ratio).
- Cascata fisiopatológica de morte (Causas Múltiplas CID-10).

## 🛠️ Tecnologias Utilizadas
- **Python 3**
- **Streamlit:** Construção da interface web interativa.
- **Pandas & NumPy:** Limpeza, agrupamento e cálculos matriciais.
- **Plotly:** Visualizações de dados dinâmicas (Gráficos de barras empilhadas, linhas e Sunburst).
- **SciPy:** Validação estatística (Cálculo de Qui-Quadrado de Pearson e Odds Ratio com p-valor).

## 🚀 Como Acessar o Painel
O dashboard está hospedado na nuvem e pode ser acessado gratuitamente por qualquer navegador (celular ou computador) através do link abaixo:

🔗 **[Acessar o Painel Epidemiológico](COLE_AQUI_O_SEU_LINK_DO_STREAMLIT_CLOUD)**

## 💻 Como Rodar Localmente (Para Desenvolvedores)
Caso queira clonar o repositório e rodar o projeto na sua máquina:

1. Clone este repositório:
   ```bash
   git clone https://github.com/SEU_USUARIO/painel-cineo.git
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o servidor do Streamlit:
   ```bash
   streamlit run app.py
   ```
