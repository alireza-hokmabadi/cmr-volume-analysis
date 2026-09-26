from __future__ import annotations

import numpy as np

from .models import LandmarkSelection, VentricularMetrics


def _cyclic_edges(start: int, end: int, n: int) -> list[int]:
    edges: list[int] = []
    index = start
    while index != end:
        edges.append(index)
        index = (index + 1) % n
        if len(edges) > n:
            raise RuntimeError("Could not resolve cyclic phase interval.")
    return edges


def derive_ventricular_metrics(
    curve_ml: np.ndarray,
    label: int,
    landmarks: LandmarkSelection,
    frame_time_ms: float | None = None,
    heart_rate_bpm: float | None = None,
) -> VentricularMetrics:
    curve = np.asarray(curve_ml, dtype=float)
    if curve.ndim != 1 or len(curve) < 2:
        raise ValueError("Volume curve must contain at least two phases.")

    ed = landmarks.ed_frame
    es = landmarks.es_frame
    edv = float(curve[ed])
    esv = float(curve[es])
    sv = edv - esv
    ef = float(100.0 * sv / edv) if edv > 0 else 0.0

    resolved_frame_time = frame_time_ms
    if resolved_frame_time is None and heart_rate_bpm is not None and heart_rate_bpm > 0:
        resolved_frame_time = 60000.0 / (heart_rate_bpm * len(curve))

    ed_to_es_ms: float | None = None
    peak_ejection: float | None = None
    peak_filling: float | None = None
    if resolved_frame_time is not None and resolved_frame_time > 0 and ed != es:
        dt_s = resolved_frame_time / 1000.0
        forward_rate = (np.roll(curve, -1) - curve) / dt_s
        systolic_edges = _cyclic_edges(ed, es, len(curve))
        diastolic_edges = _cyclic_edges(es, ed, len(curve))
        ed_to_es_ms = float(len(systolic_edges) * resolved_frame_time)
        if systolic_edges:
            peak_ejection = float(max(0.0, -np.min(forward_rate[systolic_edges])))
        if diastolic_edges:
            peak_filling = float(max(0.0, np.max(forward_rate[diastolic_edges])))

    cardiac_output = None
    if heart_rate_bpm is not None and heart_rate_bpm > 0:
        cardiac_output = float(sv * heart_rate_bpm / 1000.0)

    return VentricularMetrics(
        label=label,
        ed_frame=ed,
        es_frame=es,
        edv_ml=edv,
        esv_ml=esv,
        stroke_volume_ml=sv,
        ejection_fraction_percent=ef,
        ed_to_es_ms=ed_to_es_ms,
        peak_ejection_rate_ml_s=peak_ejection,
        peak_filling_rate_ml_s=peak_filling,
        cardiac_output_l_min=cardiac_output,
    )
