# Changelog

All notable changes to this project will be documented here.

## [0.1.0] - 2026-09-25

### Added

- 4D NIfTI cine segmentation analysis for LV and RV blood-pool labels.
- Phase-wise physical volumes derived from the full affine voxel volume.
- ED/ES landmark detection with optional cyclic Savitzky-Golay smoothing.
- EDV, ESV, stroke volume, ejection fraction, cardiac output, and peak rate metrics.
- Temporal metadata resolution from NIfTI headers, frame time, or heart rate.
- Segmentation, component, curve, timing, and geometry QA findings.
- Batch manifest processing with per-case failure isolation.
- JSON, CSV, JSONL, HTML, and PNG reporting.
- Fully synthetic cine-CMR demo generator.
- CLI, Python API, tests, coverage gate, static typing, linting, and multi-version CI.
