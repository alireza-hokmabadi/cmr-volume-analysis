import numpy as np
import pytest

from cmr_volume_analysis.analysis import analyze_label_array
from cmr_volume_analysis.synthetic import synthetic_cine_labelmap


def test_clean_synthetic_case_produces_lv_and_rv_metrics():
    data, affine = synthetic_cine_labelmap(mode="clean")
    report = analyze_label_array(
        data,
        affine,
        case_id="clean",
        frame_time_ms=50,
        heart_rate_bpm=60,
    )
    assert report.status == "pass"
    assert set(report.metrics) == {"lv", "rv"}
    assert report.metrics["lv"].ed_frame == 0
    assert report.metrics["lv"].es_frame == 10
    assert report.metrics["lv"].edv_ml > report.metrics["lv"].esv_ml
    assert 0 < report.metrics["lv"].ejection_fraction_percent < 100
    assert report.heart_rate_bpm == pytest.approx(60)
    assert report.cycle_duration_ms == pytest.approx(1000)


def test_timing_can_be_inferred_from_heart_rate():
    data, affine = synthetic_cine_labelmap()
    report = analyze_label_array(data, affine, heart_rate_bpm=75)
    assert report.frame_time_ms == pytest.approx(40.0)
    assert report.cycle_duration_ms == pytest.approx(800.0)


def test_heart_rate_can_be_inferred_from_frame_time():
    data, affine = synthetic_cine_labelmap()
    report = analyze_label_array(data, affine, frame_time_ms=40)
    assert report.heart_rate_bpm == pytest.approx(75.0)


def test_missing_label_is_blocking_error():
    data, affine = synthetic_cine_labelmap(mode="missing_rv")
    report = analyze_label_array(data, affine)
    assert report.status == "error"
    assert report.metrics == {}
    assert any(item.code == "segmentation.missing_label" for item in report.findings)


def test_abrupt_synthetic_case_warns_but_still_measures():
    data, affine = synthetic_cine_labelmap(mode="abrupt_jump")
    report = analyze_label_array(data, affine)
    assert report.status == "warning"
    assert report.metrics["lv"].edv_ml > 0
    assert any(item.code == "curve.abrupt_phase_change" for item in report.findings)


def test_invalid_affine_is_blocking():
    data, _ = synthetic_cine_labelmap()
    affine = np.eye(4)
    affine[2, 2] = 0
    report = analyze_label_array(data, affine)
    assert report.status == "error"
    assert report.metrics == {}
    assert any(item.code == "geometry.invalid_affine" for item in report.findings)
