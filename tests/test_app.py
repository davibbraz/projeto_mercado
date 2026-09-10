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
        self.assertGreater(len(self.app.get("arrow_vega_lite_chart")), 0)
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


if __name__ == "__main__":
    unittest.main()
