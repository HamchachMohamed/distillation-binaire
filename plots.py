<<<<<<< HEAD
"""Fonctions de visualisation et export PNG des résultats."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
=======
"""Figures Matplotlib indépendantes et export PNG des résultats.

Les figures restent ouvertes jusqu'à l'appel unique de ``show_figures`` : Matplotlib
les affiche alors dans des fenêtres séparées avec sa barre d'outils native.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
>>>>>>> d83d00c (Initial commit)
import numpy as np

from equilibrium import EquilibriumCurve
from mccabe_thiele import McCabeThieleResult


<<<<<<< HEAD
def _save(fig: plt.Figure, output: Path, name: str, show: bool = False) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    target = output / name
    fig.savefig(target, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    return target


def plot_txy(curve: EquilibriumCurve, z_feed: float, output: Path, show: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5.5))
=======
def configure_backend(backend: str | None) -> None:
    """Sélectionne un backend GUI optionnel avant l'import de pyplot."""
    if backend:
        matplotlib.use(backend, force=True)


def _pyplot():
    # Import différé : --backend TkAgg/QtAgg peut donc être appliqué par main.py.
    import matplotlib.pyplot as plt
    return plt


def gui_backend_available() -> tuple[bool, str]:
    """Indique si le backend courant peut créer une fenêtre interactive."""
    backend = matplotlib.get_backend()
    non_gui = {"agg", "pdf", "ps", "svg", "cairo", "pgf", "template",
               "module://matplotlib_inline.backend_inline"}
    return backend.lower() not in non_gui, backend


def _save(fig: Any, output: Path, name: str) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    target = output / name
    fig.savefig(target, dpi=300, bbox_inches="tight")
    return target


def plot_txy(curve: EquilibriumCurve, z_feed: float, output: Path) -> tuple[Path, Any]:
    plt = _pyplot()
    fig, ax = plt.subplots(num="Diagramme T-x-y eau-éthanol", figsize=(8, 5.5))
>>>>>>> d83d00c (Initial commit)
    ax.plot(curve.x_ethanol, curve.temperature_C, label="Courbe de bulle (liquide x)", lw=2)
    ax.plot(curve.y_ethanol, curve.temperature_C, label="Courbe de rosée (vapeur y)", lw=2)
    T_feed = float(np.interp(z_feed, curve.x_ethanol, curve.temperature_C))
    ax.scatter([z_feed], [T_feed], c="black", zorder=3, label="Alimentation : x_E")
    ax.scatter([0, 1], [curve.temperature_C[0], curve.temperature_C[-1]], c="black", zorder=3)
    ax.annotate("Eau pure", (0, curve.temperature_C[0]), xytext=(7, 8), textcoords="offset points")
    ax.annotate("Éthanol pur", (1, curve.temperature_C[-1]), xytext=(-64, 8), textcoords="offset points")
    ax.set(xlim=(0, 1), xlabel="Fraction molaire d'éthanol (x ou y)", ylabel="Température (°C)",
           title="Diagramme isobare T-x-y eau–éthanol")
<<<<<<< HEAD
    ax.grid(alpha=.3); ax.legend()
    return _save(fig, output, "diagramme_Txy.png", show)


def plot_xy(curve: EquilibriumCurve, z_feed: float, y_feed: float, output: Path, show: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
=======
    ax.grid(alpha=.3)
    ax.legend()
    return _save(fig, output, "diagramme_Txy.png"), fig


def plot_xy(curve: EquilibriumCurve, z_feed: float, y_feed: float, output: Path) -> tuple[Path, Any]:
    plt = _pyplot()
    fig, ax = plt.subplots(num="Diagramme y-x eau-éthanol", figsize=(6.2, 6.2))
>>>>>>> d83d00c (Initial commit)
    ax.plot(curve.x_ethanol, curve.y_ethanol, label="Équilibre ELV (NRTL)", lw=2)
    ax.plot([0, 1], [0, 1], "k--", label="Diagonale y = x")
    ax.scatter([z_feed], [y_feed], c="black", zorder=3, label="Vapeur en équilibre avec l'alimentation")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="x_E, liquide", ylabel="y_E, vapeur",
           title="Diagramme d'équilibre y-x eau–éthanol")
<<<<<<< HEAD
    ax.grid(alpha=.3); ax.legend()
    return _save(fig, output, "diagramme_yx.png", show)


def plot_mccabe_thiele(curve: EquilibriumCurve, result: McCabeThieleResult,
                        x_D: float, x_B: float, z_F: float, q: float, output: Path,
                        show: bool = False) -> Path:
    fig, ax = plt.subplots(figsize=(7, 7))
=======
    ax.grid(alpha=.3)
    ax.legend()
    return _save(fig, output, "diagramme_yx.png"), fig


def plot_mccabe_thiele(curve: EquilibriumCurve, result: McCabeThieleResult,
                        x_D: float, x_B: float, z_F: float, q: float,
                        output: Path) -> tuple[Path, Any]:
    plt = _pyplot()
    fig, ax = plt.subplots(num="McCabe–Thiele eau-éthanol", figsize=(7, 7))
>>>>>>> d83d00c (Initial commit)
    x = np.linspace(0, 1, 500)
    ax.plot(curve.x_ethanol, curve.y_ethanol, lw=2, label="Équilibre ELV")
    ax.plot(x, x, "k--", label="Diagonale")
    ax.plot(x, result.rectifying_slope * x + result.rectifying_intercept, label="Enrichissement")
    ax.plot(x, result.stripping_slope * x + result.stripping_intercept, label="Appauvrissement")
    if abs(q - 1) < 1e-12:
        ax.axvline(z_F, color="tab:purple", label="q-line (q=1)")
    else:
        ax.plot(x, q / (q - 1) * x - z_F / (q - 1), color="tab:purple", label="q-line")
    px, py = zip(*result.stage_points)
    ax.plot(px, py, color="tab:red", lw=1.4, label=f"Marches : {result.stages_including_reboiler} étages")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="x_E, liquide", ylabel="y_E, vapeur",
           title="McCabe–Thiele eau–éthanol")
<<<<<<< HEAD
    ax.grid(alpha=.3); ax.legend(fontsize=8)
    return _save(fig, output, "mccabe_thiele.png", show)
=======
    ax.grid(alpha=.3)
    ax.legend(fontsize=8)
    return _save(fig, output, "mccabe_thiele.png"), fig


def finish_figures(figures: list[Any], show: bool) -> tuple[bool, str]:
    """Ouvre simultanément toutes les fenêtres GUI ou libère les figures exportées."""
    plt = _pyplot()
    gui_available, backend = gui_backend_available()
    if show and gui_available:
        # Un seul show() laisse vivre toutes les figures : une fenêtre par figure.
        plt.show()
        shown = True
    else:
        shown = False
    for fig in figures:
        plt.close(fig)
    return shown, backend
>>>>>>> d83d00c (Initial commit)
