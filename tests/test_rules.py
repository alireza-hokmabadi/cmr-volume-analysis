import json

import pytest

from cmr_volume_analysis.rules import AnalysisRules


def test_rules_roundtrip_json(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"max_relative_phase_jump": 0.2}), encoding="utf-8")
    rules = AnalysisRules.from_json(path)
    assert rules.max_relative_phase_jump == 0.2
    assert rules.to_dict()["min_frames"] == 8


def test_rules_reject_unknown_key(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"unknown": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown analysis rule"):
        AnalysisRules.from_json(path)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_frames": 1},
        {"min_largest_component_fraction": 0.0},
        {"max_relative_phase_jump": 0.0},
        {"smoothing_window": 4},
        {"smoothing_polyorder": 5},
    ],
)
def test_rules_validate_configuration(kwargs):
    with pytest.raises(ValueError):
        AnalysisRules(**kwargs)
