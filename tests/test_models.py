from cmr_volume_analysis.models import Finding, Severity, status_from_findings


def test_status_from_findings():
    assert status_from_findings([]) == "pass"
    assert status_from_findings([Finding("w", Severity.WARNING, "warning")]) == "warning"
    assert status_from_findings([Finding("e", Severity.ERROR, "error")]) == "error"


def test_finding_serializes_enum():
    payload = Finding("code", Severity.WARNING, "message", {"x": 1}).to_dict()
    assert payload["severity"] == "warning"
    assert payload["context"] == {"x": 1}
