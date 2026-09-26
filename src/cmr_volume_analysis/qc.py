from __future__ import annotations

import numpy as np
from scipy import ndimage

from .models import Finding, Severity
from .rules import AnalysisRules


def validate_labelmap(
    data: np.ndarray,
    expected_labels: dict[str, int],
    rules: AnalysisRules,
) -> list[Finding]:
    findings: list[Finding] = []
    array = np.asarray(data)
    if array.ndim != 4:
        return [
            Finding(
                "segmentation.not_4d",
                Severity.ERROR,
                "Segmentation must be a 4D cine label map with phases on the last axis.",
                {"shape": list(array.shape)},
            )
        ]
    if array.shape[-1] < rules.min_frames:
        findings.append(
            Finding(
                "segmentation.too_few_phases",
                Severity.WARNING,
                "Cine segmentation contains fewer phases than the configured QA threshold.",
                {"frame_count": int(array.shape[-1]), "minimum": rules.min_frames},
            )
        )
    finite = np.isfinite(array)
    if not np.all(finite):
        findings.append(
            Finding(
                "segmentation.nonfinite_values",
                Severity.ERROR,
                "Segmentation contains NaN or infinite values.",
                {"nonfinite_voxels": int(np.size(array) - np.count_nonzero(finite))},
            )
        )
        return findings
    rounded = np.rint(array)
    noninteger = np.abs(array - rounded) > rules.integer_tolerance
    if np.any(noninteger):
        findings.append(
            Finding(
                "segmentation.noninteger_labels",
                Severity.ERROR,
                "Segmentation contains non-integer label values.",
                {"voxel_count": int(np.count_nonzero(noninteger))},
            )
        )
    if np.any(array < 0):
        findings.append(
            Finding(
                "segmentation.negative_labels",
                Severity.ERROR,
                "Segmentation contains negative labels.",
            )
        )

    for name, label in expected_labels.items():
        if not np.any(rounded == label):
            findings.append(
                Finding(
                    "segmentation.missing_label",
                    Severity.ERROR,
                    f"Expected {name.upper()} label is absent from the complete cine segmentation.",
                    {"structure": name, "label": label},
                )
            )
    return findings


def component_findings(
    labels_4d: np.ndarray,
    label: int,
    structure_name: str,
    rules: AnalysisRules,
) -> list[Finding]:
    data = np.asarray(labels_4d)
    findings: list[Finding] = []
    bad_phases: list[dict[str, float | int]] = []
    small_component_phases: list[int] = []
    connectivity = ndimage.generate_binary_structure(3, 1)

    for phase in range(data.shape[-1]):
        mask = data[..., phase] == label
        total = int(np.count_nonzero(mask))
        if total == 0:
            continue
        component_map, count = ndimage.label(mask, structure=connectivity)
        if count <= 1:
            continue
        sizes = np.bincount(component_map.ravel())[1:]
        largest = int(sizes.max())
        fraction = largest / total
        if np.any(sizes < rules.min_component_voxels):
            small_component_phases.append(phase)
        if fraction < rules.min_largest_component_fraction:
            bad_phases.append(
                {
                    "phase": phase,
                    "component_count": int(count),
                    "largest_component_fraction": float(fraction),
                }
            )

    if bad_phases:
        findings.append(
            Finding(
                "segmentation.fragmented_label",
                Severity.WARNING,
                f"{structure_name.upper()} is substantially fragmented in one or more phases.",
                {"structure": structure_name, "label": label, "phases": bad_phases},
            )
        )
    if small_component_phases:
        findings.append(
            Finding(
                "segmentation.small_components",
                Severity.WARNING,
                f"{structure_name.upper()} contains small disconnected components.",
                {
                    "structure": structure_name,
                    "label": label,
                    "phases": sorted(set(small_component_phases)),
                    "minimum_component_voxels": rules.min_component_voxels,
                },
            )
        )
    return findings


def curve_findings(
    curve_ml: np.ndarray,
    structure_name: str,
    rules: AnalysisRules,
) -> list[Finding]:
    curve = np.asarray(curve_ml, dtype=float)
    findings: list[Finding] = []
    zero_phases = np.flatnonzero(curve <= 0).astype(int).tolist()
    if zero_phases:
        findings.append(
            Finding(
                "curve.empty_phase",
                Severity.ERROR,
                f"{structure_name.upper()} has zero measured volume in one or more phases.",
                {"structure": structure_name, "phases": zero_phases},
            )
        )
        return findings

    median = float(np.median(curve))
    if median > 0:
        cyclic_diff = np.abs(np.roll(curve, -1) - curve) / median
        bad_edges = np.flatnonzero(cyclic_diff > rules.max_relative_phase_jump).astype(int).tolist()
        if bad_edges:
            findings.append(
                Finding(
                    "curve.abrupt_phase_change",
                    Severity.WARNING,
                    f"{structure_name.upper()} volume changes abruptly between adjacent phases.",
                    {
                        "structure": structure_name,
                        "edge_start_phases": bad_edges,
                        "threshold": rules.max_relative_phase_jump,
                    },
                )
            )
    if float(np.ptp(curve)) <= max(1e-6, 1e-6 * float(np.max(curve))):
        findings.append(
            Finding(
                "curve.flat",
                Severity.WARNING,
                f"{structure_name.upper()} volume curve is effectively flat.",
                {"structure": structure_name},
            )
        )
    return findings


def timing_findings(
    frame_count: int,
    frame_time_ms: float | None,
    heart_rate_bpm: float | None,
    rules: AnalysisRules,
) -> list[Finding]:
    if frame_time_ms is None or heart_rate_bpm is None or frame_time_ms <= 0 or heart_rate_bpm <= 0:
        return []
    derived_hr = 60000.0 / (frame_time_ms * frame_count)
    relative = abs(derived_hr - heart_rate_bpm) / heart_rate_bpm
    if relative <= rules.timing_disagreement_fraction:
        return []
    return [
        Finding(
            "timing.heart_rate_disagreement",
            Severity.WARNING,
            (
                "Provided heart rate disagrees with the heart rate implied by frame time "
                "and phase count."
            ),
            {
                "provided_heart_rate_bpm": heart_rate_bpm,
                "implied_heart_rate_bpm": derived_hr,
                "relative_difference": relative,
            },
        )
    ]
