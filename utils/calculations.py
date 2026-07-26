import pandas as pd


def _obter_coluna_valida(
    dados: pd.DataFrame,
    nome_coluna: str,
) -> pd.Series:
    """Retorna uma coluna válida para os cálculos financeiros."""
    if dados.empty:
        raise ValueError("Não há dados disponíveis para realizar o cálculo.")

    if nome_coluna not in dados.columns:
        raise ValueError(
            f"A coluna '{nome_coluna}' não foi encontrada nos dados."
        )

    valores = dados[nome_coluna].dropna()

    if valores.empty:
        raise ValueError(
            f"A coluna '{nome_coluna}' não possui valores válidos."
        )

    return valores


def calcular_variacao_percentual(dados: pd.DataFrame) -> float:
    """Calcula a variação percentual entre o primeiro e o último fechamento."""
    fechamentos = _obter_coluna_valida(dados, "Close")
    preco_inicial = fechamentos.iloc[0]
    preco_final = fechamentos.iloc[-1]

    if preco_inicial == 0:
        raise ValueError(
            "O preço inicial não pode ser zero para calcular a variação."
        )

    return float(((preco_final - preco_inicial) / preco_inicial) * 100)


def obter_preco_atual(dados: pd.DataFrame) -> float:
    """Retorna o último preço de fechamento disponível."""
    fechamentos = _obter_coluna_valida(dados, "Close")
    return float(fechamentos.iloc[-1])


def obter_maior_preco_periodo(dados: pd.DataFrame) -> float:
    """Retorna o maior preço negociado no período."""
    precos_maximos = _obter_coluna_valida(dados, "High")
    return float(precos_maximos.max())


def obter_menor_preco_periodo(dados: pd.DataFrame) -> float:
    """Retorna o menor preço negociado no período."""
    precos_minimos = _obter_coluna_valida(dados, "Low")
    return float(precos_minimos.min())


def calcular_preco_medio_fechamento(dados: pd.DataFrame) -> float:
    """Calcula a média dos preços de fechamento do período."""
    fechamentos = _obter_coluna_valida(dados, "Close")
    return float(fechamentos.mean())


def calcular_media_movel_simples(
    dados: pd.DataFrame,
    janela: int,
) -> pd.Series:
    """Calcula a média móvel simples dos preços de fechamento."""
    if not isinstance(janela, int) or isinstance(janela, bool) or janela <= 0:
        raise ValueError("A janela da média móvel deve ser um inteiro positivo.")

    fechamentos = _obter_coluna_valida(dados, "Close")
    return fechamentos.rolling(window=janela).mean()


def adicionar_media_movel(
    dados: pd.DataFrame,
    janela: int,
) -> pd.DataFrame:
    """Retorna uma cópia dos dados com uma coluna de média móvel simples."""
    media_movel = calcular_media_movel_simples(dados, janela)
    dados_com_media = dados.copy()
    nome_coluna = f"Media_Movel_{janela}"
    dados_com_media[nome_coluna] = media_movel

    return dados_com_media


def calcular_retornos_diarios(dados: pd.DataFrame) -> pd.Series:
    """Calcula a variação percentual do fechamento entre dias consecutivos."""
    fechamentos = _obter_coluna_valida(dados, "Close")

    if len(fechamentos) < 2:
        raise ValueError(
            "São necessários pelo menos dois preços de fechamento "
            "para calcular os retornos diários."
        )

    if (fechamentos.iloc[:-1] == 0).any():
        raise ValueError(
            "O preço do dia anterior não pode ser zero "
            "para calcular o retorno diário."
        )

    return fechamentos.pct_change().dropna() * 100


def calcular_volatilidade(dados: pd.DataFrame) -> float:
    """Calcula o desvio-padrão amostral dos retornos diários percentuais."""
    retornos_diarios = calcular_retornos_diarios(dados)

    if len(retornos_diarios) < 2:
        raise ValueError(
            "São necessários pelo menos dois retornos diários "
            "para calcular a volatilidade."
        )

    return float(retornos_diarios.std())


def calcular_amplitude(dados: pd.DataFrame) -> float:
    """Calcula a diferença entre o maior e o menor preço do período."""
    maior_preco = obter_maior_preco_periodo(dados)
    menor_preco = obter_menor_preco_periodo(dados)

    return maior_preco - menor_preco


def calcular_volume_medio(dados: pd.DataFrame) -> float:
    """Calcula a média dos volumes negociados no período."""
    volumes = _obter_coluna_valida(dados, "Volume")
    return float(volumes.mean())


def obter_volume_atual(dados: pd.DataFrame) -> float:
    """Retorna o último volume negociado disponível."""
    volumes = _obter_coluna_valida(dados, "Volume")
    return float(volumes.iloc[-1])


def calcular_variacao_volume(dados: pd.DataFrame) -> float:
    """Compara percentualmente o volume atual com o volume médio."""
    volume_medio = calcular_volume_medio(dados)
    volume_atual = obter_volume_atual(dados)

    if volume_medio == 0:
        raise ValueError(
            "O volume médio não pode ser zero para calcular a variação."
        )

    return ((volume_atual - volume_medio) / volume_medio) * 100
