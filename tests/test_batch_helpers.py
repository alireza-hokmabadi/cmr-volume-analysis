import pytest

from cmr_volume_analysis.batch import _optional_float, _optional_int


def test_optional_parsers():
    assert _optional_float("") is None
    assert _optional_float("1.5") == pytest.approx(1.5)
    assert _optional_int(None, 7) == 7
    assert _optional_int("3", 7) == 3
