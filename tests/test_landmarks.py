import numpy as np

from cmr_volume_analysis.landmarks import cyclic_smooth_curve, detect_landmarks
from cmr_volume_analysis.rules import AnalysisRules


def test_detect_landmarks_without_smoothing():
    curve = np.array([100, 90, 70, 50, 60, 80], dtype=float)
    rules = AnalysisRules(use_smoothing_for_landmarks=False, min_frames=2)
    result = detect_landmarks(curve, rules)
    assert result.ed_frame == 0
    assert result.es_frame == 3
    assert not result.used_smoothed_curve


def test_smoothing_returns_copy_for_short_curve():
    curve = np.array([1.0, 2.0, 1.0])
    smoothed = cyclic_smooth_curve(curve, window=5, polyorder=2)
    assert np.array_equal(smoothed, curve)
    assert smoothed is not curve


def test_detect_landmarks_uses_cyclic_smoothing():
    curve = np.array([100, 97, 85, 68, 55, 51, 54, 67, 84, 96], dtype=float)
    rules = AnalysisRules(smoothing_window=5, smoothing_polyorder=2, min_frames=2)
    result = detect_landmarks(curve, rules)
    assert result.used_smoothed_curve
    assert result.ed_frame in {0, 9}
    assert result.es_frame in {4, 5, 6}
