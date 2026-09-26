from cmr_volume_analysis import AnalysisRules, analyze_cine_segmentation

report = analyze_cine_segmentation(
    "cine_segmentation.nii.gz",
    lv_label=1,
    rv_label=2,
    heart_rate_bpm=72,
    rules=AnalysisRules(max_relative_phase_jump=0.30),
)

for chamber, metrics in report.metrics.items():
    print(
        chamber.upper(),
        f"EDV={metrics.edv_ml:.1f} mL",
        f"ESV={metrics.esv_ml:.1f} mL",
        f"SV={metrics.stroke_volume_ml:.1f} mL",
        f"EF={metrics.ejection_fraction_percent:.1f}%",
    )
