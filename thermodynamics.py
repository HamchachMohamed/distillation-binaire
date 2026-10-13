"""Modele gamma-phi simplifié : NRTL liquide + vapeur idéale (P = 1 atm)."""
from __future__ import annotations

import math
from typing import Literal

import numpy as np

from config import ANTOINE, NRTL_ETHANOL_WATER


def _check_fraction(x: float) -> float:
    if not 0.0 <= x <= 1.0:
        raise ValueError("La fraction molaire d'éthanol doit être comprise entre 0 et 1.")
    return float(x)


def antoine_pressure_pa(component: Literal["ethanol", "water"], temperature_K: float) -> float:
    """Retourne P_sat en Pa; choisit un segment Antoine NIST dans son domaine."""
    if component == "water":
        candidates = [ANTOINE["water_low"], ANTOINE["water_high"]]
    elif component == "ethanol":
        candidates = [ANTOINE["ethanol_low"], ANTOINE["ethanol_high"]]
    else:
        raise ValueError("Composant inconnu.")
    params = next((s for s in candidates if s.t_min_K <= temperature_K <= s.t_max_K), None)
    if params is None:
        domains = "; ".join(f"{s.t_min_K:g}-{s.t_max_K:g} K" for s in candidates)
        raise ValueError(f"T={temperature_K:.3f} K hors domaine Antoine NIST de {component} ({domains}).")
    return 1.0e5 * 10.0 ** (params.A - params.B / (temperature_K + params.C))


def nrtl_activity_coefficients(x_ethanol: float, temperature_K: float) -> tuple[float, float]:
    """Coefficients d'activité (gamma_ethanol, gamma_water) du NRTL binaire.

    Forme générale : ln(gamma_i)=sum_j x_j tau_ji G_ji / sum_k x_k G_ki
    + sum_j x_j G_ij/sum_k x_k G_kj * [tau_ij-sum_m x_m tau_mj G_mj/sum_k x_k G_kj].
    """
    x_e = _check_fraction(x_ethanol)
    x = np.array([x_e, 1.0 - x_e], dtype=float)
    p = NRTL_ETHANOL_WATER
    tau = np.array([[0.0, p.a_e_w + p.b_e_w_K / temperature_K],
                    [p.a_w_e + p.b_w_e_K / temperature_K, 0.0]])
    alpha = np.array([[0.0, p.alpha], [p.alpha, 0.0]])
    G = np.exp(-alpha * tau)
    denominator = x @ G  # denominator[j] = sum_k x_k G_kj
    ln_gamma = np.zeros(2)
    for i in range(2):
        first = sum(x[j] * tau[j, i] * G[j, i] / denominator[i] for j in range(2))
        second = 0.0
        for j in range(2):
            weighted_tau = sum(x[m] * tau[m, j] * G[m, j] for m in range(2)) / denominator[j]
            second += x[j] * G[i, j] / denominator[j] * (tau[i, j] - weighted_tau)
        ln_gamma[i] = first + second
    return float(math.exp(ln_gamma[0])), float(math.exp(ln_gamma[1]))


def bubble_pressure_pa(x_ethanol: float, temperature_K: float) -> float:
    """P de bulle par Raoult modifié, facteur de Poynting et phi vapeur négligés."""
    x_e = _check_fraction(x_ethanol)
    gamma_e, gamma_w = nrtl_activity_coefficients(x_e, temperature_K)
    return (x_e * gamma_e * antoine_pressure_pa("ethanol", temperature_K)
            + (1.0 - x_e) * gamma_w * antoine_pressure_pa("water", temperature_K))


def equilibrium_vapor_composition(x_ethanol: float, temperature_K: float,
                                  pressure_pa: float) -> float:
    """y_E à l'ELV pour un liquide de composition x_E et T donnée."""
    x_e = _check_fraction(x_ethanol)
    if pressure_pa <= 0:
        raise ValueError("La pression doit être positive.")
    if x_e == 0.0:
        return 0.0
    if x_e == 1.0:
        return 1.0
    gamma_e, _ = nrtl_activity_coefficients(x_e, temperature_K)
    y_e = x_e * gamma_e * antoine_pressure_pa("ethanol", temperature_K) / pressure_pa
    return float(np.clip(y_e, 0.0, 1.0))
