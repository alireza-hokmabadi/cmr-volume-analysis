import numpy as np
import pytest

from cmr_volume_analysis.synthetic import synthetic_cine_labelmap


def test_synthetic_generator_shapes_and_labels():
    data, affine = synthetic_cine_labelmap()
    assert data.shape == (112, 96, 12, 20)
    assert affine.shape == (4, 4)
    assert set(np.unique(data)) == {0, 1, 2}


def test_synthetic_modes():
    fragmented, _ = synthetic_cine_labelmap(mode="fragmented")
    abrupt, _ = synthetic_cine_labelmap(mode="abrupt_jump")
    missing, _ = synthetic_cine_labelmap(mode="missing_rv")
    assert fragmented[4:6, 4:6, 2:4, 5].sum() > 0
    assert np.count_nonzero(abrupt[..., 6] == 1) > np.count_nonzero(abrupt[..., 5] == 1)
    assert 2 not in np.unique(missing)


def test_synthetic_rejects_bad_mode_and_short_sequence():
    with pytest.raises(ValueError):
        synthetic_cine_labelmap(mode="unknown")
    with pytest.raises(ValueError):
        synthetic_cine_labelmap(shape=(20, 20, 4, 4))
