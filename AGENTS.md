# AGENTS.md

## Visão geral do projeto

Este é um projeto educacional de análise do mercado financeiro desenvolvido em Python.

O objetivo inicial é criar um sistema capaz de:

- consultar ações da bolsa brasileira;
- exibir dados históricos de preços;
- mostrar gráficos e indicadores financeiros;
- permitir que o usuário pesquise ativos;
- futuramente interpretar os dados usando inteligência artificial;
- futuramente integrar automações com n8n.

O projeto deve começar simples e evoluir progressivamente.

## Tecnologias planejadas

- Python como linguagem principal;
- Streamlit para a interface e o dashboard;
- pandas para manipulação de dados;
- yfinance como fonte inicial de dados de mercado;
- PostgreSQL para persistência de dados em etapas futuras;
- n8n para automações;
- FastAPI para uma API interna futura;
- inteligência artificial para explicações e análises dos dados.

As tecnologias futuras não devem ser implementadas antes de serem necessárias para a etapa atual.

## Ambiente de desenvolvimento

- Windows com WSL;
- distribuição Debian no WSL;
- Visual Studio Code;
- ambiente virtual Python com `venv`;
- Git e GitHub para controle de versão;
- comandos devem ser compatíveis com Linux e Debian.

## Estado atual

O projeto está em sua fase inicial.

Atualmente existe um módulo de dados de mercado responsável por:

- receber o código de uma ação brasileira;
- formatar códigos como `PETR4` para `PETR4.SA`;
- consultar o histórico da ação usando `yfinance`;
- retornar os dados em um DataFrame do pandas;
- verificar se foram encontrados dados;
- lançar um erro quando nenhum dado for encontrado.

Esta seção deve ser atualizada conforme novas funcionalidades forem implementadas.

## Estrutura do projeto

A estrutura aproximada do projeto é:

```text
projeto_mercado/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .gitignore
├── app.py
├── src/
│   └── market_data.py
└── venv/
```

A estrutura acima deve ser adaptada aos nomes reais dos arquivos existentes.

A pasta `venv/` é local e não deve ser adicionada ao Git.

## Organização desejada

Sempre que possível, separar as responsabilidades entre módulos diferentes:

- interface Streamlit;
- consulta de dados de mercado;
- cálculos e indicadores;
- acesso ao banco de dados;
- serviços de inteligência artificial;
- automações e integrações externas.

Evitar colocar toda a lógica dentro de um único arquivo.

A interface não deve conter diretamente toda a lógica de consulta, cálculo ou persistência.

## Antes de alterar o código

Antes de editar qualquer arquivo, o agente deve:

1. ler este arquivo;
2. analisar os arquivos relacionados à tarefa;
3. verificar se já existe uma função que resolva parte do problema;
4. identificar possíveis impactos da alteração;
5. apresentar um plano curto antes de editar.

O plano deve informar:

- quais arquivos serão modificados;
- o objetivo de cada alteração;
- como o resultado será testado.

O agente deve evitar criar arquivos, classes ou abstrações desnecessárias.

## Forma de trabalho

Este também é um projeto de aprendizado.

Ao realizar alterações:

1. explicar resumidamente o que será feito antes de editar;
2. fazer alterações pequenas e progressivas;
3. explicar conceitos novos utilizados no código;
4. não reestruturar todo o projeto sem necessidade;
5. preservar o que já estiver funcionando;
6. não instalar bibliotecas novas sem explicar por que são necessárias;
7. mostrar quais arquivos foram alterados;
8. executar ou indicar testes relevantes;
9. informar possíveis erros, riscos ou limitações;
10. não esconder decisões importantes atrás de abstrações complexas;
11. evitar entregar grandes quantidades de código sem explicação;
12. priorizar uma funcionalidade por etapa.

Quando houver mais de uma solução possível, explicar brevemente as principais opções e justificar a escolha feita.

## Padrões de código

- utilizar nomes de funções e variáveis claros;
- preferir nomes em português enquanto o projeto seguir esse padrão;
- adicionar type hints nas funções;
- escrever docstrings nas funções principais;
- manter funções pequenas e com uma responsabilidade clara;
- evitar duplicação de código;
- tratar erros de APIs e dados ausentes;
- utilizar mensagens de erro compreensíveis;
- não usar valores mágicos quando uma constante clara puder ser utilizada;
- evitar otimizações prematuras;
- seguir o estilo PEP 8 sempre que possível.

