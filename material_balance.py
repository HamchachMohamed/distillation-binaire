"""Bilans de matière de l'alimentation et de la colonne binaire."""
from dataclasses import dataclass

from config import ETHANOL_MW_KG_PER_KMOL, WATER_MW_KG_PER_KMOL


@dataclass(frozen=True)
class FeedBalance:
    water_mass_kg_h: float
    ethanol_mass_kg_h: float
    water_kmol_h: float
    ethanol_kmol_h: float
    total_kmol_h: float
    ethanol_mole_fraction: float


@dataclass(frozen=True)
class ColumnBalance:
    distillate_kmol_h: float
    bottoms_kmol_h: float
    distillate_mass_kg_h: float
    bottoms_mass_kg_h: float
    total_residual_kmol_h: float
    ethanol_residual_kmol_h: float
    total_mass_residual_kg_h: float


def feed_balance(total_mass_kg_h: float, ethanol_mass_fraction: float) -> FeedBalance:
    """Convertit le débit massique de l'alimentation en débits molaires."""
    if total_mass_kg_h <= 0:
        raise ValueError("Le débit massique d'alimentation doit être strictement positif.")
    if not 0.0 <= ethanol_mass_fraction <= 1.0:
        raise ValueError("La fraction massique d'éthanol doit être comprise entre 0 et 1.")
    ethanol_mass = total_mass_kg_h * ethanol_mass_fraction
    water_mass = total_mass_kg_h - ethanol_mass
    ethanol_kmol = ethanol_mass / ETHANOL_MW_KG_PER_KMOL
    water_kmol = water_mass / WATER_MW_KG_PER_KMOL
    total_kmol = ethanol_kmol + water_kmol
    return FeedBalance(water_mass, ethanol_mass, water_kmol, ethanol_kmol, total_kmol,
                       ethanol_kmol / total_kmol)


def mixture_molar_mass_kg_per_kmol(x_ethanol: float) -> float:
    if not 0.0 <= x_ethanol <= 1.0:
        raise ValueError("La fraction molaire doit être comprise entre 0 et 1.")
    return x_ethanol * ETHANOL_MW_KG_PER_KMOL + (1.0 - x_ethanol) * WATER_MW_KG_PER_KMOL


def column_balance(feed_kmol_h: float, z_ethanol: float, x_distillate: float,
                   x_bottoms: float) -> ColumnBalance:
    """Résout F=D+B et Fz=DxD+BxB; les fractions sont molaires d'éthanol."""
    if feed_kmol_h <= 0:
        raise ValueError("F doit être strictement positif.")
    if not all(0.0 <= value <= 1.0 for value in (z_ethanol, x_distillate, x_bottoms)):
        raise ValueError("Les compositions doivent être comprises entre 0 et 1.")
    if abs(x_distillate - x_bottoms) < 1e-12:
        raise ValueError("x_D et x_B doivent être différents.")
    distillate = feed_kmol_h * (z_ethanol - x_bottoms) / (x_distillate - x_bottoms)
    bottoms = feed_kmol_h - distillate
    if distillate < -1e-10 or bottoms < -1e-10:
        raise ValueError("Les spécifications sont incompatibles avec la composition de l'alimentation.")
    total_residual = feed_kmol_h - distillate - bottoms
    ethanol_residual = feed_kmol_h * z_ethanol - distillate * x_distillate - bottoms * x_bottoms
    distillate_mass = distillate * mixture_molar_mass_kg_per_kmol(x_distillate)
    bottoms_mass = bottoms * mixture_molar_mass_kg_per_kmol(x_bottoms)
    feed_mass = feed_kmol_h * mixture_molar_mass_kg_per_kmol(z_ethanol)
    return ColumnBalance(distillate, bottoms, distillate_mass, bottoms_mass,
                         total_residual, ethanol_residual, feed_mass - distillate_mass - bottoms_mass)
