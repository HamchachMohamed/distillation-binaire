"""Données, unités et paramètres thermodynamiques du solveur eau--éthanol.

Les compositions sont molaires et repérées par l'éthanol sauf mention contraire.
Les pressions internes sont en Pa, les températures internes en K.
"""
from dataclasses import dataclass


WATER_MW_KG_PER_KMOL = 18.01528
ETHANOL_MW_KG_PER_KMOL = 46.06844
ATM_PA = 101_325.0


@dataclass(frozen=True)
class NRTLParameters:
    """NRTL dans la convention tau_ij = a_ij + b_ij/T (T en K)."""

    # Ordre des constituants : [ethanol, water].
    a_e_w: float = -0.8009
    b_e_w_K: float = 246.18
    a_w_e: float = 3.4578
    b_w_e_K: float = -586.0809
    alpha: float = 0.30


NRTL_ETHANOL_WATER = NRTLParameters()


@dataclass(frozen=True)
class AntoineSet:
    """log10(P_sat/bar) = A - B/(T[K] + C), domaine inclus en K."""

    A: float
    B: float
    C: float
    t_min_K: float
    t_max_K: float
    reference: str


# Les segments suivants viennent de NIST Chemistry WebBook SRD 69.
ANTOINE = {
    "ethanol_low": AntoineSet(5.24677, 1598.673, -46.424, 292.77, 366.63,
                               "NIST SRD 69; Ambrose & Sprake (1970)"),
    "ethanol_high": AntoineSet(4.92531, 1432.526, -61.819, 364.80, 513.91,
                                "NIST SRD 69; Ambrose et al. (1975)"),
    "water_low": AntoineSet(4.65430, 1435.264, -64.848, 255.90, 344.00,
                              "NIST SRD 69; Stull (1947)"),
    # Le domaine NIST est publié jusqu'à 373 K (arrondi); la borne 373.15 K est
    # explicitement retenue pour le point normal d'ébullition de l'eau (373.124 K).
    "water_high": AntoineSet(5.08354, 1663.125, -45.622, 344.00, 373.15,
                               "NIST SRD 69; Bridgeman & Aldrich (1964)"),
}


@dataclass(frozen=True)
class FeedInput:
    mass_flow_kg_h: float = 30.0
    ethanol_mass_fraction: float = 0.40
    reference_temperature_C: float = 25.0
    pressure_kPa: float = 101.325


@dataclass(frozen=True)
class ColumnSpecifications:
    x_distillate: float
    x_bottoms: float
    reflux_ratio: float
    q: float


THERMO_SOURCES = """\
NRTL : jeu DECHEMA/Aspen (ethanol, water), tau_ij=a_ij+b_ij/T :
a_E,W=-0.8009, b_E,W=246.18 K; a_W,E=3.4578, b_W,E=-586.0809 K;
alpha=0.30. Une validation indépendante publiée avec ce jeu donne
x_az=0.89344 et T_az=351.289 K à 101325 Pa.
Référence de mise en oeuvre et de comparaison : Kitchin Research Group,
"Phase diagrams and activity models" (DECHEMA/Aspen NRTL set), 2024.
P_sat : NIST Chemistry WebBook SRD 69, équation Antoine en bar et K.
"""
