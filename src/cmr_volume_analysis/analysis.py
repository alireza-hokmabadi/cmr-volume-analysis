from __future__ import annotations

from pathlib import Path

import numpy as np

from .io import load_cine_segmentation
from .landmarks import detect_landmarks
from .metrics import derive_ventricular_metrics
from .models import (
    CaseAnalysis,
    Finding,
    LandmarkSelection,
    Severity,
    VentricularMetrics,
    status_from_findings,
)
from .provenance import file_provenance
from .qc import component_findings, curve_findings, timing_findings, validate_labelmap
from .rules import AnalysisRules
from .volumes import label_volume_curve_ml, voxel_volume_mm3


def _resolve_timing(
    frame_count: int,
    frame_time_ms: float | None,
    heart_rate_bpm: float | None,
) -> tuple[float | None, float | None, float | None]:
    resolved_frame_time = frame_time_ms
    resolved_hr = heart_rate_bpm
    if resolved_frame_time is None and resolved_hr is not None and resolved_hr > 0:
        resolved_frame_time = 60000.0 / (resolved_hr * frame_count)
    if resolved_hr is None and resolved_frame_time is not None and resolved_frame_time > 0:
        resolved_hr = 60000.0 / (resolved_frame_time * frame_count)
    cycle_duration = (
        resolved_frame_time * frame_count
        if resolved_frame_time is not None and resolved_frame_time > 0
        else None
    )
    return resolved_frame_time, resolved_hr, cycle_duration


def analyze_label_array(
    labels_4d: np.ndarray,
    affine: np.ndarray,
    *,
    case_id: str = "case",
    source_path: str | None = None,
    lv_label: int = 1,
    rv_label: int = 2,
    frame_time_ms: float | None = None,
    heart_rate_bpm: float | None = None,
    rules: AnalysisRules | None = None,
) -> CaseAnalysis:
    active_rules = rules or AnalysisRules()
    data = np.asarray(labels_4d)
    findings = validate_labelmap(data, {"lv": lv_label, "rv": rv_label}, active_rules)

    try:
        voxel_volume = voxel_volume_mm3(np.asarray(affine, dtype=float))
    except ValueError as exc:
        findings.append(Finding("geometry.invalid_affine", Severity.ERROR, str(exc)))
        voxel_volume = 0.0

    frame_count = int(data.shape[-1]) if data.ndim == 4 else 0
    resolved_frame_time, resolved_hr, cycle_duration = _resolve_timing(
        frame_count, frame_time_ms, heart_rate_bpm
    ) if frame_count else (frame_time_ms, heart_rate_bpm, None)
    if frame_count:
        findings.extend(
            timing_findings(frame_count, frame_time_ms, heart_rate_bpm, active_rules)
        )

    phase_volumes: dict[str, list[float]] = {}
    landmarks: dict[str, LandmarkSelection] = {}
    metrics: dict[str, VentricularMetrics] = {}
    blocking = any(item.severity == Severity.ERROR for item in findings)
    if not blocking:
        rounded = np.rint(data).astype(np.int64, copy=False)
        for structure_name, label in (("lv", lv_label), ("rv", rv_label)):
            curve = label_volume_curve_ml(rounded, label, voxel_volume)
            phase_volumes[f"{structure_name}_ml"] = curve.tolist()
            findings.extend(component_findings(rounded, label, structure_name, active_rules))
            curve_issues = curve_findings(curve, structure_name, active_rules)
            findings.extend(curve_issues)
            if any(item.severity == Severity.ERROR for item in curve_issues):
                continue
            selection = detect_landmarks(curve, active_rules)
            landmarks[structure_name] = selection
            metrics[structure_name] = derive_ventricular_metrics(
                curve,
                label,
                selection,
                frame_time_ms=resolved_frame_time,
                heart_rate_bpm=resolved_hr,
            )

    return CaseAnalysis(
        case_id=case_id,
        status=status_from_findings(findings),
        source_path=source_path,
        shape=list(data.shape),
        frame_count=frame_count,
        voxel_volume_mm3=voxel_volume,
        frame_time_ms=resolved_frame_time,
        cycle_duration_ms=cycle_duration,
        heart_rate_bpm=resolved_hr,
        lv_label=lv_label,
        rv_label=rv_label,
        phase_volumes_ml=phase_volumes,
        landmarks=landmarks,
        metrics=metrics,
        findings=findings,
    )


def analyze_cine_segmentation(
    path: str | Path,
    *,
    case_id: str | None = None,
    lv_label: int = 1,
    rv_label: int = 2,
    frame_time_ms: float | None = None,
    heart_rate_bpm: float | None = None,
    rules: AnalysisRules | None = None,
    include_hash: bool = False,
) -> CaseAnalysis:
    active_rules = rules or AnalysisRules()
    record = load_cine_segmentation(path)
    timing = frame_time_ms if frame_time_ms is not None else record.frame_time_ms
    report = analyze_label_array(
        record.data,
        record.affine,
        case_id=case_id or record.path.stem,
        source_path=str(record.path),
        lv_label=lv_label,
        rv_label=rv_label,
        frame_time_ms=timing,
        heart_rate_bpm=heart_rate_bpm,
        rules=active_rules,
    )
    if active_rules.warn_missing_qform_sform and record.qform_code == 0 and record.sform_code == 0:
        report.findings.append(
            Finding(
                "metadata.missing_qform_sform",
                Severity.WARNING,
                "NIfTI header has neither qform nor sform code set.",
            )
        )
        report.status = status_from_findings(report.findings)
    report.provenance = file_provenance(record.path, include_hash)
    return report
