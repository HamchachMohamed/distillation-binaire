<<<<<<< HEAD
"""Point d'entrée CLI du solveur pédagogique de distillation eau--éthanol."""
=======
"""Point d'entrée interactif et CLI du solveur eau--éthanol."""
>>>>>>> d83d00c (Initial commit)
from __future__ import annotations

import argparse
import csv
import sys
<<<<<<< HEAD
=======
from dataclasses import dataclass
>>>>>>> d83d00c (Initial commit)
from pathlib import Path

import numpy as np

<<<<<<< HEAD
from config import ATM_PA, THERMO_SOURCES
from equilibrium import azeotrope, calculate_equilibrium_curve, equilibrium_at_liquid_composition
from material_balance import column_balance, feed_balance
from mccabe_thiele import step_off_stages
from plots import plot_mccabe_thiele, plot_txy, plot_xy
=======
from config import FeedInput, THERMO_SOURCES
from equilibrium import azeotrope, calculate_equilibrium_curve, equilibrium_at_liquid_composition
from material_balance import column_balance, feed_balance
from mccabe_thiele import step_off_stages
from plots import configure_backend, finish_figures, plot_mccabe_thiele, plot_txy, plot_xy
>>>>>>> d83d00c (Initial commit)


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
<<<<<<< HEAD
    parser = argparse.ArgumentParser(description="ELV NRTL et McCabe–Thiele pour eau–éthanol.")
    parser.add_argument("--pressure-kpa", "--pressure", dest="pressure_kpa", type=positive, default=101.325,
                        help="Pression absolue en kPa (défaut : 101.325).")
    parser.add_argument("--feed", type=positive, default=30.0, help="Débit massique F en kg/h (défaut : 30).")
    parser.add_argument("--ethanol-mass-fraction", type=fraction, default=0.40,
                        help="Fraction massique d'éthanol de l'alimentation (défaut : 0.40).")
    parser.add_argument("--reference-temperature", type=float, default=25.0,
                        help="Température initiale/de référence en °C (défaut : 25).")
=======
    defaults = FeedInput()
    parser = argparse.ArgumentParser(description="ELV NRTL et McCabe–Thiele pour eau–éthanol.")
    parser.add_argument("--pressure-kpa", "--pressure", dest="pressure_kpa", type=positive,
                        default=defaults.pressure_kPa, help="Pression absolue en kPa (défaut : 101.325).")
    parser.add_argument("--feed", type=positive, default=defaults.mass_flow_kg_h,
                        help="Débit massique F en kg/h (défaut : 30).")
    parser.add_argument("--ethanol-mass-fraction", type=fraction, default=defaults.ethanol_mass_fraction,
                        help="Fraction massique d'éthanol de l'alimentation (défaut : 0.40).")
    parser.add_argument("--feed-temperature", "--reference-temperature", dest="feed_temperature_C", type=float,
                        default=defaults.reference_temperature_C,
                        help="Température d'alimentation T_F en °C (défaut : 25).")
>>>>>>> d83d00c (Initial commit)
    parser.add_argument("--xD", type=fraction, help="Fraction molaire d'éthanol au distillat.")
    parser.add_argument("--xB", type=fraction, help="Fraction molaire d'éthanol au résidu.")
    parser.add_argument("--reflux-ratio", "--R", dest="reflux_ratio", type=positive, help="Taux de reflux R=L/D.")
    parser.add_argument("--q", type=float, help="Condition thermique de l'alimentation (q=1 : liquide saturé).")
    parser.add_argument("--points", type=int, default=201, help="Nombre de points ELV (>=11).")
    parser.add_argument("--output", type=Path, default=Path("results"), help="Répertoire de sortie.")
<<<<<<< HEAD
    parser.add_argument("--show", action="store_true", help="Affiche les figures après leur sauvegarde.")
    return parser


=======
    parser.add_argument("--interactive", action="store_true", help="Force la saisie interactive, même avec une entrée redirigée.")
    parser.add_argument("--no-interactive", action="store_true", help="Désactive les questions interactives.")
    parser.add_argument("--show", action="store_true", help="Compatibilité : les fenêtres sont déjà affichées par défaut.")
    parser.add_argument("--no-show", action="store_true", help="N'ouvre pas les fenêtres de figures (les PNG restent générés).")
    parser.add_argument("--backend", help="Backend Matplotlib optionnel, p. ex. TkAgg ou QtAgg.")
    return parser


