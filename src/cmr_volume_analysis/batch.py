from __future__ import annotations

import csv
from pathlib import Path

from .analysis import analyze_cine_segmentation
from .models import BatchAnalysis, CaseAnalysis, Finding, Severity
from .reporting import write_batch_report
from .rules import AnalysisRules


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def _optional_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    return int(value)


def run_batch(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    rules: AnalysisRules | None = None,
    include_hash: bool = False,
) -> BatchAnalysis:
    active_rules = rules or AnalysisRules()
    manifest = Path(manifest_path)
    base_dir = manifest.parent
    cases: list[CaseAnalysis] = []
    seen: set[str] = set()

    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"case_id", "segmentation_path"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"Manifest is missing required column(s): {missing_text}")

        for row in reader:
            case_id = row["case_id"].strip()
            if not case_id:
                raise ValueError("Manifest contains an empty case_id.")
            if case_id in seen:
                raise ValueError(f"Manifest contains duplicate case_id: {case_id}")
            seen.add(case_id)

            path = Path(row["segmentation_path"].strip())
            if not path.is_absolute():
                path = base_dir / path
            try:
                report = analyze_cine_segmentation(
                    path,
                    case_id=case_id,
                    lv_label=_optional_int(row.get("lv_label"), 1),
                    rv_label=_optional_int(row.get("rv_label"), 2),
                    frame_time_ms=_optional_float(row.get("frame_time_ms")),
                    heart_rate_bpm=_optional_float(row.get("heart_rate_bpm")),
                    rules=active_rules,
                    include_hash=include_hash,
                )
            except Exception as exc:
                report = CaseAnalysis(
                    case_id=case_id,
                    status="error",
                    source_path=str(path),
                    shape=[],
                    frame_count=0,
                    voxel_volume_mm3=0.0,
                    frame_time_ms=None,
                    cycle_duration_ms=None,
                    heart_rate_bpm=None,
                    lv_label=_optional_int(row.get("lv_label"), 1),
                    rv_label=_optional_int(row.get("rv_label"), 2),
                    findings=[
                        Finding(
                            "case.processing_failed",
                            Severity.ERROR,
                            "Case could not be processed.",
                            {"exception_type": type(exc).__name__, "detail": str(exc)},
                        )
                    ],
                )
            cases.append(report)

    batch = BatchAnalysis(cases)
    write_batch_report(batch, output_dir, active_rules)
    return batch
