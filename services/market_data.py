import pandas as pd
import yfinance as yf


def formatar_codigo_acao(codigo: str) -> str:
    """
    Formata o código informado pelo usuário para o padrão
    utilizado pelo Yahoo Finance na bolsa brasileira.

    Exemplo:
        PETR4 -> PETR4.SA

    Raises:
        ValueError: Quando o código está vazio.
    """

    codigo = codigo.strip().upper()

    if not codigo:
        raise ValueError("O código da ação não pode estar vazio.")

    if not codigo.endswith(".SA"):
        codigo = f"{codigo}.SA"

    return codigo


def buscar_historico(
    codigo: str,
    periodo: str = "1mo",
) -> pd.DataFrame:
    """
    Busca o histórico de preços de uma ação brasileira.

    Args:
        codigo: Código da ação, como PETR4 ou VALE3.
        periodo: Período que será consultado.

    Returns:
        DataFrame contendo os dados históricos da ação.

    Raises:
        ValueError: Quando nenhum dado é encontrado.
    """

    codigo_formatado = formatar_codigo_acao(codigo)

    acao = yf.Ticker(codigo_formatado)

    dados = acao.history(period=periodo)

    if dados.empty:
        raise ValueError(
            f"Nenhum dado encontrado para {codigo_formatado}."
        )

    return dados
