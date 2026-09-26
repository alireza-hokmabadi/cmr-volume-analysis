from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True)
class FileProvenance:
    path: str
    size_bytes: int
    mtime_ns: int
    sha256: str | None = None


@dataclass(frozen=True)
class LandmarkSelection:
    ed_frame: int
    es_frame: int
    used_smoothed_curve: bool
    selection_curve_ml: list[float]


@dataclass(frozen=True)
class VentricularMetrics:
    label: int
    ed_frame: int
    es_frame: int
    edv_ml: float
    esv_ml: float
    stroke_volume_ml: float
    ejection_fraction_percent: float
    ed_to_es_ms: float | None = None
    peak_ejection_rate_ml_s: float | None = None
    peak_filling_rate_ml_s: float | None = None
    cardiac_output_l_min: float | None = None


@dataclass
class CaseAnalysis:
    case_id: str
    status: str
    source_path: str | None
    shape: list[int]
    frame_count: int
    voxel_volume_mm3: float
    frame_time_ms: float | None
    cycle_duration_ms: float | None
    heart_rate_bpm: float | None
    lv_label: int
    rv_label: int
    phase_volumes_ml: dict[str, list[float]] = field(default_factory=dict)
    landmarks: dict[str, LandmarkSelection] = field(default_factory=dict)
    metrics: dict[str, VentricularMetrics] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    provenance: FileProvenance | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "status": self.status,
            "source_path": self.source_path,
            "shape": self.shape,
            "frame_count": self.frame_count,
            "voxel_volume_mm3": self.voxel_volume_mm3,
            "frame_time_ms": self.frame_time_ms,
            "cycle_duration_ms": self.cycle_duration_ms,
            "heart_rate_bpm": self.heart_rate_bpm,
            "lv_label": self.lv_label,
            "rv_label": self.rv_label,
            "phase_volumes_ml": self.phase_volumes_ml,
            "landmarks": {key: asdict(value) for key, value in self.landmarks.items()},
            "metrics": {key: asdict(value) for key, value in self.metrics.items()},
            "findings": [item.to_dict() for item in self.findings],
            "provenance": asdict(self.provenance) if self.provenance is not None else None,
        }


@dataclass
class BatchAnalysis:
    cases: list[CaseAnalysis]

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def pass_cases(self) -> int:
        return sum(case.status == "pass" for case in self.cases)

    @property
    def warning_cases(self) -> int:
        return sum(case.status == "warning" for case in self.cases)

    @property
    def error_cases(self) -> int:
        return sum(case.status == "error" for case in self.cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_cases": self.total_cases,
                "pass_cases": self.pass_cases,
                "warning_cases": self.warning_cases,
                "error_cases": self.error_cases,
            },
            "cases": [case.to_dict() for case in self.cases],
        }


def status_from_findings(findings: list[Finding]) -> str:
    if any(item.severity == Severity.ERROR for item in findings):
        return "error"
    if any(item.severity == Severity.WARNING for item in findings):
        return "warning"
    return "pass"
