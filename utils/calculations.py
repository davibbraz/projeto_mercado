import pandas as pd


def _obter_coluna_valida(
    dados: pd.DataFrame,
    nome_coluna: str,
    preservar_ausentes: bool = False,
) -> pd.Series:
    """Retorna uma coluna válida para os cálculos financeiros."""
    if dados.empty:
        raise ValueError("Não há dados disponíveis para realizar o cálculo.")

    if nome_coluna not in dados.columns:
        raise ValueError(
            f"A coluna '{nome_coluna}' não foi encontrada nos dados."
        )

    valores = pd.to_numeric(dados[nome_coluna], errors="coerce").replace(
        [float("inf"), float("-inf")], float("nan")
    )

    if valores.isna().all():
        raise ValueError(
            f"A coluna '{nome_coluna}' não possui valores válidos."
        )

    return valores if preservar_ausentes else valores.dropna()


def calcular_variacao_percentual(dados: pd.DataFrame) -> float:
    """Calcula a variação percentual entre o primeiro e o último fechamento."""
    fechamentos = _obter_coluna_valida(dados, "Close")
    if len(fechamentos) < 2:
        raise ValueError("São necessários dois fechamentos para a variação.")
    preco_inicial = fechamentos.iloc[0]
    preco_final = fechamentos.iloc[-1]

    if preco_inicial == 0:
        raise ValueError(
            "O preço inicial não pode ser zero para calcular a variação."
        )

    return float(((preco_final - preco_inicial) / preco_inicial) * 100)


def obter_preco_atual(dados: pd.DataFrame) -> float:
    """Retorna o fechamento do último registro, sem recuar sobre lacunas."""
    fechamentos = _obter_coluna_valida(dados, "Close", preservar_ausentes=True)
    if pd.isna(fechamentos.iloc[-1]):
        raise ValueError("O último registro não possui preço disponível.")
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

    fechamentos = _obter_coluna_valida(dados, "Close", preservar_ausentes=True)
    return fechamentos.rolling(window=janela, min_periods=janela).mean()


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
    """Calcula retornos entre registros adjacentes, preservando lacunas.

    Não preenche preços ausentes nem procura um fechamento mais antigo.
    O calendário de pregões é o fornecido pela fonte de dados.
    """
    fechamentos = _obter_coluna_valida(dados, "Close", preservar_ausentes=True)

    if len(fechamentos) < 2:
        raise ValueError(
            "São necessários pelo menos dois preços de fechamento "
            "para calcular os retornos diários."
        )

    if ((fechamentos.shift(1) == 0) & fechamentos.notna()).any():
        raise ValueError(
            "O preço do dia anterior não pode ser zero "
            "para calcular o retorno diário."
        )

    retornos = fechamentos.pct_change(fill_method=None) * 100
    if retornos.notna().sum() == 0:
        raise ValueError(
            "Não há dois fechamentos consecutivos válidos para os retornos."
        )
    return retornos


def calcular_volatilidade(dados: pd.DataFrame) -> float:
    """Calcula o desvio-padrão amostral dos retornos diários percentuais."""
    retornos_diarios = calcular_retornos_diarios(dados).dropna()

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
    """Retorna o volume do último registro, sem recuar sobre lacunas."""
    volumes = _obter_coluna_valida(dados, "Volume", preservar_ausentes=True)
    if pd.isna(volumes.iloc[-1]):
        raise ValueError("O último registro não possui volume disponível.")
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


def calcular_variacao_ultimo_pregao(dados: pd.DataFrame) -> float:
    """Compara os dois últimos registros; o mais recente pode ser parcial."""
    fechamentos = _obter_coluna_valida(dados, "Close", preservar_ausentes=True)

    if len(fechamentos) < 2:
        raise ValueError(
            "São necessários pelo menos dois pregões "
            "para calcular a variação."
        )

    fechamento_anterior = fechamentos.iloc[-2]
    fechamento_atual = fechamentos.iloc[-1]

    if fechamentos.iloc[-2:].isna().any():
        raise ValueError("Falta fechamento em um dos dois últimos registros.")

    if fechamento_anterior == 0:
        raise ValueError("O fechamento anterior não pode ser zero.")

    variacao = (
        (fechamento_atual - fechamento_anterior)
        / fechamento_anterior
    ) * 100

    return float(variacao)
