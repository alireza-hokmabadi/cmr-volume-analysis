from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

from .models import LandmarkSelection
from .rules import AnalysisRules


def cyclic_smooth_curve(curve_ml: np.ndarray, window: int, polyorder: int) -> np.ndarray:
    curve = np.asarray(curve_ml, dtype=float)
    if curve.ndim != 1:
        raise ValueError("Volume curve must be one-dimensional.")
    if len(curve) < window:
        return curve.copy()
    return np.asarray(
        savgol_filter(curve, window_length=window, polyorder=polyorder, mode="wrap"),
        dtype=float,
    )


def detect_landmarks(curve_ml: np.ndarray, rules: AnalysisRules | None = None) -> LandmarkSelection:
    active_rules = rules or AnalysisRules()
    curve = np.asarray(curve_ml, dtype=float)
    if curve.ndim != 1 or len(curve) < 2:
        raise ValueError("Volume curve must contain at least two phases.")
    if not np.all(np.isfinite(curve)):
        raise ValueError("Volume curve contains non-finite values.")

    use_smoothing = (
        active_rules.use_smoothing_for_landmarks
        and len(curve) >= active_rules.smoothing_window
    )
    selection = (
        cyclic_smooth_curve(curve, active_rules.smoothing_window, active_rules.smoothing_polyorder)
        if use_smoothing
        else curve.copy()
    )
    ed_frame = int(np.argmax(selection))
    es_frame = int(np.argmin(selection))
    return LandmarkSelection(
        ed_frame=ed_frame,
        es_frame=es_frame,
        used_smoothed_curve=use_smoothing,
        selection_curve_ml=selection.tolist(),
    )
