from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AnalysisRules:
    integer_tolerance: float = 1e-6
    min_frames: int = 8
    min_component_voxels: int = 8
    min_largest_component_fraction: float = 0.95
    max_relative_phase_jump: float = 0.35
    timing_disagreement_fraction: float = 0.10
    smoothing_window: int = 5
    smoothing_polyorder: int = 2
    use_smoothing_for_landmarks: bool = True
    warn_missing_qform_sform: bool = True

    def __post_init__(self) -> None:
        if self.min_frames < 2:
            raise ValueError("min_frames must be at least 2.")
        if not 0 < self.min_largest_component_fraction <= 1:
            raise ValueError("min_largest_component_fraction must be in (0, 1].")
        if self.max_relative_phase_jump <= 0:
            raise ValueError("max_relative_phase_jump must be positive.")
        if self.smoothing_window < 3 or self.smoothing_window % 2 == 0:
            raise ValueError("smoothing_window must be an odd integer >= 3.")
        if self.smoothing_polyorder < 1 or self.smoothing_polyorder >= self.smoothing_window:
            raise ValueError("smoothing_polyorder must be >= 1 and smaller than smoothing_window.")

    @classmethod
    def from_json(cls, path: str | Path) -> AnalysisRules:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Analysis rules JSON must contain an object at the top level.")
        allowed = set(asdict(cls()).keys())
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(f"Unknown analysis rule(s): {', '.join(unknown)}")
        return cls(**payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
