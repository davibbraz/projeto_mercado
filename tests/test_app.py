"""Fluxos da interface com o AppTest oficial; cotações são simuladas."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

DEPENDENCIAS_PRESENTES = all(
    importlib.util.find_spec(nome) is not None
    for nome in ("streamlit", "yfinance")
)
if DEPENDENCIAS_PRESENTES:
    import streamlit as st
    from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def dados_exemplo(quantidade=25):
    return pd.DataFrame(
        {
            "Close": [100 + i for i in range(quantidade)],
            "High": [102 + i for i in range(quantidade)],
            "Low": [99 + i for i in range(quantidade)],
            "Volume": [1000] * quantidade,
        },
        index=pd.bdate_range("2026-08-03", periods=quantidade),
    )


@unittest.skipUnless(DEPENDENCIAS_PRESENTES, "Instale requirements.txt para AppTest")
class TestInterface(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        self.busca = patch(
            "services.market_data.buscar_historico", return_value=dados_exemplo()
        ).start()
        self.addCleanup(patch.stopall)
        self.addCleanup(st.cache_data.clear)
        self.app = AppTest.from_file(str(APP), default_timeout=15).run()

    def consultar(self, codigo="PETR4"):
        self.app.text_input(key="codigo_acao").set_value(codigo).run()
        self.app.button(key="consultar").click().run()
        self.assertEqual(len(self.app.exception), 0)

    def test_consulta_persiste_e_media_nao_busca_novamente(self):
        self.assertEqual(self.app.selectbox(key="periodo").value, "1mo")
        self.consultar()
        self.app.selectbox(key="janela_media").select(5).run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertGreater(len(self.app.metric), 0)
        self.assertEqual(self.busca.call_count, 1)
        self.assertIn("Media_Movel_5", self.app.dataframe[0].value.columns)

    def test_atalho_consulta_imediatamente(self):
        self.app.button(key="acao_VALE3").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.text_input(key="codigo_acao").value, "VALE3")
        self.busca.assert_called_once_with("VALE3.SA", "1mo")
        self.assertGreater(len(self.app.metric), 0)

    def test_cache_reutiliza_consulta(self):
        self.consultar(" petr4 ")
        self.consultar("PETR4.SA")
        self.assertEqual(self.busca.call_count, 1)

    def test_periodo_busca_acao_consultada(self):
        self.consultar()
        self.app.text_input(key="codigo_acao").set_value("VALE3").run()
        self.app.selectbox(key="periodo").select("3mo").run()
        self.busca.assert_called_with("PETR4.SA", "3mo")
        self.assertEqual(self.busca.call_count, 2)
        self.assertEqual(len(self.app.exception), 0)

    def test_indicador_indisponivel_preserva_grafico(self):
        self.busca.return_value = dados_exemplo(2).drop(columns="Volume")
        self.consultar()
        valores = {metrica.label: metrica.value for metrica in self.app.metric}
        self.assertEqual(valores["Último preço disponível"], "R$ 101,00")
        self.assertEqual(valores["Volatilidade diária"], "Indisponível")
        self.assertEqual(valores["Volume médio"], "Indisponível")
        self.assertEqual(len(self.app.dataframe), 1)
        graficos = list(self.app.get("arrow_vega_lite_chart"))
        graficos += list(self.app.get("vega_lite_chart"))
        self.assertGreater(len(graficos), 0)
        self.assertTrue(any("20 pregões" in item.value for item in self.app.info))

    def test_falha_preserva_resultado_identificado(self):
        self.consultar()
        self.busca.side_effect = RuntimeError("Falha simulada")
        self.app.button(key="acao_VALE3").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(any("Não foi possível" in item.value for item in self.app.warning))
        self.assertTrue(any("PETR4.SA" in item.value for item in self.app.subheader))
        self.assertGreater(len(self.app.metric), 0)

    def test_codigo_vazio_nao_consulta(self):
        self.consultar("   ")
        self.busca.assert_not_called()
        self.assertTrue(any("vazio" in item.value for item in self.app.warning))

    def test_atualizar_cartoes_preserva_acao_e_cache(self):
        self.consultar("ITUB4")
        self.app.button(key="atualizar_acoes").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state.resultado["codigo"], "ITUB4.SA")
        self.assertEqual(self.busca.call_count, 5)
        self.app.button(key="acao_PETR4").click().run()
        self.assertEqual(self.busca.call_count, 5)
        self.assertEqual(self.app.session_state.resultado["codigo"], "PETR4.SA")

    def test_falha_parcial_atualizacao_preserva_cartao_anterior(self):
        self.consultar("VALE3")
        anterior = self.app.session_state.acoes_consultadas["VALE3.SA"]
        st.cache_data.clear()

        def buscar(codigo, periodo):
            if codigo == "VALE3.SA":
                raise RuntimeError("Falha simulada")
            return dados_exemplo()

        self.busca.side_effect = buscar
        self.app.button(key="atualizar_acoes").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state.falhas_acompanhadas, ["VALE3"])
        mantido = self.app.session_state.acoes_consultadas["VALE3.SA"]
        self.assertEqual(mantido["consultado_em"], anterior["consultado_em"])
        self.assertIn("MGLU3.SA", self.app.session_state.acoes_consultadas)

    def test_movimentos_separam_datas_de_pregao(self):
        self.consultar("PETR4")
        self.busca.return_value = dados_exemplo(24)
        self.consultar("VALE3")
        self.assertEqual(len(self.app.exception), 0)
        datas = self.app.selectbox(key="data_movimentos").options
        self.assertEqual(len(datas), 2)
        html = "".join(item.proto.body for item in self.app.get("html"))
        tabela = html.split('<table class="market-table"')[1]
        self.assertIn("PETR4", tabela)
        self.assertNotIn("VALE3", tabela)

    def test_preco_ausente_nao_interrompe_interface(self):
        dados = dados_exemplo()
        dados.loc[dados.index[-1], "Close"] = float("nan")
        self.busca.return_value = dados
        self.consultar()
        valores = {m.label: m.value for m in self.app.metric}
        self.assertEqual(valores["Último preço disponível"], "Indisponível")
        self.assertEqual(valores["Média móvel 20"], "Indisponível")
        self.assertEqual(len(self.app.dataframe), 1)


if __name__ == "__main__":
    unittest.main()
