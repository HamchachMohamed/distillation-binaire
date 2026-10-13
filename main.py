"""Point d'entrée CLI du solveur pédagogique de distillation eau--éthanol."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from config import ATM_PA, THERMO_SOURCES
from equilibrium import azeotrope, calculate_equilibrium_curve, equilibrium_at_liquid_composition
from material_balance import column_balance, feed_balance
from mccabe_thiele import step_off_stages
from plots import plot_mccabe_thiele, plot_txy, plot_xy


def fraction(value: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Une fraction doit être numérique.") from error
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("Une fraction doit être comprise entre 0 et 1.")
    return number


def positive(value: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("La valeur doit être numérique.") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("La valeur doit être strictement positive.")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ELV NRTL et McCabe–Thiele pour eau–éthanol.")
    parser.add_argument("--pressure-kpa", "--pressure", dest="pressure_kpa", type=positive, default=101.325,
                        help="Pression absolue en kPa (défaut : 101.325).")
    parser.add_argument("--feed", type=positive, default=30.0, help="Débit massique F en kg/h (défaut : 30).")
    parser.add_argument("--ethanol-mass-fraction", type=fraction, default=0.40,
                        help="Fraction massique d'éthanol de l'alimentation (défaut : 0.40).")
    parser.add_argument("--reference-temperature", type=float, default=25.0,
                        help="Température initiale/de référence en °C (défaut : 25).")
    parser.add_argument("--xD", type=fraction, help="Fraction molaire d'éthanol au distillat.")
    parser.add_argument("--xB", type=fraction, help="Fraction molaire d'éthanol au résidu.")
    parser.add_argument("--reflux-ratio", "--R", dest="reflux_ratio", type=positive, help="Taux de reflux R=L/D.")
    parser.add_argument("--q", type=float, help="Condition thermique de l'alimentation (q=1 : liquide saturé).")
    parser.add_argument("--points", type=int, default=201, help="Nombre de points ELV (>=11).")
    parser.add_argument("--output", type=Path, default=Path("results"), help="Répertoire de sortie.")
    parser.add_argument("--show", action="store_true", help="Affiche les figures après leur sauvegarde.")
    return parser


def write_equilibrium_csv(curve, output: Path) -> Path:
    target = output / "equilibre_Txy_yx.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["x_ethanol_liquide", "y_ethanol_vapeur", "temperature_K", "temperature_C"])
        for x, y, T in zip(curve.x_ethanol, curve.y_ethanol, curve.temperature_K):
            writer.writerow([f"{x:.10f}", f"{y:.10f}", f"{T:.8f}", f"{T - 273.15:.8f}"])
    return target


def write_stages_csv(result, output: Path) -> Path:
    target = output / "marches_mccabe_thiele.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["point", "x_ethanol", "y_ethanol"])
        writer.writerows((index, f"{x:.10f}", f"{y:.10f}")
                         for index, (x, y) in enumerate(result.stage_points))
    return target


def print_feed(feed, args) -> None:
    print("\n=== DONNÉES D'ENTRÉE ===")
    print(f"F = {args.feed:.6g} kg/h | w_E,F = {args.ethanol_mass_fraction:.6f} (massique)")
    print(f"P = {args.pressure_kpa:.6g} kPa abs | T de référence = {args.reference_temperature:.6g} °C")
    print("Note : 25 °C est une température initiale/de référence, pas une température d'ELV à 1 atm.")
    print("\n=== BILAN DE L'ALIMENTATION ===")
    print(f"Eau      : {feed.water_mass_kg_h:.6f} kg/h = {feed.water_kmol_h:.6f} kmol/h")
    print(f"Éthanol  : {feed.ethanol_mass_kg_h:.6f} kg/h = {feed.ethanol_kmol_h:.6f} kmol/h")
    print(f"Total    : {feed.total_kmol_h:.6f} kmol/h")
    print(f"z_E,F    : {feed.ethanol_mole_fraction:.8f} (molaire; différent de w_E,F)")


def check_column_specifications(args) -> tuple[float, float, float, float] | None:
    values = (args.xD, args.xB, args.reflux_ratio, args.q)
    if all(value is None for value in values) and sys.stdin.isatty():
        print("\nSpécifications McCabe–Thiele absentes. Saisissez-les ou laissez x_D vide pour ignorer.")
        x_D_text = input("x_D (fraction molaire d'éthanol) : ").strip()
        if not x_D_text:
            return None
        x_B_text = input("x_B (fraction molaire d'éthanol) : ").strip()
        R_text = input("R = L/D : ").strip()
        q_text = input("q (1 = liquide saturé) : ").strip()
        try:
            return float(x_D_text), float(x_B_text), float(R_text), float(q_text)
        except ValueError as error:
            raise ValueError("Les quatre spécifications McCabe–Thiele doivent être numériques.") from error
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("McCabe–Thiele exige --xD, --xB, --reflux-ratio et --q ensemble.")
    return args.xD, args.xB, args.reflux_ratio, args.q


def main() -> int:
    # Évite les erreurs de console Windows (cp1252) avec les symboles scientifiques.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    if args.points < 11:
        raise ValueError("--points doit être au moins égal à 11.")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pressure_pa = args.pressure_kpa * 1000.0
    feed = feed_balance(args.feed, args.ethanol_mass_fraction)
    print_feed(feed, args)

    curve = calculate_equilibrium_curve(pressure_pa, args.points)
    T_feed_K, y_feed = equilibrium_at_liquid_composition(feed.ethanol_mole_fraction, pressure_pa)
    print("\n=== ELV À LIQUIDE SATURÉ (COMPOSITION DE L'ALIMENTATION) ===")
    print(f"T_bulle(z_E,F) = {T_feed_K:.4f} K = {T_feed_K - 273.15:.4f} °C")
    print(f"y_E à l'équilibre = {y_feed:.8f}; y_E - x_E = {y_feed - feed.ethanol_mole_fraction:+.8f}")
    print("La vapeur est enrichie en éthanol car son équilibre liquide-vapeur favorise l'espèce la plus volatile.")

    az = azeotrope(curve)
    if az:
        print(f"Azéotrope NRTL détecté : x_E = y_E = {az[0]:.6f}, T = {az[1]:.3f} K ({az[1]-273.15:.3f} °C).")
        print(f"Comparaison du jeu publié : Δx = {az[0] - 0.89344265:+.6f}, ΔT = {az[1] - 351.28895:+.3f} K.")
        print("Une distillation binaire ordinaire à cette pression ne franchit pas cet azéotrope.")
    if np.any((curve.x_ethanol < 0) | (curve.x_ethanol > 1) | (curve.y_ethanol < 0) | (curve.y_ethanol > 1)):
        raise RuntimeError("Échec de validation : composition hors de [0,1].")
    print("Validation physique : toutes les compositions calculées appartiennent à [0, 1].")

    generated = [plot_txy(curve, feed.ethanol_mole_fraction, output, args.show),
                 plot_xy(curve, feed.ethanol_mole_fraction, y_feed, output, args.show),
                 write_equilibrium_csv(curve, output)]

    specs = check_column_specifications(args)
    if specs is None:
        print("\n=== MCCABE–THIELE ===")
        print("Spécifications absentes : aucun nombre d'étages n'est inventé.")
        print("Relancez avec --xD --xB --reflux-ratio --q, par exemple :")
        print("  python main.py --xD 0.85 --xB 0.05 --reflux-ratio 4 --q 1")
    else:
        x_D, x_B, R, q = specs
        if az and x_D > az[0] + 1e-3:
            raise ValueError("x_D dépasse l'azéotrope : séparation impossible par distillation binaire simple à cette pression.")
        column = column_balance(feed.total_kmol_h, feed.ethanol_mole_fraction, x_D, x_B)
        result = step_off_stages(curve, x_D, x_B, R, q, feed.ethanol_mole_fraction)
        print("\n=== BILAN DE LA COLONNE ===")
        print(f"D = {column.distillate_kmol_h:.6f} kmol/h = {column.distillate_mass_kg_h:.6f} kg/h")
        print(f"B = {column.bottoms_kmol_h:.6f} kmol/h = {column.bottoms_mass_kg_h:.6f} kg/h")
        print(f"Résidus bilan total = {column.total_residual_kmol_h:.3e} kmol/h")
        print(f"Résidu bilan éthanol = {column.ethanol_residual_kmol_h:.3e} kmol/h")
        print(f"Résidu bilan massique = {column.total_mass_residual_kg_h:.3e} kg/h")
        print("\n=== MCCABE–THIELE ===")
        print(f"x_D={x_D:.6f}, x_B={x_B:.6f}, R={R:.6g}, q={q:.6g}")
        print(f"Nombre entier construit = {result.stages_including_reboiler} étages théoriques.")
        print("Convention : condenseur total exclu; rebouilleur partiel inclus; dernier étage potentiellement fractionnaire non interpolé.")
        generated.extend([plot_mccabe_thiele(curve, result, x_D, x_B, feed.ethanol_mole_fraction, q, output, args.show),
                          write_stages_csv(result, output)])
    print("\nFichiers générés :")
    for path in generated:
        print(f"  {path}")
    print("\n=== MODÈLE ET LIMITES ===")
    print(THERMO_SOURCES.strip())
    print("Hypothèses ELV : vapeur idéale, pression modérée, facteur de Poynting négligé; utiliser un EOS/gamma-phi pour des conditions non modérées.")
    print("Principes : y_i P = x_i gamma_i P_i^sat; R=L/D; à reflux total R→∞, les droites opératoires tendent vers y=x.")
    print("Le condenseur total produit un distillat de composition x_D; le rebouilleur fournit la vapeur montante et est ici compté.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        raise SystemExit(2)
