"""Bilans opérationnels et marches de McCabe--Thiele pour un binaire."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from equilibrium import EquilibriumCurve, x_at_equilibrium_y


@dataclass(frozen=True)
class McCabeThieleResult:
    stages_including_reboiler: int
    stage_points: list[tuple[float, float]]
    feed_intersection: tuple[float, float]
    rectifying_slope: float
    rectifying_intercept: float
    stripping_slope: float
    stripping_intercept: float


def _validate_specs(x_D: float, x_B: float, R: float, q: float, z_F: float) -> None:
    if not all(0.0 < value < 1.0 for value in (x_D, x_B, z_F)):
        raise ValueError("x_D, x_B et z_F doivent être strictement compris entre 0 et 1.")
    if not x_B < z_F < x_D:
        raise ValueError("Il faut x_B < z_F < x_D pour une séparation ordinaire.")
    if R <= 0:
        raise ValueError("Le taux de reflux R doit être strictement positif.")
    if not np.isfinite(q):
        raise ValueError("q doit être fini.")


def operating_lines(x_D: float, x_B: float, R: float, q: float, z_F: float) -> tuple[float, float, float, float, tuple[float, float]]:
    """Retourne droite d'enrichissement, d'appauvrissement et leur intersection."""
    _validate_specs(x_D, x_B, R, q, z_F)
    m_r, b_r = R / (R + 1.0), x_D / (R + 1.0)
    if abs(q - 1.0) < 1e-12:
        x_q = z_F
        y_q = m_r * x_q + b_r
    else:
        # q-line: y=q/(q-1)x-z_F/(q-1)
        m_q, b_q = q / (q - 1.0), -z_F / (q - 1.0)
        if abs(m_r - m_q) < 1e-12:
            raise ValueError("La q-line est parallèle à la droite d'enrichissement.")
        x_q = (b_q - b_r) / (m_r - m_q)
        y_q = m_r * x_q + b_r
    if not (x_B < x_q < x_D):
        raise ValueError("Intersection q-line/opératoire hors de la zone de séparation : R ou q incompatible.")
    m_s = (y_q - x_B) / (x_q - x_B)
    b_s = x_B * (1.0 - m_s)
    return m_r, b_r, m_s, b_s, (x_q, y_q)


def step_off_stages(curve: EquilibriumCurve, x_D: float, x_B: float, R: float,
                    q: float, z_F: float, maximum_stages: int = 200) -> McCabeThieleResult:
    """Construit les marches; condenseur total exclu, rebouilleur partiel inclus.

    Chaque paire de segments (horizontal vers ELV, vertical vers une droite opératoire)
    est stockée dans ``stage_points``. Un dépassement de x_B correspond au dernier étage,
    compté comme le rebouilleur.
    """
    m_r, b_r, m_s, b_s, feed_cross = operating_lines(x_D, x_B, R, q, z_F)
    points: list[tuple[float, float]] = [(x_D, x_D)]
    y_current = x_D
    for count in range(1, maximum_stages + 1):
        x_eq = x_at_equilibrium_y(y_current, curve)
        points.append((x_eq, y_current))
        if x_eq <= x_B:
            return McCabeThieleResult(count, points, feed_cross, m_r, b_r, m_s, b_s)
        # Au-dessus de l'alimentation : section d'enrichissement.
        y_next = (m_r * x_eq + b_r) if x_eq >= feed_cross[0] else (m_s * x_eq + b_s)
        points.append((x_eq, y_next))
        y_current = y_next
    raise RuntimeError("Nombre maximal d'étages atteint (pincement ou R insuffisant).")