## Tratamento de erros

As consultas de dados externos devem considerar pelo menos:

- código de ativo inválido;
- ativo não encontrado;
- resposta vazia;
- indisponibilidade da fonte de dados;
- falha de conexão;
- dados ausentes ou incompletos.

Os erros devem ser tratados em uma camada adequada.

Funções internas podem lançar exceções claras, enquanto a interface deve apresentar mensagens compreensíveis para o usuário.

## Segurança

- nunca colocar senhas, tokens ou chaves de API diretamente no código;
- utilizar variáveis de ambiente para informações sensíveis;
- não adicionar arquivos `.env` ao Git;
- não mostrar segredos em logs ou mensagens de erro;
- não implementar operações reais de compra e venda nesta fase;
- não executar comandos destrutivos sem autorização explícita.

## Dependências

Antes de adicionar uma dependência:

1. verificar se a funcionalidade pode ser feita com as bibliotecas existentes;
2. explicar a finalidade da nova dependência;
3. informar por que ela é adequada ao projeto;
4. atualizar o arquivo `requirements.txt`;
5. informar o comando de instalação;
6. verificar se a biblioteca é compatível com o ambiente atual.

Não adicionar uma biblioteca apenas para realizar uma tarefa simples que possa ser implementada com a biblioteca padrão do Python.

## Comandos do projeto

Ativar o ambiente virtual:

```bash
source venv/bin/activate
```

Instalar as dependências:

```bash
python -m pip install -r requirements.txt
```

Verificar a sintaxe dos arquivos Python:

```bash
python -m compileall .
```

Executar o dashboard, quando o arquivo `app.py` e a interface Streamlit estiverem disponíveis:

```bash
streamlit run app.py
```

Os comandos devem ser executados a partir da raiz do projeto, salvo quando indicado o contrário.

## Validação

Uma tarefa somente deve ser considerada concluída quando:

- o código estiver sintaticamente válido;
- os imports estiverem corretos;
- o comportamento anterior não tiver sido quebrado;
- os principais casos de erro tiverem sido considerados;
- houver uma explicação clara das alterações;
- os arquivos alterados tiverem sido informados;
- os comandos necessários para testar tiverem sido apresentados;
- os testes relevantes tiverem sido executados quando possível.

Caso não seja possível executar um teste, o agente deve informar claramente o motivo.

## Git e versionamento

- não executar `git push --force`;
- não apagar ou reescrever o histórico do repositório;
- não alterar arquivos fora do escopo da tarefa;
- não realizar commit ou push sem solicitação explícita;
- não adicionar `venv/`, `.env`, senhas, tokens ou chaves ao repositório;
- verificar o estado do repositório antes de operações importantes;
- sugerir uma mensagem de commit ao concluir uma alteração;
- evitar incluir alterações não relacionadas no mesmo commit.

Antes de uma mudança grande, recomendar a criação de um commit de segurança.

## Restrições atuais

- começar pela bolsa brasileira;
- utilizar o `yfinance` como fonte inicial de dados;
- não implementar operações reais de compra e venda;
- não prometer lucros ou retornos financeiros;
- não apresentar indicadores como garantias de valorização;
- diferenciar dados, indicadores e análises de recomendações de investimento;
- não avançar prematuramente para PostgreSQL, FastAPI, IA ou n8n;
- priorizar aprendizado, clareza e manutenção do código;
- desenvolver uma etapa pequena e funcional por vez.

## Prioridade atual

A prioridade atual é consolidar a camada de consulta de dados de mercado antes de adicionar funcionalidades mais avançadas.

A evolução recomendada é:

1. validar a consulta de uma ação brasileira;
2. melhorar o tratamento de erros;
3. criar uma interface Streamlit simples;
4. permitir a escolha do período;
5. exibir tabela e gráfico de preços;
6. adicionar indicadores financeiros básicos;
7. adicionar persistência de dados;
8. integrar inteligência artificial;
9. integrar automações com n8n.

O agente não deve implementar várias dessas etapas ao mesmo tempo sem solicitação explícita.