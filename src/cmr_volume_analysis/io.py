from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CineSegmentationRecord:
    path: Path
    data: np.ndarray
    affine: np.ndarray
    zooms: tuple[float, ...]
    axcodes: tuple[str, ...]
    qform_code: int
    sform_code: int
    frame_time_ms: float | None


def _temporal_zoom_ms(header: Any) -> float | None:
    zooms = header.get_zooms()
    if len(zooms) < 4 or zooms[3] <= 0:
        return None
    _, time_unit = header.get_xyzt_units()
    factor = {"sec": 1000.0, "msec": 1.0, "usec": 0.001}.get(time_unit)
    if factor is None:
        return None
    return float(zooms[3] * factor)


def load_cine_segmentation(path: str | Path) -> CineSegmentationRecord:
    try:
        import nibabel as nib
    except ImportError as exc:  # pragma: no cover - package dependency
        raise ImportError("nibabel is required to load NIfTI files.") from exc

    target = Path(path)
    image = nib.load(str(target))
    data = np.asanyarray(image.dataobj)
    header = image.header
    affine = np.asarray(image.affine, dtype=float)
    zooms = tuple(float(value) for value in header.get_zooms())
    axcodes = tuple(str(value) for value in nib.aff2axcodes(affine))
    qform_code = int(header["qform_code"])
    sform_code = int(header["sform_code"])
    return CineSegmentationRecord(
        path=target,
        data=data,
        affine=affine,
        zooms=zooms,
        axcodes=axcodes,
        qform_code=qform_code,
        sform_code=sform_code,
        frame_time_ms=_temporal_zoom_ms(header),
    )
