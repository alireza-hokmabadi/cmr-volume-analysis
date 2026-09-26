from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .analysis import analyze_cine_segmentation
from .batch import run_batch
from .plotting import plot_case_analysis
from .reporting import write_case_json
from .rules import AnalysisRules
from .synthetic import create_demo_dataset
from .version import __version__

app = typer.Typer(
    no_args_is_help=True,
    help="Phase-resolved ventricular volume analysis for cine CMR.",
)
console = Console()


class FailOn(str, Enum):
    NEVER = "never"
    WARNING = "warning"
    ERROR = "error"


def _rules(config: Path | None) -> AnalysisRules:
    return AnalysisRules.from_json(config) if config is not None else AnalysisRules()


def _exit_code(status: str, fail_on: FailOn) -> int:
    if fail_on == FailOn.NEVER:
        return 0
    if fail_on == FailOn.WARNING and status in {"warning", "error"}:
        return 2
    if fail_on == FailOn.ERROR and status == "error":
        return 2
    return 0


def _render_case(report) -> None:
    console.print(
        f"[bold]Case:[/bold] {report.case_id}  "
        f"[bold]Status:[/bold] {report.status.upper()}"
    )
    table = Table("Chamber", "ED frame", "ES frame", "EDV mL", "ESV mL", "SV mL", "EF %")
    for chamber in ("lv", "rv"):
        item = report.metrics.get(chamber)
        if item is not None:
            table.add_row(
                chamber.upper(),
                str(item.ed_frame),
                str(item.es_frame),
                f"{item.edv_ml:.2f}",
                f"{item.esv_ml:.2f}",
                f"{item.stroke_volume_ml:.2f}",
                f"{item.ejection_fraction_percent:.2f}",
            )
    console.print(table)
    if report.findings:
        findings = Table("Severity", "Code", "Message")
        for item in report.findings:
            findings.add_row(item.severity.value, item.code, item.message)
        console.print(findings)


@app.command("analyze")
def analyze_command(
    segmentation: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    case_id: Annotated[str | None, typer.Option()] = None,
    lv_label: Annotated[int, typer.Option()] = 1,
    rv_label: Annotated[int, typer.Option()] = 2,
    frame_time_ms: Annotated[float | None, typer.Option()] = None,
    heart_rate_bpm: Annotated[float | None, typer.Option()] = None,
    config: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    hash_file: Annotated[bool, typer.Option()] = False,
    json_out: Annotated[Path | None, typer.Option()] = None,
    plot_out: Annotated[Path | None, typer.Option()] = None,
    fail_on: Annotated[FailOn, typer.Option()] = FailOn.ERROR,
) -> None:
    report = analyze_cine_segmentation(
        segmentation,
        case_id=case_id,
        lv_label=lv_label,
        rv_label=rv_label,
        frame_time_ms=frame_time_ms,
        heart_rate_bpm=heart_rate_bpm,
        rules=_rules(config),
        include_hash=hash_file,
    )
    _render_case(report)
    if json_out is not None:
        write_case_json(report, json_out)
    if plot_out is not None and report.phase_volumes_ml:
        plot_case_analysis(report, plot_out)
    raise typer.Exit(_exit_code(report.status, fail_on))


@app.command("batch")
def batch_command(
    manifest: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output_dir: Annotated[Path, typer.Option("--output-dir", "-o")],
    config: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    hash_files: Annotated[bool, typer.Option()] = False,
    fail_on: Annotated[FailOn, typer.Option()] = FailOn.ERROR,
) -> None:
    batch = run_batch(manifest, output_dir, rules=_rules(config), include_hash=hash_files)
    console.print(
        f"Processed {batch.total_cases} case(s): {batch.pass_cases} pass, "
        f"{batch.warning_cases} warning, {batch.error_cases} error."
    )
    aggregate = "error" if batch.error_cases else "warning" if batch.warning_cases else "pass"
    raise typer.Exit(_exit_code(aggregate, fail_on))


@app.command("demo")
def demo_command(output_dir: Annotated[Path, typer.Argument()]) -> None:
    manifest = create_demo_dataset(output_dir)
    report_dir = output_dir / "analysis_report"
    batch = run_batch(manifest, report_dir)
    console.print(json.dumps(batch.to_dict()["summary"], indent=2))
    console.print(f"Open {report_dir / 'index.html'}")


@app.command("version")
def version_command() -> None:
    console.print(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
