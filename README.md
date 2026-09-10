# Mercado de ações brasileiras

Dashboard educacional em Python para consultar históricos de ações brasileiras
com yfinance, calcular indicadores com pandas e visualizar resultados no Streamlit.

## Instalação no WSL / Debian

Requer Python 3.10 ou superior, acesso à internet para instalar dependências e
consultar o Yahoo Finance, e o módulo `venv` disponível na instalação do Python.
Na pasta do projeto:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra o endereço local informado pelo Streamlit, normalmente `http://localhost:8501`.

## Como usar

- Digite uma ação, como `PETR4`, e clique em **Consultar**, ou use um dos atalhos
  em **Ações acompanhadas**. Os atalhos formam uma lista fixa, não um ranking da B3.
- O período inicial é um mês. Alterar o período consulta novamente a ação ativa.
  Um código que esteja sendo digitado só é consultado ao clicar em **Consultar**.
- Alterar a média móvel mantém o painel visível e recalcula o gráfico com os
  dados já consultados, sem nova chamada ao Yahoo Finance.
- A consulta é mantida durante a sessão. Consultas iguais são reutilizadas por
  até cinco minutos; clique em **Consultar** após esse prazo para buscar dados
  novos. Não há atualização automática. Recarregar a página pode encerrar a sessão.
- A identificação da ação, o período e o horário da consulta aparecem no painel.
  Se uma nova busca falhar, o último resultado bem-sucedido permanece identificado.

## Indicadores e dados incompletos

O painel apresenta preço do último registro, máximas e mínimas, fechamento médio,
variação no período, variação entre os dois últimos registros, volatilidade diária,
amplitude e indicadores de volume. Há gráficos de fechamento/média móvel e retornos,
além da tabela histórica.

- A média móvel de N pregões exige N fechamentos consecutivos válidos. Se não
  houver uma janela completa, o gráfico de preços continua e um aviso explica a
  indisponibilidade. Aumente o período ou diminua a janela.
- Retornos não preenchem nem atravessam registros com fechamento ausente.
  A série retornada por `calcular_retornos_diarios` preserva o índice e valores
  ausentes; use `.dropna()` quando precisar contar apenas retornos válidos.
- A volatilidade é o desvio-padrão amostral dos retornos percentuais, sem
  anualização, e exige pelo menos dois retornos válidos.
- Cada indicador trata sua própria falta de dados. Volume ausente, média de
  volume zero ou histórico curto não impedem os demais resultados.
- Preço e volume do último registro não são substituídos silenciosamente por
  valores de registros anteriores. A variação do período usa o primeiro e o
  último fechamento válidos e exige pelo menos dois valores.
- A média de volume inclui o último registro, mantendo a definição original.

Os registros mais recentes podem ser parciais durante um pregão e as cotações
podem ter atraso. O calendário e o ajuste de preços seguem o histórico fornecido
pelo yfinance; não há reconstrução de pregões inteiramente ausentes da resposta.
Os indicadores são informativos e não constituem recomendação de investimento.

## Organização

- `app.py`: interface, estado da sessão e cache das consultas.
- `services/market_data.py`: formatação do código e acesso ao Yahoo Finance.
- `utils/calculations.py`: cálculos independentes da interface.
- `tests/test_calculations.py`: regressões com lacunas, zeros e histórico curto.
- `tests/test_app.py`: interações com o AppTest oficial do Streamlit, usando dados
  simulados no lugar da consulta externa.

O cache permanece na interface para que o serviço de dados continue independente
do Streamlit. Não são necessários PostgreSQL, FastAPI, IA ou n8n nesta etapa.

## Verificação

```bash
python -m compileall -q app.py services utils tests
python -m unittest discover -s tests -v
```

Os testes não consultam a internet. Os testes da interface são sinalizados como
ignorados (`skipped`) se Streamlit ou yfinance não estiverem instalados; instale
`requirements.txt` para executá-los. As faixas de dependências limitam versões
principais, mas não representam um arquivo de versões exatas homologadas.

Na verificação manual, consulte uma ação, altere a média móvel e o período,
clique em outra ação acompanhada e tente uma consulta inválida. Confira a
identificação dos resultados e a preservação do painel.