def _prompt_number(label: str, default: float, validator) -> float:
    while True:
        entered = input(f"{label} [{default:g}] : ").strip().replace(",", ".")
        if not entered:
            return default
        try:
            value = float(entered)
            validator(value)
            return value
        except ValueError as error:
            print(f"Entrée invalide : {error}")


def _positive_input(value: float) -> None:
    if value <= 0:
        raise ValueError("la valeur doit être strictement positive")


def _fraction_input(value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError("la fraction doit être comprise entre 0 et 1")


def prompt_feed_inputs(args: argparse.Namespace) -> None:
    """Met à jour args par saisie terminal; Entrée conserve chaque valeur proposée."""
    print("\n=== SAISIE INTERACTIVE DES DONNÉES D'ALIMENTATION ===")
    print("Unités : F en kg/h, w_E,F sans dimension, P absolue en kPa, T_F en °C.")
    args.feed = _prompt_number("Débit massique F (kg/h)", args.feed, _positive_input)
    args.ethanol_mass_fraction = _prompt_number("Fraction massique d'éthanol w_E,F", args.ethanol_mass_fraction,
                                                 _fraction_input)
    args.pressure_kpa = _prompt_number("Pression absolue P (kPa)", args.pressure_kpa, _positive_input)
    args.feed_temperature_C = _prompt_number("Température d'alimentation T_F (°C)", args.feed_temperature_C,
                                              lambda _: None)


@dataclass(frozen=True)
class FeedThermalState:
    bubble_temperature_K: float
    dew_temperature_K: float
    label: str


def determine_feed_thermal_state(feed_temperature_C: float, z_ethanol: float, curve) -> FeedThermalState:
    """Classe T_F par rapport aux limites ELV sans effectuer de bilan d'enthalpie."""
    T_feed_K = feed_temperature_C + 273.15
    T_bubble_K, _ = equilibrium_at_liquid_composition(z_ethanol, curve.pressure_pa)
    T_dew_K = float(np.interp(z_ethanol, curve.y_ethanol, curve.temperature_K))
    tolerance_K = 0.05
    if T_feed_K < T_bubble_K - tolerance_K:
        label = "liquide sous-refroidi"
    elif abs(T_feed_K - T_bubble_K) <= tolerance_K:
        label = "liquide saturé (q = 1 si la pression de colonne est la même)"
    elif T_feed_K < T_dew_K - tolerance_K:
        label = "domaine liquide-vapeur possible (titre vapeur non calculé sans bilan d'enthalpie)"
    elif abs(T_feed_K - T_dew_K) <= tolerance_K:
        label = "vapeur saturée (q = 0 si la pression de colonne est la même)"
    else:
        label = "vapeur surchauffée"
    return FeedThermalState(T_bubble_K, T_dew_K, label)


>>>>>>> d83d00c (Initial commit)
def write_equilibrium_csv(curve, output: Path) -> Path:
    target = output / "equilibre_Txy_yx.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["x_ethanol_liquide", "y_ethanol_vapeur", "temperature_K", "temperature_C"])
<<<<<<< HEAD
        for x, y, T in zip(curve.x_ethanol, curve.y_ethanol, curve.temperature_K):
            writer.writerow([f"{x:.10f}", f"{y:.10f}", f"{T:.8f}", f"{T - 273.15:.8f}"])
=======
        writer.writerows((f"{x:.10f}", f"{y:.10f}", f"{T:.8f}", f"{T - 273.15:.8f}")
                         for x, y, T in zip(curve.x_ethanol, curve.y_ethanol, curve.temperature_K))
>>>>>>> d83d00c (Initial commit)
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
<<<<<<< HEAD
    print("\n=== DONNÉES D'ENTRÉE ===")
    print(f"F = {args.feed:.6g} kg/h | w_E,F = {args.ethanol_mass_fraction:.6f} (massique)")
    print(f"P = {args.pressure_kpa:.6g} kPa abs | T de référence = {args.reference_temperature:.6g} °C")
    print("Note : 25 °C est une température initiale/de référence, pas une température d'ELV à 1 atm.")
=======
    print("\n=== DONNÉES D'ENTRÉE UTILISÉES ===")
    print(f"F = {args.feed:.6g} kg/h | w_E,F = {args.ethanol_mass_fraction:.6f} (fraction massique)")
    print(f"P = {args.pressure_kpa:.6g} kPa absolue | T_F = {args.feed_temperature_C:.6g} °C")
    print("T_F décrit l'état de l'alimentation : ce n'est pas une température d'ELV imposée.")
>>>>>>> d83d00c (Initial commit)
    print("\n=== BILAN DE L'ALIMENTATION ===")
    print(f"Eau      : {feed.water_mass_kg_h:.6f} kg/h = {feed.water_kmol_h:.6f} kmol/h")
    print(f"Éthanol  : {feed.ethanol_mass_kg_h:.6f} kg/h = {feed.ethanol_kmol_h:.6f} kmol/h")
    print(f"Total    : {feed.total_kmol_h:.6f} kmol/h")
<<<<<<< HEAD
    print(f"z_E,F    : {feed.ethanol_mole_fraction:.8f} (molaire; différent de w_E,F)")


def check_column_specifications(args) -> tuple[float, float, float, float] | None:
    values = (args.xD, args.xB, args.reflux_ratio, args.q)
    if all(value is None for value in values) and sys.stdin.isatty():
=======
    print(f"z_E,F    : {feed.ethanol_mole_fraction:.8f} (fraction molaire calculée depuis w_E,F)")


def check_column_specifications(args: argparse.Namespace) -> tuple[float, float, float, float] | None:
    values = (args.xD, args.xB, args.reflux_ratio, args.q)
    if all(value is None for value in values) and sys.stdin.isatty() and not args.no_interactive:
>>>>>>> d83d00c (Initial commit)
        print("\nSpécifications McCabe–Thiele absentes. Saisissez-les ou laissez x_D vide pour ignorer.")
        x_D_text = input("x_D (fraction molaire d'éthanol) : ").strip()
        if not x_D_text:
            return None
<<<<<<< HEAD
        x_B_text = input("x_B (fraction molaire d'éthanol) : ").strip()
        R_text = input("R = L/D : ").strip()
        q_text = input("q (1 = liquide saturé) : ").strip()
        try:
            return float(x_D_text), float(x_B_text), float(R_text), float(q_text)
=======
        try:
            x_B = float(input("x_B (fraction molaire d'éthanol) : ").strip().replace(",", "."))
            reflux_ratio = float(input("R = L/D : ").strip().replace(",", "."))
            q = float(input("q (1 = liquide saturé) : ").strip().replace(",", "."))
            return float(x_D_text.replace(",", ".")), x_B, reflux_ratio, q
>>>>>>> d83d00c (Initial commit)
        except ValueError as error:
            raise ValueError("Les quatre spécifications McCabe–Thiele doivent être numériques.") from error
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError("McCabe–Thiele exige --xD, --xB, --reflux-ratio et --q ensemble.")
    return args.xD, args.xB, args.reflux_ratio, args.q


<<<<<<< HEAD
def main() -> int:
    # Évite les erreurs de console Windows (cp1252) avec les symboles scientifiques.
=======
def _core_options_were_given(argv: list[str]) -> bool:
    options = ("--pressure", "--pressure-kpa", "--feed", "--ethanol-mass-fraction",
               "--feed-temperature", "--reference-temperature")
    return any(item == option or item.startswith(option + "=") for item in argv for option in options)


def main(argv: list[str] | None = None) -> int:
>>>>>>> d83d00c (Initial commit)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
<<<<<<< HEAD
    args = build_parser().parse_args()
    if args.points < 11:
        raise ValueError("--points doit être au moins égal à 11.")
=======
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    if args.points < 11:
        raise ValueError("--points doit être au moins égal à 11.")
    configure_backend(args.backend)
    should_prompt = args.interactive or (sys.stdin.isatty() and not args.no_interactive and not _core_options_were_given(argv))
    if should_prompt:
        prompt_feed_inputs(args)

>>>>>>> d83d00c (Initial commit)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pressure_pa = args.pressure_kpa * 1000.0
    feed = feed_balance(args.feed, args.ethanol_mass_fraction)
    print_feed(feed, args)
<<<<<<< HEAD

    curve = calculate_equilibrium_curve(pressure_pa, args.points)
    T_feed_K, y_feed = equilibrium_at_liquid_composition(feed.ethanol_mole_fraction, pressure_pa)
    print("\n=== ELV À LIQUIDE SATURÉ (COMPOSITION DE L'ALIMENTATION) ===")
    print(f"T_bulle(z_E,F) = {T_feed_K:.4f} K = {T_feed_K - 273.15:.4f} °C")
    print(f"y_E à l'équilibre = {y_feed:.8f}; y_E - x_E = {y_feed - feed.ethanol_mole_fraction:+.8f}")
    print("La vapeur est enrichie en éthanol car son équilibre liquide-vapeur favorise l'espèce la plus volatile.")
=======
    try:
        curve = calculate_equilibrium_curve(pressure_pa, args.points)
    except ValueError as error:
        print("AVERTISSEMENT THERMODYNAMIQUE : la pression demandée sort du domaine couvert par les corrélations Antoine installées.")
        raise ValueError("Choisissez une pression compatible ou ajoutez des corrélations validées pour cette plage.") from error

    T_bubble_K, y_feed = equilibrium_at_liquid_composition(feed.ethanol_mole_fraction, pressure_pa)
    feed_state = determine_feed_thermal_state(args.feed_temperature_C, feed.ethanol_mole_fraction, curve)
    print("\n=== ELV À LIQUIDE SATURÉ (COMPOSITION DE L'ALIMENTATION) ===")
    print(f"T_bulle(z_E,F) = {T_bubble_K:.4f} K = {T_bubble_K - 273.15:.4f} °C")
    print(f"y_E à l'équilibre = {y_feed:.8f}; y_E - x_E = {y_feed - feed.ethanol_mole_fraction:+.8f}")
    print("La vapeur est enrichie en éthanol car son équilibre liquide-vapeur favorise l'espèce la plus volatile.")
    print("\n=== ÉTAT THERMIQUE DE L'ALIMENTATION ===")
    print(f"T_F = {args.feed_temperature_C:.3f} °C ; T_bulle = {feed_state.bubble_temperature_K - 273.15:.3f} °C ; "
          f"T_rosée(z_E,F) = {feed_state.dew_temperature_K - 273.15:.3f} °C")
    print(f"État estimé : {feed_state.label}.")
    print("q n'est pas déduit hors saturation : un bilan d'enthalpie (C_p et ΔH_vap) validé serait nécessaire.")
>>>>>>> d83d00c (Initial commit)

    az = azeotrope(curve)
    if az:
        print(f"Azéotrope NRTL détecté : x_E = y_E = {az[0]:.6f}, T = {az[1]:.3f} K ({az[1]-273.15:.3f} °C).")
        print(f"Comparaison du jeu publié : Δx = {az[0] - 0.89344265:+.6f}, ΔT = {az[1] - 351.28895:+.3f} K.")
        print("Une distillation binaire ordinaire à cette pression ne franchit pas cet azéotrope.")
    if np.any((curve.x_ethanol < 0) | (curve.x_ethanol > 1) | (curve.y_ethanol < 0) | (curve.y_ethanol > 1)):
        raise RuntimeError("Échec de validation : composition hors de [0,1].")
    print("Validation physique : toutes les compositions calculées appartiennent à [0, 1].")

<<<<<<< HEAD
    generated = [plot_txy(curve, feed.ethanol_mole_fraction, output, args.show),
                 plot_xy(curve, feed.ethanol_mole_fraction, y_feed, output, args.show),
                 write_equilibrium_csv(curve, output)]
=======
    txy_path, txy_figure = plot_txy(curve, feed.ethanol_mole_fraction, output)
    xy_path, xy_figure = plot_xy(curve, feed.ethanol_mole_fraction, y_feed, output)
    generated: list[Path] = [txy_path, xy_path, write_equilibrium_csv(curve, output)]
    figures = [txy_figure, xy_figure]
>>>>>>> d83d00c (Initial commit)

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
<<<<<<< HEAD
        generated.extend([plot_mccabe_thiele(curve, result, x_D, x_B, feed.ethanol_mole_fraction, q, output, args.show),
                          write_stages_csv(result, output)])
    print("\nFichiers générés :")
    for path in generated:
        print(f"  {path}")
=======
        mt_path, mt_figure = plot_mccabe_thiele(curve, result, x_D, x_B, feed.ethanol_mole_fraction, q, output)
        generated.extend([mt_path, write_stages_csv(result, output)])
        figures.append(mt_figure)

    print("\nFichiers générés :")
    for path in generated:
        print(f"  {path}")
    shown, backend = finish_figures(figures, show=not args.no_show)
    if shown:
        print(f"Fenêtres graphiques ouvertes via le backend Matplotlib {backend}.")
    elif not args.no_show:
        print(f"AVERTISSEMENT GRAPHIQUE : backend Matplotlib « {backend} » non interactif; fenêtres indisponibles. PNG sauvegardés.")
>>>>>>> d83d00c (Initial commit)
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
