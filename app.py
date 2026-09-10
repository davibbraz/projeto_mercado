from collections.abc import Callable
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from ui.dashboard import (
    aplicar_estilo, exibir_navegacao, exibir_preco_cartao,
    exibir_linhas, exibir_tabela_movimentos,
)
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
ACOES_ACOMPANHADAS = ("PETR4", "VALE3", "BBAS3", "MGLU3")
NOMES_ACOES = {
    "PETR4": ("Petrobras", "Petróleo e gás"),
    "VALE3": ("Vale", "Mineração"),
    "BBAS3": ("Banco do Brasil", "Bancos"),
    "MGLU3": ("Magazine Luiza", "Varejo"),
    "ITUB4": ("Itaú Unibanco", "Bancos"),
}
ROTULOS_PERIODOS = {"5d": "5D", "1mo": "1M", "3mo": "3M", "6mo": "6M", "1y": "1A", "5y": "5A"}
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
        st.session_state.setdefault("acoes_consultadas", {})[codigo] = (
            st.session_state.resultado.copy()
        )
        st.session_state.erro_consulta = None


def atualizar_acompanhadas() -> None:
    """Atualiza os cartões isoladamente, preservando a consulta em análise."""
    resultados = st.session_state.setdefault("acoes_consultadas", {})
    falhas = []
    for codigo in ACOES_ACOMPANHADAS:
        codigo_formatado = formatar_codigo_acao(codigo)
        try:
            dados, horario = carregar_historico(codigo_formatado, "1mo")
        except Exception:
            falhas.append(codigo)
        else:
            resultados[codigo_formatado] = {
                "codigo": codigo_formatado, "periodo": "1mo",
                "dados": dados, "consultado_em": horario,
            }
    st.session_state.falhas_acompanhadas = falhas


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


def valor_disponivel(calculo: Callable, dados: pd.DataFrame) -> float | None:
    """Usa a validação dos cálculos existentes para cada valor do painel."""
    try:
        return calculo(dados)
    except ValueError:
        return None


def exibir_resumo(dados: pd.DataFrame | None) -> None:
    """Ocupa os quatro cartões do Figma com indicadores já disponíveis."""
    indicadores = (
        ("Último preço disponível", obter_preco_atual, formatar_moeda),
        ("Variação no período", calcular_variacao_percentual, formatar_percentual),
        ("Maior preço", obter_maior_preco_periodo, formatar_moeda),
        ("Menor preço", obter_menor_preco_periodo, formatar_moeda),
    )
    with st.container(key="resumo"):
        for coluna, (titulo, calculo, formatador) in zip(st.columns(4), indicadores):
            with coluna:
                if dados is None:
                    st.metric(titulo, "—")
                else:
                    exibir_indicador(titulo, calculo, dados, formatador)


def exibir_acoes() -> None:
    """Apresenta atalhos com os resultados reais já carregados na sessão."""
    with st.container(key="acoes"):
        esquerda, direita = st.columns([3, 1])
        esquerda.subheader("Ações acompanhadas", anchor="acoes")
        direita.button("Atualizar ações", key="atualizar_acoes",
                       on_click=atualizar_acompanhadas, use_container_width=True)
        st.caption("Lista fixa de acompanhamento. Atualize os cartões ou clique em uma ação para analisar.")
        falhas = st.session_state.get("falhas_acompanhadas", [])
        if falhas:
            st.warning("Não foi possível atualizar: " + ", ".join(falhas) +
                       ". Resultados anteriores, quando disponíveis, mantêm suas datas abaixo.")
        for coluna, codigo in zip(st.columns(4), ACOES_ACOMPANHADAS):
            with coluna, st.container(border=True):
                selecionada = st.session_state.get("resultado", {}).get("codigo")
                st.button(codigo, key=f"acao_{codigo}", on_click=solicitar_consulta,
                          args=(codigo,), use_container_width=True,
                          type="primary" if selecionada == f"{codigo}.SA" else "secondary")
                resultado = st.session_state.get("acoes_consultadas", {}).get(f"{codigo}.SA")
                preco, variacao = None, None
                if resultado:
                    preco = valor_disponivel(obter_preco_atual, resultado["dados"])
                    variacao = valor_disponivel(calcular_variacao_ultimo_pregao, resultado["dados"])
                exibir_preco_cartao(NOMES_ACOES[codigo][0],
                                   formatar_moeda(preco) if preco is not None else "—",
                                   variacao)
                if resultado and "Close" in resultado["dados"]:
                    exibir_linhas(resultado["dados"][["Close"]], compacto=True,
                                  cor="#f24f5c" if variacao is not None and variacao < 0 else "#2ec77d")
                    data = resultado["dados"].index[-1].strftime("%d/%m/%Y")
                    hora = resultado["consultado_em"].strftime("%H:%M UTC")
                    st.caption(f"Registro {data} · busca {hora}")
                else:
                    st.caption("Selecione para carregar o histórico.")


