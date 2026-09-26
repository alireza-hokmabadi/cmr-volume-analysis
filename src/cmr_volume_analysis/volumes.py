from __future__ import annotations

import numpy as np


def voxel_volume_mm3(affine: np.ndarray) -> float:
    matrix = np.asarray(affine, dtype=float)
    if matrix.shape != (4, 4):
        raise ValueError("Affine must have shape (4, 4).")
    value = float(abs(np.linalg.det(matrix[:3, :3])))
    if not np.isfinite(value) or value <= 0:
        raise ValueError("Affine does not define a positive finite voxel volume.")
    return value


def label_volume_curve_ml(
    labels_4d: np.ndarray,
    label: int,
    voxel_volume: float,
) -> np.ndarray:
    data = np.asarray(labels_4d)
    if data.ndim != 4:
        raise ValueError("Expected a 4D label map with shape (X, Y, Z, phase).")
    if voxel_volume <= 0:
        raise ValueError("voxel_volume must be positive.")
    counts = np.count_nonzero(data == label, axis=(0, 1, 2))
    return counts.astype(float) * float(voxel_volume) / 1000.0
