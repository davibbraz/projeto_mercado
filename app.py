from collections.abc import Callable
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from services.market_data import buscar_historico, formatar_codigo_acao
from utils.calculations import (
    adicionar_media_movel,
    calcular_amplitude,
    calcular_preco_medio_fechamento,
    calcular_retornos_diarios,
    calcular_variacao_percentual,
    calcular_variacao_ultimo_pregao,
    calcular_variacao_volume,
    calcular_volatilidade,
    calcular_volume_medio,
    obter_maior_preco_periodo,
    obter_menor_preco_periodo,
    obter_preco_atual,
    obter_volume_atual,
)


PERIODOS_DISPONIVEIS = ("5d", "1mo", "3mo", "6mo", "1y", "5y")
JANELAS_MEDIA_MOVEL = (5, 10, 20, 50)
ACOES_ACOMPANHADAS = ("PETR4", "VALE3", "ITUB4", "BBAS3")
TEMPO_CACHE_SEGUNDOS = 300


@st.cache_data(ttl=TEMPO_CACHE_SEGUNDOS, max_entries=128, show_spinner=False)
def carregar_historico(
    codigo: str, periodo: str,
) -> tuple[pd.DataFrame, datetime]:
    """Reutiliza consultas recentes e preserva o horário da busca original."""
    dados = buscar_historico(codigo, periodo)
    return dados, datetime.now(timezone.utc)


def solicitar_consulta(codigo: str | None = None) -> None:
    """Registra a consulta pedida pelo campo de pesquisa ou por um atalho."""
    if codigo is not None:
        # Callbacks executam antes dos widgets, permitindo atualizar o campo.
        st.session_state.codigo_acao = codigo
    try:
        codigo_formatado = formatar_codigo_acao(st.session_state.codigo_acao)
    except ValueError as erro:
        st.session_state.erro_consulta = str(erro)
        return
    st.session_state.consulta = (codigo_formatado, st.session_state.periodo)
    st.session_state.consultar_pendente = True
    st.session_state.erro_consulta = None


def atualizar_periodo() -> None:
    """Aplica o período à ação consultada, preservando a pesquisa em edição."""
    consulta = st.session_state.get("consulta")
    if consulta is not None:
        st.session_state.consulta = (consulta[0], st.session_state.periodo)
        st.session_state.consultar_pendente = True
        st.session_state.erro_consulta = None


def executar_consulta_pendente() -> None:
    """Substitui o resultado somente depois de uma consulta bem-sucedida."""
    if not st.session_state.pop("consultar_pendente", False):
        return
    codigo, periodo = st.session_state.consulta
    try:
        with st.spinner("Consultando histórico..."):
            dados, consultado_em = carregar_historico(codigo, periodo)
    except ValueError as erro:
        st.session_state.erro_consulta = str(erro)
    except Exception:
        st.session_state.erro_consulta = (
            "Não foi possível consultar os dados no momento. "
            "Tente novamente mais tarde."
        )
    else:
        st.session_state.resultado = {
            "codigo": codigo,
            "periodo": periodo,
            "dados": dados,
            "consultado_em": consultado_em,
        }
        st.session_state.erro_consulta = None


def formatar_moeda(valor: float) -> str:
    """Formata um valor numérico como moeda brasileira."""
    valor_formatado = f"{valor:,.2f}"
    valor_formatado = valor_formatado.replace(",", "_").replace(".", ",")
    return f"R$ {valor_formatado.replace('_', '.')}"


