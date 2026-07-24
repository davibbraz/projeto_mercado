import streamlit as st

from services.market_data import buscar_historico


PERIODOS_DISPONIVEIS = ("5d", "1mo", "3mo", "6mo", "1y", "5y")


st.title("Mercado de ações brasileiras")
st.write(
    "Consulte o histórico de preços de uma ação negociada na bolsa brasileira."
)

codigo_acao = st.text_input(
    "Código da ação",
    placeholder="Exemplo: PETR4",
)
periodo = st.selectbox(
    "Período",
    options=PERIODOS_DISPONIVEIS,
)

if st.button("Consultar"):
    try:
        dados = buscar_historico(codigo_acao, periodo)
    except ValueError as erro:
        st.warning(str(erro))
    except Exception:
        st.error(
            "Não foi possível consultar os dados no momento. "
            "Tente novamente mais tarde."
        )
    else:
        st.subheader("Histórico de preços")
        st.dataframe(dados, width="stretch")

        st.subheader("Preço de fechamento")
        st.line_chart(dados["Close"])
