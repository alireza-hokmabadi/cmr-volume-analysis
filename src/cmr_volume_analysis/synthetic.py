from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def synthetic_cine_labelmap(
    *,
    shape: tuple[int, int, int, int] = (112, 96, 12, 20),
    mode: str = "clean",
) -> tuple[np.ndarray, np.ndarray]:
    if len(shape) != 4 or shape[-1] < 8:
        raise ValueError("Synthetic shape must be 4D with at least 8 phases.")
    x, y, z = np.indices(shape[:3])
    data = np.zeros(shape, dtype=np.uint8)

    for phase in range(shape[-1]):
        theta = 2.0 * np.pi * phase / shape[-1]
        filling = (1.0 + np.cos(theta)) / 2.0
        lv_scale = 0.82 + 0.18 * filling
        rv_scale = 0.80 + 0.20 * filling

        lv = (
            ((x - 34.0) / (20.0 * lv_scale)) ** 2
            + ((y - 48.0) / (16.0 * lv_scale)) ** 2
            + ((z - 5.5) / (4.2 * lv_scale)) ** 2
            <= 1.0
        )
        rv = (
            ((x - 76.0) / (19.0 * rv_scale)) ** 2
            + ((y - 48.0) / (14.0 * rv_scale)) ** 2
            + ((z - 5.5) / (4.0 * rv_scale)) ** 2
            <= 1.0
        )
        data[..., phase][lv] = 1
        data[..., phase][rv & ~lv] = 2

    if mode == "fragmented":
        data[4:6, 4:6, 2:3, 5] = 1
    elif mode == "abrupt_jump":
        phase = 6
        scale = 1.20
        enlarged = (
            ((x - 34.0) / (20.0 * scale)) ** 2
            + ((y - 48.0) / (16.0 * scale)) ** 2
            + ((z - 5.5) / (4.2 * scale)) ** 2
            <= 1.0
        )
        data[..., phase][data[..., phase] == 1] = 0
        data[..., phase][enlarged & (data[..., phase] == 0)] = 1
    elif mode == "missing_rv":
        data[data == 2] = 0
    elif mode != "clean":
        raise ValueError(f"Unknown synthetic mode: {mode}")

    affine = np.diag([1.5, 1.5, 8.0, 1.0]).astype(float)
    return data, affine


def create_demo_dataset(output_dir: str | Path) -> Path:
    try:
        import nibabel as nib
    except ImportError as exc:  # pragma: no cover - package dependency
        raise ImportError("nibabel is required to write the synthetic demo.") from exc

    target = Path(output_dir)
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for mode in ("clean", "fragmented", "abrupt_jump", "missing_rv"):
        data, affine = synthetic_cine_labelmap(mode=mode)
        image = nib.Nifti1Image(data, affine)
        image.header.set_xyzt_units("mm", "msec")
        image.header.set_zooms((*image.header.get_zooms()[:3], 50.0))
        path = data_dir / f"{mode}.nii.gz"
        nib.save(image, path)
        rows.append(
            {
                "case_id": mode,
                "segmentation_path": f"data/{path.name}",
                "lv_label": "1",
                "rv_label": "2",
                "frame_time_ms": "50",
                "heart_rate_bpm": "60",
            }
        )

    manifest = target / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return manifest
