import pytest

from cmr_volume_analysis.batch import run_batch
from cmr_volume_analysis.synthetic import create_demo_dataset

nib = pytest.importorskip("nibabel")


def test_batch_demo_runs_and_isolates_error_case(tmp_path):
    manifest = create_demo_dataset(tmp_path / "demo")
    output = tmp_path / "report"
    batch = run_batch(manifest, output, include_hash=True)
    assert batch.total_cases == 4
    assert batch.error_cases >= 1
    assert (output / "summary.csv").exists()
    assert (output / "phase_volumes.csv").exists()
    assert (output / "index.html").exists()


def test_batch_rejects_duplicate_case_ids(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "case_id,segmentation_path\ncase,data/a.nii.gz\ncase,data/b.nii.gz\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case_id"):
        run_batch(manifest, tmp_path / "report")
