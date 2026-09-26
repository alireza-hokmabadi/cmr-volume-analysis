from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .models import CaseAnalysis


def plot_case_analysis(report: CaseAnalysis, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    plotted = False
    for name, display in (("lv", "LV"), ("rv", "RV")):
        curve = report.phase_volumes_ml.get(f"{name}_ml")
        if not curve:
            continue
        phases = np.arange(len(curve))
        line = ax.plot(phases, curve, marker="o", markersize=3, label=display)[0]
        selection = report.landmarks.get(name)
        if selection is not None:
            ax.scatter(
                [selection.ed_frame, selection.es_frame],
                [curve[selection.ed_frame], curve[selection.es_frame]],
                marker="x",
                s=55,
                color=line.get_color(),
            )
        plotted = True

    ax.set_title(f"Phase-resolved ventricular volumes — {report.case_id}")
    ax.set_xlabel("Cardiac phase")
    ax.set_ylabel("Volume (mL)")
    ax.grid(True, alpha=0.2)
    if plotted:
        ax.legend()
    fig.tight_layout()
    fig.savefig(target, dpi=160)
    plt.close(fig)
