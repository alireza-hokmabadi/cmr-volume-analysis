# Design notes

## Scope

`cmr-volume-analysis` performs transparent quantitative analysis of phase-resolved cine-CMR segmentation label maps. It does not perform segmentation and does not determine whether a result is clinically normal or abnormal.

## Measurement model

Volumes are calculated from label voxel counts multiplied by the physical voxel volume derived from `abs(det(affine[:3, :3]))`. This remains correct for rotated and sheared voxel bases and avoids assuming an axis-aligned affine.

## Landmark selection

End diastole (ED) and end systole (ES) are selected as the maximum and minimum of the ventricular volume curve. Optional cyclic Savitzky-Golay smoothing can be used only to select the frame indices. EDV and ESV are always read from the original unsmoothed measurements at the selected frames.

## Timing

Frame time may be supplied directly, read from NIfTI temporal metadata, or inferred from heart rate assuming the 4D sequence spans one cardiac cycle. When both frame time and heart rate are available, disagreement is reported rather than silently reconciled.

## QA philosophy

The package checks technical properties that can be evaluated deterministically: label-map validity, missing phases, fragmentation, abrupt phase-to-phase volume changes, timing consistency, and metadata issues. It intentionally avoids hard-coded clinical normal ranges because those depend on population, acquisition, segmentation convention, indexing method, and clinical context.

## Reproducibility

Structured reports include software version, QA rules, input metadata, optional SHA-256 hashes, raw phase-volume curves, selected landmarks, and derived metrics.
