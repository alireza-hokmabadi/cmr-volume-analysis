import numpy as np
import pytest

from cmr_volume_analysis.metrics import derive_ventricular_metrics
from cmr_volume_analysis.models import LandmarkSelection


def _landmarks():
    return LandmarkSelection(0, 2, False, [120.0, 90.0, 60.0, 90.0])


def test_basic_functional_metrics():
    curve = np.array([120.0, 90.0, 60.0, 90.0])
    result = derive_ventricular_metrics(curve, 1, _landmarks(), heart_rate_bpm=60)
    assert result.edv_ml == 120
    assert result.esv_ml == 60
    assert result.stroke_volume_ml == 60
    assert result.ejection_fraction_percent == pytest.approx(50.0)
    assert result.cardiac_output_l_min == pytest.approx(3.6)


def test_temporal_rate_metrics():
    curve = np.array([120.0, 90.0, 60.0, 90.0])
    result = derive_ventricular_metrics(curve, 1, _landmarks(), frame_time_ms=250)
    assert result.ed_to_es_ms == 500
    assert result.peak_ejection_rate_ml_s == pytest.approx(120.0)
    assert result.peak_filling_rate_ml_s == pytest.approx(120.0)


def test_heart_rate_can_supply_frame_time_for_rates():
    curve = np.array([120.0, 90.0, 60.0, 90.0])
    result = derive_ventricular_metrics(curve, 1, _landmarks(), heart_rate_bpm=60)
    assert result.ed_to_es_ms == pytest.approx(500.0)