def formatar_volume(valor: float) -> str:
    """Formata um volume sem casas decimais."""
    return f"{valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    """Formata um percentual em português."""
    return f"{valor:.2f}%".replace(".", ",")


def exibir_indicador(
    titulo: str,
    calculo: Callable[[pd.DataFrame], float],
    dados: pd.DataFrame,
    formatador: Callable[[float], str],
) -> None:
    """Isola a falta de dados de um indicador sem interromper o painel."""
    try:
        valor = calculo(dados)
    except ValueError as erro:
        st.metric(titulo, "Indisponível")
        st.caption(str(erro))
    else:
        st.metric(titulo, formatador(valor))


def exibir_resumo(dados: pd.DataFrame) -> None:
    """Apresenta os indicadores existentes e a variação do último registro."""
    grupos = (
        ("Resumo de preços", (
            ("Último preço disponível", obter_preco_atual, formatar_moeda),
            ("Maior preço", obter_maior_preco_periodo, formatar_moeda),
            ("Menor preço", obter_menor_preco_periodo, formatar_moeda),
            ("Fechamento médio", calcular_preco_medio_fechamento, formatar_moeda),
        )),
        ("Variações de preço", (
            ("Variação no período", calcular_variacao_percentual, formatar_percentual),
            (
                "Último registro × anterior",
                calcular_variacao_ultimo_pregao,
                formatar_percentual,
            ),
        )),
        ("Risco e oscilação", (
            ("Volatilidade diária", calcular_volatilidade, formatar_percentual),
            ("Amplitude do período", calcular_amplitude, formatar_moeda),
        )),
        ("Volume", (
            ("Volume do último registro", obter_volume_atual, formatar_volume),
            ("Volume médio", calcular_volume_medio, formatar_volume),
            ("Variação do volume", calcular_variacao_volume, formatar_percentual),
        )),
    )
    for titulo_grupo, indicadores in grupos:
        st.subheader(titulo_grupo)
        for coluna, (titulo, calculo, formatador) in zip(
            st.columns(len(indicadores)), indicadores
        ):
            with coluna:
                exibir_indicador(titulo, calculo, dados, formatador)


def exibir_graficos(dados: pd.DataFrame, janela: int) -> None:
    """Exibe gráficos disponíveis e explica a falta de média móvel."""
    st.subheader("Preço de fechamento e média móvel")
    dados_com_media = dados
    try:
        dados_com_media = adicionar_media_movel(dados, janela)
    except ValueError as erro:
        st.info(str(erro))
    else:
        nome_media = f"Media_Movel_{janela}"
        if dados_com_media[nome_media].notna().any():
            st.line_chart(dados_com_media[["Close", nome_media]])
        else:
            st.info(
                f"A média móvel de {janela} pregões exige {janela} "
                "fechamentos consecutivos válidos. Aumente o período "
                "ou escolha uma janela menor."
            )
            st.line_chart(dados_com_media[["Close"]])

    st.subheader("Retornos diários")
    try:
        retornos = calcular_retornos_diarios(dados)
    except ValueError as erro:
        st.info(str(erro))
    else:
        st.line_chart(retornos.rename("Retorno diário (%)"))

    st.subheader("Histórico de preços")
    st.dataframe(dados_com_media, width="stretch")


def main() -> None:
    """Monta o dashboard e mantém o último resultado durante as interações."""
    st.title("Mercado de ações brasileiras")
    st.write("Consulte preços, oscilações e volumes de ações da bolsa brasileira.")
    st.subheader("Ações acompanhadas")
    st.caption("Lista fixa de atalhos. Clique em uma ação para abrir seu gráfico.")
    for coluna, codigo in zip(st.columns(len(ACOES_ACOMPANHADAS)), ACOES_ACOMPANHADAS):
        coluna.button(
            codigo, key=f"acao_{codigo}", on_click=solicitar_consulta, args=(codigo,)
        )

    st.text_input("Código da ação", placeholder="Exemplo: PETR4", key="codigo_acao")
    st.selectbox(
        "Período", options=PERIODOS_DISPONIVEIS, index=1,
        key="periodo", on_change=atualizar_periodo,
    )
    janela = st.selectbox(
        "Janela da média móvel", options=JANELAS_MEDIA_MOVEL,
        index=2, key="janela_media",
    )
    st.button("Consultar", key="consultar", on_click=solicitar_consulta)
    executar_consulta_pendente()

    erro = st.session_state.get("erro_consulta")
    if erro:
        st.warning(erro)
    resultado = st.session_state.get("resultado")
    if resultado is None:
        st.info("Pesquise uma ação ou selecione um dos atalhos acima.")
        return
    if erro:
        st.info("Exibindo a última consulta bem-sucedida, identificada abaixo.")

    dados = resultado["dados"]
    horario_consulta = resultado["consultado_em"].strftime("%d/%m/%Y %H:%M UTC")
    st.subheader(f"{resultado['codigo']} · período {resultado['periodo']}")
    st.caption(
        f"Último registro: {dados.index[-1].strftime('%d/%m/%Y')}. "
        f"Consulta à fonte: {horario_consulta}. "
        "O registro mais recente pode corresponder a um pregão em andamento."
    )
    st.caption(
        "Consultas são reutilizadas por até 5 minutos. Clique em Consultar "
        "após esse prazo para buscar dados novos; não há atualização automática."
    )
    exibir_resumo(dados)
    exibir_graficos(dados, janela)
    st.caption(
        "Fonte: Yahoo Finance via yfinance. Dados informativos, sujeitos a "
        "atrasos; não representam recomendação de investimento."
    )


if __name__ == "__main__":
    main()