def exibir_grafico_preco(dados: pd.DataFrame, janela: int) -> pd.DataFrame:
    """Mantém o gráfico disponível quando a média não pode ser calculada."""
    dados_com_media = dados
    nome_media = f"Media_Movel_{janela}"
    try:
        dados_com_media = adicionar_media_movel(dados, janela)
    except ValueError as erro:
        st.info(str(erro))
    else:
        if not dados_com_media[nome_media].notna().any():
            st.info(f"A média móvel de {janela} pregões exige {janela} "
                    "fechamentos consecutivos válidos. Aumente o período "
                    "ou escolha uma janela menor.")
    colunas = ["Close"] if "Close" in dados.columns else []
    if nome_media in dados_com_media and dados_com_media[nome_media].notna().any():
        colunas.append(nome_media)
    if colunas:
        exibir_linhas(dados_com_media[colunas].rename(
            columns={"Close": "Fechamento", nome_media: f"Média móvel {janela}"}
        ))
    else:
        st.info("Não há preços de fechamento disponíveis para o gráfico.")
    return dados_com_media


def exibir_indicadores_rapidos(dados: pd.DataFrame, janela: int) -> None:
    """Apresenta os cálculos existentes em linhas compactas ao lado do gráfico."""
    st.subheader("Indicadores rápidos")
    indicadores = (
        ("Variação no período", calcular_variacao_percentual, formatar_percentual),
        ("Último registro × anterior", calcular_variacao_ultimo_pregao, formatar_percentual),
        ("Volatilidade diária", calcular_volatilidade, formatar_percentual),
        ("Volume médio", calcular_volume_medio, formatar_volume),
        ("Variação do volume", calcular_variacao_volume, formatar_percentual),
    )
    for titulo, calculo, formatador in indicadores:
        exibir_indicador(titulo, calculo, dados, formatador)
    try:
        media = adicionar_media_movel(dados, janela)[f"Media_Movel_{janela}"].iloc[-1]
    except ValueError:
        media = float("nan")
    st.metric(f"Média móvel {janela}",
              "Indisponível" if pd.isna(media) else formatar_moeda(media))
    st.html('<div class="reading"><strong>LEITURA DOS DADOS</strong>'
            '<p>A volatilidade mede a oscilação dos retornos diários. '
            'A variação do volume compara o último registro com a média do período.</p></div>')


def exibir_movimentos() -> None:
    """Ordena apenas ações consultadas da mesma data, sem sugerir ranking da B3."""
    with st.container(key="movimentos", border=True):
        st.subheader("Movimentos das ações acompanhadas")
        resultados = [r for c, r in st.session_state.get("acoes_consultadas", {}).items()
                      if c.removesuffix(".SA") in NOMES_ACOES]
        if not resultados:
            st.caption("Atualize as ações para comparar os últimos registros disponíveis.")
            return
        datas = sorted({r["dados"].index[-1].date() for r in resultados}, reverse=True)
        # Dados de pregões diferentes nunca entram no mesmo ranking.
        data = st.selectbox("Data dos movimentos", datas, key="data_movimentos",
                            format_func=lambda d: d.strftime("%d/%m/%Y"))
        linhas = []
        for resultado in resultados:
            dados = resultado["dados"]
            if dados.index[-1].date() != data:
                continue
            codigo = resultado["codigo"].removesuffix(".SA")
            preco = valor_disponivel(obter_preco_atual, dados)
            variacao = valor_disponivel(calcular_variacao_ultimo_pregao, dados)
            volume = valor_disponivel(obter_volume_atual, dados)
            linhas.append({
                "Ativo": codigo,
                "Preço": formatar_moeda(preco) if preco is not None else "Indisponível",
                "Variação": f"{variacao:+.2f}%".replace(".", ",") if variacao is not None else "Indisponível",
                "Volume": formatar_volume(volume) if volume is not None else "Indisponível",
                "Setor": NOMES_ACOES[codigo][1], "Registro": data.strftime("%d/%m/%Y"),
                "variacao": variacao,
            })
        linhas.sort(key=lambda r: abs(r["variacao"]) if r["variacao"] is not None else -1,
                    reverse=True)
        st.caption("Ordenação pela variação absoluta entre os dois últimos registros, "
                   "apenas nas ações carregadas desta data. Não é um ranking de toda a B3; "
                   "o registro mais recente pode estar em andamento.")
        exibir_tabela_movimentos(linhas)


