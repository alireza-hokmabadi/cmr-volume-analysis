import numpy as np

from cmr_volume_analysis.qc import (
    component_findings,
    curve_findings,
    timing_findings,
    validate_labelmap,
)
from cmr_volume_analysis.rules import AnalysisRules


def _codes(findings):
    return {item.code for item in findings}


def test_validate_labelmap_happy_path():
    data = np.zeros((3, 3, 3, 8), dtype=np.uint8)
    data[0, 0, 0, :] = 1
    data[1, 1, 1, :] = 2
    assert validate_labelmap(data, {"lv": 1, "rv": 2}, AnalysisRules()) == []


def test_validate_labelmap_detects_bad_input():
    rules = AnalysisRules()
    assert "segmentation.not_4d" in _codes(validate_labelmap(np.zeros((2, 2, 2)), {"lv": 1}, rules))

    data = np.zeros((2, 2, 2, 8), dtype=float)
    data[0, 0, 0, 0] = 1.5
    data[0, 0, 1, 0] = -1
    findings = validate_labelmap(data, {"lv": 1, "rv": 2}, rules)
    codes = _codes(findings)
    assert "segmentation.noninteger_labels" in codes
    assert "segmentation.negative_labels" in codes
    assert "segmentation.missing_label" in codes


def test_validate_labelmap_detects_nonfinite():
    data = np.zeros((2, 2, 2, 8), dtype=float)
    data[0, 0, 0, 0] = np.nan
    findings = validate_labelmap(data, {"lv": 1}, AnalysisRules())
    assert "segmentation.nonfinite_values" in _codes(findings)


def test_component_qc_detects_fragmentation_and_small_component():
    data = np.zeros((8, 8, 8, 8), dtype=np.uint8)
    data[1:3, 1:3, 1:3, 0] = 1
    data[5:8, 5:8, 5:8, 0] = 1
    rules = AnalysisRules(min_component_voxels=10, min_largest_component_fraction=0.8)
    codes = _codes(component_findings(data, 1, "lv", rules))
    assert "segmentation.fragmented_label" in codes
    assert "segmentation.small_components" in codes


def test_curve_qc_detects_zero_abrupt_and_flat_curves():
    rules = AnalysisRules(max_relative_phase_jump=0.3)
    assert "curve.empty_phase" in _codes(curve_findings(np.array([5.0, 0.0, 5.0]), "lv", rules))
    assert "curve.abrupt_phase_change" in _codes(
        curve_findings(np.array([100.0, 100.0, 40.0, 100.0]), "lv", rules)
    )
    assert "curve.flat" in _codes(curve_findings(np.array([10.0, 10.0, 10.0]), "lv", rules))


def test_timing_qc():
    rules = AnalysisRules(timing_disagreement_fraction=0.05)
    assert timing_findings(20, 50.0, 60.0, rules) == []
    findings = timing_findings(20, 40.0, 60.0, rules)
    assert "timing.heart_rate_disagreement" in _codes(findings)
