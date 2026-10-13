# Solveur pédagogique de distillation binaire eau–éthanol

Ce projet calcule le bilan d'alimentation, l'ELV isobare eau–éthanol par **NRTL**,
les diagrammes `T-x-y` et `y-x`, puis la construction de McCabe–Thiele lorsque les
spécifications de séparation sont fournies.

## Données transcrites de l'énoncé

L'image annoncée (`1000417173.jpg`) n'était pas accessible dans le répertoire du
projet lors de la création du programme. Les données utilisées sont donc celles
transcrites dans la demande : `F = 30 kg/h`, `w_E,F = 0,40`, `T_ref = 25 °C`,
`P = 1 atm = 101,325 kPa`. Le programme permet de les modifier toutes.

La température de 25 °C est une température initiale/de référence : elle n'est
pas utilisée comme température d'équilibre à 1 atm.

## Installation et exécution

Exécuter depuis le dossier `distillation_binaire` avec Python 3.12 (ou version
compatible) :

```powershell
python -m pip install -r requirements.txt
python main.py
```

La pression est toujours une pression **absolue en kPa** au niveau de la CLI; les
équations travaillent en Pa. Les températures internes sont en K et affichées en
°C. Les débits molaires sont en kmol/h.

Exemple avec les spécifications nécessaires à McCabe–Thiele :

```powershell
python main.py --pressure-kpa 101.325 --feed 30 --ethanol-mass-fraction 0.40 --xD 0.85 --xB 0.05 --reflux-ratio 4 --q 1
```

`xD`, `xB` et `q` sont des fractions molaires d'éthanol; `R=L/D` est sans unité.
Sans ces quatre arguments, le programme calcule l'ELV mais ne suppose aucun
objectif de séparation. Les fichiers PNG (300 dpi) et CSV sont écrits dans
`results/`, modifiable par `--output`.

Tests :

```powershell
python -m unittest discover -s tests -v
```

## Méthode thermodynamique

Pour chaque point de bulle, le code résout numériquement :

`P = somme_i x_i gamma_i(x,T) P_i^sat(T)`

et en déduit `y_i = x_i gamma_i P_i^sat/P`. C'est une formulation Raoult modifiée
avec vapeur idéale et facteur de Poynting négligé, adaptée au voisinage de 1 atm.
`gamma_i` est évalué par NRTL : `tau_ij=a_ij+b_ij/T` et
`G_ij=exp(-alpha_ij tau_ij)`.

L'ordre interne est `(ethanol, water)` : `a_E,W=-0.8009`, `b_E,W=246.18 K`,
`a_W,E=3.4578`, `b_W,E=-586.0809 K`, `alpha=0.30`. Il s'agit du jeu
DECHEMA/Aspen rapporté dans l'exemple indépendant de Kitchin Research Group,
*Phase diagrams and activity models* (2024), qui rapporte à 101325 Pa
`x_az=0.89344`, `T_az=351.289 K` (expérimental cité : `0.894`, `351.3 K`).
Le programme affiche l'écart de sa résolution numérique à cette comparaison;
sur l'installation validée, il est voisin de `+0.0020` sur `x` et `+0.006 K`.
Les pressions de vapeur sont les coefficients Antoine de NIST Chemistry WebBook
SRD 69 : `log10(P_sat/bar)=A-B/(T[K]+C)` (Ambrose/Sprake pour l'éthanol;
Stull pour l'eau). Les domaines de validité sont contrôlés (la limite NIST de
l'eau, affichée arrondie à 373 K, est portée explicitement à 373,15 K pour son
point normal d'ébullition), et le solveur refuse
une pression nécessitant une extrapolation des jeux installés.

Sources directes :

- [NIST SRD 69 — éthanol](https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175&Type=ANTOINE)
- [NIST SRD 69 — eau](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Type=ANTOINE)
- [Mise en œuvre/validation du jeu NRTL DECHEMA-Aspen](https://kitchingroup.cheme.cmu.edu/differentiable-flowsheets/examples/41_phase_diagrams.html)

Le système possède un azéotrope minimum à 1 atm : un objectif `xD` supérieur à
l'azéotrope est rejeté, car une colonne binaire ordinaire ne peut pas le franchir.
Pour des conceptions industrielles, vérifier les paramètres contre les données
expérimentales de la plage de pression et employer un modèle plus complet si la
vapeur est non idéale.

## McCabe–Thiele

Les droites appliquées sont :

`y = R/(R+1) x + xD/(R+1)` (enrichissement),

`y = q/(q-1) x - zF/(q-1)` (q-line, verticale pour `q=1`),

et la droite d'appauvrissement reliant l'intersection q-line/enrichissement au
point `(xB,xB)`. Les marches alternent horizontalement vers l'ELV puis verticalement
vers une droite opératoire. Le total affiché exclut un condenseur total et inclut
un rebouilleur partiel; le dernier dépassement de `xB` est compté comme dernier
étage entier, sans interpolation de fraction d'étage.

Les bilans sont `F=D+B` et `F zF = D xD + B xB`. Le programme affiche les
résidus numériques du bilan global et du bilan éthanol.
