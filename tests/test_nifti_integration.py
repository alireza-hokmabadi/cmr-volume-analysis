import pytest

from cmr_volume_analysis.analysis import analyze_cine_segmentation
from cmr_volume_analysis.synthetic import create_demo_dataset, synthetic_cine_labelmap

nib = pytest.importorskip("nibabel")


def test_analyze_nifti_reads_temporal_metadata(tmp_path):
    data, affine = synthetic_cine_labelmap()
    image = nib.Nifti1Image(data, affine)
    image.header.set_xyzt_units("mm", "msec")
    image.header.set_zooms((*image.header.get_zooms()[:3], 40.0))
    path = tmp_path / "cine.nii.gz"
    nib.save(image, path)

    report = analyze_cine_segmentation(path, include_hash=True)
    assert report.frame_time_ms == pytest.approx(40.0)
    assert report.heart_rate_bpm == pytest.approx(75.0)
    assert report.provenance is not None
    assert report.provenance.sha256 is not None


def test_demo_dataset_and_batch_manifest(tmp_path):
    manifest = create_demo_dataset(tmp_path)
    text = manifest.read_text(encoding="utf-8")
    assert "clean" in text
    assert "fragmented" in text
    assert "abrupt_jump" in text
    assert "missing_rv" in text
