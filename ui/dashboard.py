"""Estilo e componentes visuais; consultas e cálculos ficam fora deste módulo."""
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


def aplicar_estilo() -> None:
    """Carrega os tokens do Figma sem depender da pasta de execução."""
    css = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def exibir_navegacao() -> None:
    """Usa âncoras reais e identifica os recursos ainda não implementados."""
    with st.sidebar:
        st.html('''
            <div class="brand"><span>▦</span> Mercado<span>.</span></div>
            <div class="brand-subtitle">EXPLORADOR DE AÇÕES · B3</div>
            <div class="eyebrow">NAVEGAÇÃO</div>
            <nav aria-label="Navegação principal">
              <a class="nav-link active" href="#visao-geral" target="_self"><span>▦</span> Visão geral</a>
              <a class="nav-link" href="#acoes" target="_self"><span>↗</span> Ações</a>
              <div class="nav-disabled" aria-disabled="true">⌁ Índices <small>EM BREVE</small></div>
              <div class="nav-disabled" aria-disabled="true">★ Favoritos <small>EM BREVE</small></div>
              <div class="nav-disabled" aria-disabled="true">⇄ Comparador <small>EM BREVE</small></div>
              <a class="nav-link" href="#historico" target="_self"><span>≡</span> Histórico</a>
            </nav>
            <div class="tip"><strong>DICA</strong><p>Clique em uma ação acompanhada para abrir o gráfico e os indicadores.</p></div>
        ''')
        st.caption("Projeto educacional · Python + Streamlit")


def cor_variacao(valor: float | None) -> str:
    """Retorna a classe visual sem interpretar os dados como recomendação."""
    if valor is None or valor == 0:
        return "neutral"
    return "positive" if valor > 0 else "negative"


def exibir_preco_cartao(nome: str, preco: str, variacao: float | None) -> None:
    """Escapa textos antes de montar o conteúdo do cartão."""
    delta = "Variação indisponível"
    if variacao is not None:
        delta = f"{variacao:+.2f}%".replace(".", ",")
    st.html(
        f'<div class="stock-name">{escape(nome)}</div>'
        f'<div class="stock-price">{escape(preco)}</div>'
        f'<div class="stock-delta {cor_variacao(variacao)}">{delta}</div>'
    )


def exibir_linhas(dados: pd.DataFrame, compacto: bool = False,
                  cor: str = "#4d8cff") -> None:
    """Desenha séries reais; nulos interrompem a linha, sem preencher lacunas."""
    valores = dados.apply(pd.to_numeric, errors="coerce").replace(
        [float("inf"), float("-inf")], float("nan")
    )
    tabela = valores.rename_axis("Data").reset_index().melt(
        id_vars="Data", var_name="Série", value_name="Preço"
    )
    eixo_x = None if compacto else {"title": None, "format": "%d/%m", "grid": False}
    eixo_y = None if compacto else {"title": "R$", "gridColor": "#212936"}
    spec = {
        "height": 38 if compacto else 270,
        "background": "transparent",
        "mark": {"type": "line", "strokeWidth": 2,
                 "invalid": "break-paths-show-domains"},
        "encoding": {
            "x": {"field": "Data", "type": "temporal", "axis": eixo_x},
            "y": {"field": "Preço", "type": "quantitative", "axis": eixo_y,
                  "scale": {"zero": False}},
            "color": {"field": "Série", "type": "nominal",
                      "scale": {"range": [cor, "#f5ab33"]},
                      "legend": None if compacto else {"orient": "bottom", "title": None}},
            "tooltip": [
                {"field": "Data", "type": "temporal", "format": "%d/%m/%Y"},
                {"field": "Série", "type": "nominal"},
                {"field": "Preço", "type": "quantitative", "format": ".2f"},
            ],
        },
        "config": {"view": {"stroke": None},
                   "axis": {"labelColor": "#8594ab", "titleColor": "#8594ab",
                            "domain": False, "ticks": False},
                   "legend": {"labelColor": "#8594ab"}},
    }
    st.vega_lite_chart(tabela, spec, use_container_width=True, theme=None)


def exibir_tabela_movimentos(linhas: list[dict]) -> None:
    """Renderiza uma tabela rolável com textos escapados e sinais explícitos."""
    cabecalhos = ("Ativo", "Preço", "Variação", "Volume", "Setor", "Registro")
    corpo = ""
    for linha in linhas:
        corpo += "<tr>"
        for chave in cabecalhos:
            classe = cor_variacao(linha.get("variacao")) if chave == "Variação" else ""
            corpo += f'<td class="{classe}">{escape(str(linha[chave]))}</td>'
        corpo += "</tr>"
    titulos = "".join(f'<th scope="col">{titulo}</th>' for titulo in cabecalhos)
    st.html(
        '<div class="table-scroll"><table class="market-table" '
        'aria-label="Movimentos das ações acompanhadas">'
        f'<thead><tr>{titulos}</tr></thead><tbody>{corpo}</tbody></table></div>'
    )
