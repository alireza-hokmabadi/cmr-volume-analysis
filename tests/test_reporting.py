import json

from cmr_volume_analysis.analysis import analyze_label_array
from cmr_volume_analysis.models import BatchAnalysis
from cmr_volume_analysis.reporting import write_batch_report, write_case_json
from cmr_volume_analysis.rules import AnalysisRules
from cmr_volume_analysis.synthetic import synthetic_cine_labelmap


def _report():
    data, affine = synthetic_cine_labelmap()
    return analyze_label_array(data, affine, case_id="case-1", frame_time_ms=50)


def test_case_json_contains_version_and_metrics(tmp_path):
    path = tmp_path / "case.json"
    write_case_json(_report(), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["software"]["name"] == "cmr-volume-analysis"
    assert "lv" in payload["metrics"]


def test_batch_report_writes_machine_and_human_outputs(tmp_path):
    batch = BatchAnalysis([_report()])
    write_batch_report(batch, tmp_path, AnalysisRules())
    expected = {
        "batch_report.json",
        "summary.csv",
        "phase_volumes.csv",
        "findings.jsonl",
        "index.html",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    assert (tmp_path / "cases" / "case-1.json").exists()
    assert (tmp_path / "plots" / "case-1.png").exists()
