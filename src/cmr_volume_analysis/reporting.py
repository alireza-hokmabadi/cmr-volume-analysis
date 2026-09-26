from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from .models import BatchAnalysis, CaseAnalysis
from .plotting import plot_case_analysis
from .rules import AnalysisRules
from .version import __version__


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_case_json(report: CaseAnalysis, path: str | Path) -> None:
    _write_json(
        Path(path),
        {"software": {"name": "cmr-volume-analysis", "version": __version__}, **report.to_dict()},
    )


def _metric_value(case: CaseAnalysis, chamber: str, field: str) -> float | int | str:
    item = case.metrics.get(chamber)
    return getattr(item, field) if item is not None else ""


def _write_summary_csv(batch: BatchAnalysis, path: Path) -> None:
    metric_fields = ["edv_ml", "esv_ml", "stroke_volume_ml", "ejection_fraction_percent"]
    fields = ["case_id", "status", "frame_count", "frame_time_ms", "heart_rate_bpm"]
    fields += [f"{chamber}_{field}" for chamber in ("lv", "rv") for field in metric_fields]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in batch.cases:
            row: dict[str, object] = {
                "case_id": case.case_id,
                "status": case.status,
                "frame_count": case.frame_count,
                "frame_time_ms": case.frame_time_ms if case.frame_time_ms is not None else "",
                "heart_rate_bpm": case.heart_rate_bpm if case.heart_rate_bpm is not None else "",
            }
            for chamber in ("lv", "rv"):
                for field in metric_fields:
                    row[f"{chamber}_{field}"] = _metric_value(case, chamber, field)
            writer.writerow(row)


def _write_phase_csv(batch: BatchAnalysis, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "phase", "lv_ml", "rv_ml"])
        writer.writeheader()
        for case in batch.cases:
            lv = case.phase_volumes_ml.get("lv_ml", [])
            rv = case.phase_volumes_ml.get("rv_ml", [])
            n = max(len(lv), len(rv))
            for phase in range(n):
                writer.writerow(
                    {
                        "case_id": case.case_id,
                        "phase": phase,
                        "lv_ml": lv[phase] if phase < len(lv) else "",
                        "rv_ml": rv[phase] if phase < len(rv) else "",
                    }
                )


def _write_findings_jsonl(batch: BatchAnalysis, path: Path) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for case in batch.cases:
            for finding in case.findings:
                stream.write(
                    json.dumps(
                        {"case_id": case.case_id, **finding.to_dict()}, sort_keys=True
                    )
                    + "\n"
                )


def _html_report(batch: BatchAnalysis) -> str:
    rows: list[str] = []
    for case in batch.cases:
        lv = case.metrics.get("lv")
        rv = case.metrics.get("rv")
        plot_link = f"plots/{html.escape(case.case_id)}.png" if case.phase_volumes_ml else ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(case.case_id)}</td>"
            f"<td>{html.escape(case.status.upper())}</td>"
            f"<td>{'' if lv is None else f'{lv.edv_ml:.1f}'}</td>"
            f"<td>{'' if lv is None else f'{lv.esv_ml:.1f}'}</td>"
            f"<td>{'' if lv is None else f'{lv.ejection_fraction_percent:.1f}'}</td>"
            f"<td>{'' if rv is None else f'{rv.edv_ml:.1f}'}</td>"
            f"<td>{'' if rv is None else f'{rv.esv_ml:.1f}'}</td>"
            f"<td>{'' if rv is None else f'{rv.ejection_fraction_percent:.1f}'}</td>"
            f"<td>{f'<a href={chr(34)}{plot_link}{chr(34)}>curve</a>' if plot_link else ''}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CMR Volume Analysis</title>
<style>
body {{
  font-family: system-ui, sans-serif; max-width: 1200px;
  margin: 2rem auto; padding: 0 1rem;
}}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #ddd; padding: .5rem; text-align: left; }}
.cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0 2rem; }}
.card {{ border: 1px solid #ddd; border-radius: .5rem; padding: .8rem 1rem; }}
</style>
</head>
<body>
<h1>CMR Volume Analysis</h1>
<div class="cards">
<div class="card">Cases<br><strong>{batch.total_cases}</strong></div>
<div class="card">Pass<br><strong>{batch.pass_cases}</strong></div>
<div class="card">Warnings<br><strong>{batch.warning_cases}</strong></div>
<div class="card">Errors<br><strong>{batch.error_cases}</strong></div>
</div>
<table>
<thead>
<tr>
<th>Case</th><th>Status</th><th>LV EDV</th><th>LV ESV</th><th>LV EF %</th>
<th>RV EDV</th><th>RV ESV</th><th>RV EF %</th><th>Plot</th>
</tr>
</thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>"""


def write_batch_report(batch: BatchAnalysis, output_dir: str | Path, rules: AnalysisRules) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    cases_dir = target / "cases"
    plots_dir = target / "plots"
    cases_dir.mkdir(exist_ok=True)
    plots_dir.mkdir(exist_ok=True)

    _write_json(
        target / "batch_report.json",
        {
            "software": {"name": "cmr-volume-analysis", "version": __version__},
            **batch.to_dict(),
            "rules": rules.to_dict(),
        },
    )
    _write_summary_csv(batch, target / "summary.csv")
    _write_phase_csv(batch, target / "phase_volumes.csv")
    _write_findings_jsonl(batch, target / "findings.jsonl")
    (target / "index.html").write_text(_html_report(batch), encoding="utf-8")

    for case in batch.cases:
        safe_name = "".join(
            char if char.isalnum() or char in "-_." else "_" for char in case.case_id
        )
        write_case_json(case, cases_dir / f"{safe_name}.json")
        if case.phase_volumes_ml:
            plot_case_analysis(case, plots_dir / f"{safe_name}.png")
