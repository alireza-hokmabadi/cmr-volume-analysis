import numpy as np
import pytest

from cmr_volume_analysis.volumes import label_volume_curve_ml, voxel_volume_mm3


def test_voxel_volume_uses_affine_determinant():
    affine = np.eye(4)
    affine[:3, :3] = np.array([[2.0, 0.5, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]])
    assert voxel_volume_mm3(affine) == pytest.approx(24.0)


def test_voxel_volume_rejects_bad_affine():
    with pytest.raises(ValueError):
        voxel_volume_mm3(np.eye(3))
    affine = np.eye(4)
    affine[2, 2] = 0
    with pytest.raises(ValueError):
        voxel_volume_mm3(affine)


def test_label_volume_curve():
    data = np.zeros((2, 2, 2, 3), dtype=np.uint8)
    data[..., 0].flat[:2] = 1
    data[..., 1].flat[:4] = 1
    data[..., 2].flat[:6] = 1
    curve = label_volume_curve_ml(data, 1, voxel_volume=10.0)
    assert np.allclose(curve, [0.02, 0.04, 0.06])


def test_label_volume_curve_requires_4d():
    with pytest.raises(ValueError):
        label_volume_curve_ml(np.zeros((2, 2, 2)), 1, 1.0)
