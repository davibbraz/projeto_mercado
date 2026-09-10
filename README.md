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
- **Atualizar ações** carrega os cartões de PETR4, VALE3, BBAS3 e MGLU3 sem
  trocar a ação em análise. O atalho de ITUB4 continua disponível no menu lateral.
  Os cartões começam vazios até uma consulta; nenhum valor do desenho é usado
  como cotação. Falhas individuais preservam o cartão anterior e sua data.
- A tabela de movimentos considera somente ações carregadas na sessão,
  agrupadas pela data do último registro. Dentro da data selecionada, ordena
  pela magnitude da variação entre os dois últimos registros. Não é um ranking
  de toda a bolsa e as buscas podem ter ocorrido em horários diferentes.
- O menu leva às seções da página; histórico, retornos e indicadores adicionais
  ficam disponíveis abaixo do painel principal.

## Interface do Figma

Referência: [Dashboard Mercado Financeiro, frame Main shell 2:15](https://www.figma.com/design/LYAg3aIvLlDgpJKlTVXu8f/Dashboard-Mercado-Financeiro?node-id=2-15).

O layout usa fundo escuro, superfícies arredondadas, azul de destaque, cartões
de ações com minigráficos, gráfico principal e indicadores lado a lado. As
colunas se reorganizam em telas menores e a tabela permite rolagem horizontal.
O CSS fica separado em `ui/styles.css`; a configuração nativa de cores fica
em `.streamlit/config.toml`. Execute o Streamlit na raiz para carregar o tema.

Adaptações ao escopo atual:

- Os quatro cartões superiores mostram preço, variação, máxima e mínima da
  ação selecionada. Ibovespa, dólar, IFIX e bitcoin do desenho ainda não têm
  fontes integradas no projeto e não foram preenchidos com valores fictícios.
- Índices, favoritos e comparador aparecem como **Em breve**, sem botões que
  aparentem executar uma função inexistente. RSI e a interpretação de tendência
  do desenho não foram implementados; os indicadores existentes foram mantidos.
- Os períodos continuam sendo históricos diários de 5D a 5A, com padrão 1M.
  O botão 1D intradiário do desenho não foi adicionado: isso exigiria mudar a
  consulta e a interpretação dos indicadores.
- Gráficos são gerados a partir dos dados consultados, substituindo as curvas
  ilustrativas do Figma. Valores ausentes interrompem as linhas.

Não há novas dependências. A validação automatizada cobre 25 testes com dados
simulados, incluindo atualização parcial dos cartões, cache, consulta ativa e
separação dos movimentos por data. A inspeção visual em desktop e celular deve
ser feita no ambiente local; o navegador remoto bloqueou o servidor de teste.

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
- `ui/dashboard.py`: componentes visuais, gráficos e tabela de movimentos.
- `ui/styles.css`: aparência e regras de adaptação para telas menores.
- `.streamlit/config.toml`: tema escuro nativo do Streamlit.
- `services/market_data.py`: formatação do código e acesso ao Yahoo Finance.
- `utils/calculations.py`: cálculos independentes da interface.
- `tests/test_calculations.py`: regressões com lacunas, zeros e histórico curto.
- `tests/test_app.py`: interações com o AppTest oficial do Streamlit, usando dados
  simulados no lugar da consulta externa.

O cache permanece na interface para que o serviço de dados continue independente
do Streamlit. Não são necessários PostgreSQL, FastAPI, IA ou n8n nesta etapa.

## Verificação

```bash
python -m compileall -q app.py ui services utils tests
python -m unittest discover -s tests -v
```

Os testes não consultam a internet. Os testes da interface são sinalizados como
ignorados (`skipped`) se Streamlit ou yfinance não estiverem instalados; instale
`requirements.txt` para executá-los. As faixas de dependências limitam versões
principais, mas não representam um arquivo de versões exatas homologadas.

Na verificação manual, consulte uma ação, altere a média móvel e o período,
clique em outra ação acompanhada e tente uma consulta inválida. Confira a
identificação dos resultados e a preservação do painel.
