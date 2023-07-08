from datetime import datetime

import pytest

from pocketutils.core.chars import Chars
from pocketutils.tools.unit_tools import UnitTools


class TestUnitTools:
    def test_delta_time_to_str(self):
        f = UnitTools.delta_time_to_str
        assert f(15) == "15s"
        assert f(313) == "5.22min"
        assert f(15, space=Chars.narrownbsp) == "15" + Chars.narrownbsp + "s"
        assert f(15 * 60) == "15min"
        assert f(15 * 60 + 5) == "15.08min"
        assert f(15 * 60 * 60 + 5 * 60) == "15.08hr"

    def test_approx_time_wrt(self):
        f = UnitTools.approx_time_wrt
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 2)) == "2021-01-02 00:00"
        assert f(datetime(2021, 1, 1), datetime(1996, 1, 1)) == "1996"
        assert f(datetime(2021, 1, 1), datetime(2021, 5, 5)) == "2021-05"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 5)) == "2021-01-05"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 1, 6)) == "2021-01-01 06:00"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 1, 6, 22)) == "2021-01-01 06:22"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 2, 6, 22)) == "2021-01-02 06:22"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 2, 2, 22)) == "2021-01-02 02:22"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 2, 2, 22, 40)) == "2021-01-02 02:22"
        assert f(datetime(2021, 1, 1), datetime(2021, 1, 1, 0, 1, 40)) == "2021-01-01 00:01:40"
        assert (
            f(datetime(2021, 1, 1), datetime(2021, 1, 1, 0, 0, 0, 222222))
            == "2021-01-01 00:00:00.222"
        )
        assert (
            f(datetime(2021, 1, 1), datetime(2021, 1, 1, 0, 0, 0, 222))
            == "2021-01-01 00:00:00.000222"
        )
        assert (
            f(datetime(2021, 1, 1), datetime(2021, 1, 1, 0, 0, 0, 0))
            == "2021-01-01 00:00:00.000000"
        )
        assert f(datetime(2021, 1, 10), datetime(2021, 1, 5)) == "2021-01-05"  # negative delta
        assert f(datetime(2021, 9, 30, 23), datetime(2021, 10, 1)) == "2021-10-01 00:00"
        assert f(datetime(2021, 10, 1), datetime(2021, 9, 30, 23)) == "2021-09-30 23:00"
        assert f(datetime(2021, 9, 27, 1), datetime(2021, 10, 1)) == "2021-10-01"
        assert f(datetime(2021, 10, 1), datetime(2021, 9, 25)) == "2021-09-25"
        assert (
            f(datetime(2021, 1, 1), datetime(2021, 1, 1, 0, 0, 0, 0), skip_today=True)
            == "00:00:00.000000"
        )

    def test_ms_to_minsec(self):
        f = UnitTools.ms_to_minsec
        assert f(15) == "15ms"
        assert f(15 * 1000) == "00:15"
        assert f(15 * 60 * 1000) == "15:00"
        assert f(15 * 60 * 60 * 1000) == "15:00:00"
        assert f(15 * 24 * 60 * 60 * 1000) == "15d:00:00:00"

    def test_round_to_sigfigs(self):
        f = UnitTools.round_to_sigfigs
        assert str(f(0.0012, 3)) == "0.0012"
        assert str(f(0.0012, 1)) == "0.001"
        assert str(f(0.0012 / 1000 / 1000, 3)) == "1.2e-09"
        assert str(f(0.0012 / 1000 / 1000, 1)) == "1e-09"

    def test_format_micromolar(self):
        f = UnitTools.format_micromolar
        assert f(1.2) == "1.2µM"
        assert f(1.2, space=Chars.narrownbsp) == "1.2" + Chars.narrownbsp + "µM"
        assert f(0.0012) == "1.2nM"
        assert f(0.0012 / 1000) == "1.2pM"
        assert f(0.0012 / 1e6) == "1.2fM"
        assert f(9999) == "9.999mM"
        assert f(1000 * 1000) == "1M"
        assert f(9999999) == "10M"

    def test_dose_to_micromolar(self):
        f = UnitTools.concentration_to_micromolar
        assert f(55, "M") == 55 * 1e6
        assert f(55, "mM") == 55 * 1e3
        assert f(55, "uM") == 55
        assert f(-55, "uM") == -55
        assert f(55, "µM") == 55
        assert f(55, "nM") * 1e3 == 55
        assert f(-55, "nM") * 1e3 == -55
        assert f(-55, "nM") * 1e3 == pytest.approx(-55)
        assert f(55, "pM") * 1e6 == pytest.approx(55)
        assert f(55, "fM") * 1e9 == pytest.approx(55)

    def test_extract_micromolar(self):
        f = UnitTools.extract_micromolar
        assert f("abc 55 nM") == 55 / 1000
        assert f(f"abc 55{Chars.narrownbsp}uM") == 55
        assert f("abc 55 uM") == 55
        assert f("a.55bc 55uM") == 55

    def test_split_drug_dose(self):
        f = UnitTools.split_species_micromolar
        assert f("abc 55 nM") == ("abc", 55 / 1000)
        assert f(f"abc 55{Chars.narrownbsp}uM") == ("abc", 55)
        assert f("abc 55 uM") == ("abc", 55)
        assert f("a.55bc 55uM") == ("a.55bc", 55)
        assert f("") == ("", None)
        assert f("a.55bc") == ("a.55bc", None)


if __name__ == "__main__":
    pytest.main()
