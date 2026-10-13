"""Résolution ELV isobare et construction des tableaux T-x-y / y-x."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from thermodynamics import bubble_pressure_pa, equilibrium_vapor_composition


@dataclass(frozen=True)
class EquilibriumCurve:
    x_ethanol: np.ndarray
    y_ethanol: np.ndarray
    temperature_K: np.ndarray
    pressure_pa: float

    @property
    def temperature_C(self) -> np.ndarray:
        return self.temperature_K - 273.15


def bubble_temperature_K(x_ethanol: float, pressure_pa: float) -> float:
    """Résout sum_i x_i gamma_i P_sat,i(T)=P; T est bornée par les données NIST."""
    if pressure_pa <= 0:
        raise ValueError("La pression doit être strictement positive.")
    # Les paramètres et les domaines Antoine installés couvrent 1 atm. 373.15 K
    # couvre explicitement le point normal de l'eau, à la précision du domaine NIST.
    lower, upper = 293.0, 373.15
    func = lambda T: bubble_pressure_pa(x_ethanol, T) - pressure_pa
    if func(lower) * func(upper) > 0:
        raise ValueError("La pression demandée ne peut pas être traitée sans extrapoler les données Antoine.")
    return float(brentq(func, lower, upper, xtol=1e-10, rtol=1e-12))


def calculate_equilibrium_curve(pressure_pa: float, points: int = 201) -> EquilibriumCurve:
    if points < 11:
        raise ValueError("Au moins 11 points sont nécessaires.")
    x = np.linspace(0.0, 1.0, points)
    temperatures = np.array([bubble_temperature_K(float(value), pressure_pa) for value in x])
    y = np.array([equilibrium_vapor_composition(float(x_i), float(T_i), pressure_pa)
                  for x_i, T_i in zip(x, temperatures)])
    # Les corps purs imposent exactement les extrémités, indépendamment des arrondis.
    y[0], y[-1] = 0.0, 1.0
    if np.any((y < -1e-12) | (y > 1.0 + 1e-12)):
        raise RuntimeError("Composition vapeur non physique calculée.")
    return EquilibriumCurve(x, y, temperatures, pressure_pa)


def equilibrium_at_liquid_composition(x_ethanol: float, pressure_pa: float) -> tuple[float, float]:
    """Retourne (T_bulle_K, y_ethanol) pour un liquide saturé."""
    temperature = bubble_temperature_K(x_ethanol, pressure_pa)
    return temperature, equilibrium_vapor_composition(x_ethanol, temperature, pressure_pa)


def azeotrope(curve: EquilibriumCurve) -> tuple[float, float] | None:
    """Localise y=x hors des extrémités, si un azéotrope est présent."""
    f = curve.y_ethanol - curve.x_ethanol
    candidates = np.where(f[:-1] * f[1:] < 0.0)[0]
    if len(candidates) == 0:
        return None
    index = int(candidates[np.argmin(np.abs(curve.x_ethanol[candidates] - 0.9))])
    x0, x1 = curve.x_ethanol[index:index + 2]
    def residual(xx: float) -> float:
        temperature, yy = equilibrium_at_liquid_composition(float(xx), curve.pressure_pa)
        return yy - xx
    x_az = float(brentq(residual, x0, x1, xtol=1e-11))
    T_az, _ = equilibrium_at_liquid_composition(x_az, curve.pressure_pa)
    return x_az, T_az


def x_at_equilibrium_y(y_target: float, curve: EquilibriumCurve) -> float:
    """Inverse la courbe monotone y(x), requis par la construction McCabe--Thiele."""
    if not 0.0 <= y_target <= 1.0:
        raise ValueError("La composition vapeur ciblée doit être comprise entre 0 et 1.")
    if np.any(np.diff(curve.y_ethanol) < -1e-8):
        raise ValueError("La courbe y(x) n'est pas monotone : inversion impossible.")
    return float(np.interp(y_target, curve.y_ethanol, curve.x_ethanol))