def exibir_historico(dados: pd.DataFrame) -> None:
    """Preserva os retornos, a tabela original e os indicadores complementares."""
    st.subheader("Histórico de preços", anchor="historico")
    historico, retornos, detalhes = st.tabs(["Histórico", "Retornos diários", "Mais indicadores"])
    with historico:
        st.dataframe(dados, width="stretch")
    with retornos:
        try:
            serie = calcular_retornos_diarios(dados)
        except ValueError as erro:
            st.info(str(erro))
        else:
            st.line_chart(serie.rename("Retorno diário (%)"), color="#4d8cff")
    with detalhes:
        for coluna, indicador in zip(st.columns(3), (
            ("Fechamento médio", calcular_preco_medio_fechamento, formatar_moeda),
            ("Amplitude do período", calcular_amplitude, formatar_moeda),
            ("Volume do último registro", obter_volume_atual, formatar_volume),
        )):
            with coluna:
                exibir_indicador(*indicador[:2], dados, indicador[2])


def main() -> None:
    """Aplica o layout do Figma com estado, cache e consultas do projeto."""
    st.set_page_config(page_title="Mercado · Dashboard B3", page_icon="▦", layout="wide")
    aplicar_estilo()
    exibir_navegacao()
    st.sidebar.button("ITUB4 · Itaú Unibanco", key="acao_ITUB4",
                      on_click=solicitar_consulta, args=("ITUB4",))
    st.title("Visão geral do mercado", anchor="visao-geral")
    st.caption("Acompanhe ações brasileiras, explore movimentos e analise ativos.")
    pesquisa, periodo, media, consultar = st.columns([3, 1, 1.3, 1], vertical_alignment="bottom")
    with pesquisa:
        st.text_input("Código da ação", placeholder="Pesquisar ativo · PETR4, VALE3, ITUB4…",
                      key="codigo_acao")
    with periodo:
        st.selectbox("Período", options=PERIODOS_DISPONIVEIS, index=1,
                     key="periodo", on_change=atualizar_periodo,
                     format_func=lambda p: ROTULOS_PERIODOS[p])
    with media:
        janela = st.selectbox("Janela da média móvel", options=JANELAS_MEDIA_MOVEL,
                              index=2, key="janela_media")
    with consultar:
        st.button("Consultar", key="consultar", on_click=solicitar_consulta,
                  type="primary", use_container_width=True)
    executar_consulta_pendente()
    erro = st.session_state.get("erro_consulta")
    if erro:
        st.warning(erro)
    resultado = st.session_state.get("resultado")
    dados = resultado["dados"] if resultado else None
    if resultado:
        if erro:
            st.info("Exibindo a última consulta bem-sucedida, identificada abaixo.")
        st.caption(f"Resumo de {resultado['codigo']} · período {resultado['periodo']}")
    exibir_resumo(dados)
    exibir_acoes()
    dados_com_media = None
    with st.container(key="analise"):
        grafico, indicadores = st.columns([2.7, 1.15], gap="medium")
        with grafico, st.container(key="grafico", border=True):
            if resultado:
                codigo = resultado["codigo"].removesuffix(".SA")
                nome = NOMES_ACOES.get(codigo, ("Ação brasileira", ""))[0]
                st.subheader(f"{resultado['codigo']} · {nome} · período {resultado['periodo']}")
                st.caption("Preço de fechamento e média móvel")
                dados_com_media = exibir_grafico_preco(dados, janela)
                horario = resultado["consultado_em"].strftime("%d/%m/%Y %H:%M UTC")
                st.caption(f"Último registro: {dados.index[-1].strftime('%d/%m/%Y')}. "
                           f"Consulta à fonte: {horario}.")
            else:
                st.subheader("Explore uma ação")
                st.info("Pesquise uma ação ou selecione um dos atalhos acima.")
                st.caption("O gráfico de preços e a média móvel aparecerão aqui após a consulta.")
        with indicadores, st.container(key="indicadores", border=True):
            if dados is not None:
                exibir_indicadores_rapidos(dados, janela)
            else:
                st.subheader("Indicadores rápidos")
                st.caption("Selecione uma ação para visualizar variação, volatilidade e volume.")
    exibir_movimentos()
    if dados_com_media is not None:
        exibir_historico(dados_com_media)
    else:
        st.subheader("Histórico de preços", anchor="historico")
        st.caption("Disponível após consultar uma ação.")
    st.caption("Fonte: Yahoo Finance via yfinance. Consultas são reutilizadas por até 5 minutos. "
               "Clique em Consultar ou Atualizar ações após esse prazo para buscar dados novos; "
               "não há atualização automática. O último registro pode corresponder a um pregão "
               "em andamento. Dados informativos, sujeitos a atrasos; não representam "
               "recomendação de investimento.")


if __name__ == "__main__":
    main()
