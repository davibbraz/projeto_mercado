import streamlit as st

from services.market_data import buscar_historico
from utils.calculations import (
    adicionar_media_movel,
    calcular_amplitude,
    calcular_media_movel_simples,
    calcular_preco_medio_fechamento,
    calcular_retornos_diarios,
    calcular_variacao_percentual,
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


def formatar_moeda(valor: float) -> str:
    """Formata um valor numérico como moeda brasileira."""
    valor_formatado = f"{valor:,.2f}"
    valor_formatado = valor_formatado.replace(",", "_").replace(".", ",")
    return f"R$ {valor_formatado.replace('_', '.')}"


def formatar_volume(valor: float) -> str:
    """Formata um volume sem casas decimais."""
    return f"{valor:,.0f}".replace(",", ".")


st.title("Mercado de ações brasileiras")
st.write(
    "Consulte preços, oscilações e volumes de uma ação negociada "
    "na bolsa brasileira."
)

codigo_acao = st.text_input(
    "Código da ação",
    placeholder="Exemplo: PETR4",
)
periodo = st.selectbox(
    "Período",
    options=PERIODOS_DISPONIVEIS,
)
janela_media = st.selectbox(
    "Janela da média móvel",
    options=JANELAS_MEDIA_MOVEL,
    index=2,
)

if st.button("Consultar"):
    try:
        dados = buscar_historico(codigo_acao, periodo)

        variacao_percentual = calcular_variacao_percentual(dados)
        preco_atual = obter_preco_atual(dados)
        maior_preco = obter_maior_preco_periodo(dados)
        menor_preco = obter_menor_preco_periodo(dados)
        preco_medio = calcular_preco_medio_fechamento(dados)

        media_movel = calcular_media_movel_simples(dados, janela_media)
        dados_com_media = adicionar_media_movel(dados, janela_media)
        nome_media_movel = f"Media_Movel_{janela_media}"

        retornos_diarios = calcular_retornos_diarios(dados)
        volatilidade = calcular_volatilidade(dados)
        amplitude = calcular_amplitude(dados)

        volume_medio = calcular_volume_medio(dados)
        volume_atual = obter_volume_atual(dados)
        variacao_volume = calcular_variacao_volume(dados)
    except ValueError as erro:
        st.warning(str(erro))
    except Exception:
        st.error(
            "Não foi possível consultar os dados no momento. "
            "Tente novamente mais tarde."
        )
    else:
        st.subheader("Resumo de preços")
        coluna_preco, coluna_maior, coluna_menor, coluna_media = st.columns(4)
        coluna_preco.metric(
            "Preço atual",
            formatar_moeda(preco_atual),
            f"{variacao_percentual:.2f}% no período",
        )
        coluna_maior.metric("Maior preço", formatar_moeda(maior_preco))
        coluna_menor.metric("Menor preço", formatar_moeda(menor_preco))
        coluna_media.metric("Fechamento médio", formatar_moeda(preco_medio))

        st.subheader("Risco e oscilação")
        coluna_volatilidade, coluna_amplitude = st.columns(2)
        coluna_volatilidade.metric(
            "Volatilidade diária",
            f"{volatilidade:.2f}%",
        )
        coluna_amplitude.metric(
            "Amplitude do período",
            formatar_moeda(amplitude),
        )

        st.subheader("Volume")
        coluna_volume_atual, coluna_volume_medio, coluna_variacao_volume = (
            st.columns(3)
        )
        coluna_volume_atual.metric(
            "Volume atual",
            formatar_volume(volume_atual),
        )
        coluna_volume_medio.metric(
            "Volume médio",
            formatar_volume(volume_medio),
        )
        coluna_variacao_volume.metric(
            "Variação do volume",
            f"{variacao_volume:.2f}%",
        )

        st.subheader("Preço de fechamento e média móvel")
        dados_grafico = dados[["Close"]].copy()
        dados_grafico[nome_media_movel] = media_movel
        st.line_chart(dados_grafico)

        st.subheader("Retornos diários")
        st.line_chart(retornos_diarios.rename("Retorno diário (%)"))

        st.subheader("Histórico de preços")
        st.dataframe(dados_com_media, width="stretch")

        st.caption(
            "Os dados e cálculos são informativos e não representam "
            "recomendação de investimento."
        )
