"""Regressões de indicadores com poucos dados e lacunas, sem rede."""
import unittest

import pandas as pd

from utils.calculations import (
    adicionar_media_movel,
    calcular_media_movel_simples,
    calcular_retornos_diarios,
    calcular_variacao_percentual,
    calcular_variacao_ultimo_pregao,
    calcular_variacao_volume,
    calcular_volatilidade,
    obter_preco_atual,
    obter_volume_atual,
)


def historico(precos: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"Close": precos}, index=pd.bdate_range("2026-08-03", periods=len(precos))
    )


class TestCalculos(unittest.TestCase):
    def test_retornos_normais(self):
        resultado = calcular_retornos_diarios(historico([100, 110, 99]))
        self.assertTrue(pd.isna(resultado.iloc[0]))
        self.assertAlmostEqual(resultado.iloc[1], 10)
        self.assertAlmostEqual(resultado.iloc[2], -10)

    def test_nao_cruza_lacunas_e_retoma_apos_par_valido(self):
        dados = historico([100, float("nan"), 121, 133.1])
        resultado = calcular_retornos_diarios(dados)
        self.assertTrue(resultado.iloc[:3].isna().all())
        self.assertAlmostEqual(resultado.iloc[3], 10)
        self.assertTrue(resultado.index.equals(dados.index))

    def test_lacuna_sem_par_valido(self):
        with self.assertRaises(ValueError):
            calcular_retornos_diarios(historico([100, float("nan"), 121]))

    def test_zero_no_denominador(self):
        with self.assertRaises(ValueError):
            calcular_retornos_diarios(historico([0, 100]))

    def test_media_preserva_lacuna(self):
        dados = historico([10, float("nan"), 30, 40])
        media = calcular_media_movel_simples(dados, 2)
        self.assertTrue(media.iloc[:3].isna().all())
        self.assertEqual(media.iloc[3], 35)

    def test_media_sem_historico_suficiente(self):
        media = calcular_media_movel_simples(historico([10] * 5), 20)
        self.assertTrue(media.isna().all())

    def test_media_nao_modifica_original(self):
        dados = historico([10, 20, 30])
        original = dados.copy(deep=True)
        resultado = adicionar_media_movel(dados, 2)
        pd.testing.assert_frame_equal(dados, original)
        self.assertEqual(resultado["Media_Movel_2"].iloc[-1], 25)

    def test_janelas_invalidas(self):
        for janela in (0, -1, True, 2.5):
            with self.subTest(janela=janela), self.assertRaises(ValueError):
                calcular_media_movel_simples(historico([1, 2]), janela)

    def test_volatilidade_exige_dois_retornos_validos(self):
        for precos in ([100, 110], [100, float("nan"), 121, 133.1]):
            with self.subTest(precos=precos), self.assertRaises(ValueError):
                calcular_volatilidade(historico(precos))
        self.assertAlmostEqual(
            calcular_volatilidade(historico([100, 110, 99])), 2 ** 0.5 * 10
        )

    def test_ultimo_registro_nao_recua_sobre_lacuna(self):
        for precos in ([100, float("nan"), 121], [100, 110, float("nan")]):
            with self.subTest(precos=precos), self.assertRaises(ValueError):
                calcular_variacao_ultimo_pregao(historico(precos))
        self.assertAlmostEqual(
            calcular_variacao_ultimo_pregao(historico([100, 110])), 10
        )

    def test_preco_e_volume_nao_usam_registro_antigo(self):
        dados = historico([100, float("nan")])
        dados["Volume"] = [10, float("nan")]
        for calculo in (obter_preco_atual, obter_volume_atual):
            with self.subTest(calculo=calculo), self.assertRaises(ValueError):
                calculo(dados)

    def test_variacao_periodo_com_um_registro(self):
        with self.assertRaises(ValueError):
            calcular_variacao_percentual(historico([100]))

    def test_volume_zero(self):
        dados = historico([10, 20])
        dados["Volume"] = [0, 0]
        with self.assertRaises(ValueError):
            calcular_variacao_volume(dados)

    def test_coluna_invalida(self):
        for dados in (pd.DataFrame(), pd.DataFrame({"Open": [1]}),
                      historico([float("nan")]), historico([float("inf")])):
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                obter_preco_atual(dados)


if __name__ == "__main__":
    unittest.main()
