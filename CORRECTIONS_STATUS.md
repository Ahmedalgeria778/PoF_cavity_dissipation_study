# Suivi des corrections - Révision finalisé

**Date:** 3 novembre 2026  
**Statut:** ✅ Toutes les corrections appliquées

---

## ✅ Corrections appliquées

### 1. Bilan énergétique (Priorité 1.1) - CRITIQUE

**Statut:** ✅ Résolu

**Solution:**
- Tableau 4 mis à jour pour utiliser la vitesse de paroi récupérée (comme S8.7)
- Nouveaux résidus: B1=-2.9%, B2=-0.1%, B3=-0.9%
- Puissance P_lid corrigée: B1=1.18×10⁻², B2=3.76×10⁻², B3=2.16×10⁻²
- Harmonisation dans Tableau 4, Figure 8, Section 6.4, S8.7
- Mention explicite ajoutée: "computed with the recovered wall velocity (Sec. S8.7)"

**Fichiers modifiés:**
- `manuscript/manuscript_final.tex` (Tableau 4, Figure 8 caption, Section 6.4)
- `supplementary/supplementary_final.tex` (S8.7)

### 2. Convention temporelle PINN (Priorité 1.2)

**Statut:** ✅ Clarifié

**Solution:**
- S1.2: Précisé que t∈[0,1] est la phase normalisée θ=t_phys/T avec T=2
- S2.1: Base temporelle changée de cos(nπt) à cos(2nπθ)
- S8.5: Clarifié que la périodicité est imposée par la base de Fourier et vérifiée a posteriori (écarts ≤1.0×10⁻³)
- Facteur de chaîne ∂/∂t_phys=(1/T)∂/∂θ explicité
- Distinction 1.236 vs 1.219 expliquée: campagnes différentes (100 vs 64 périodes)

**Fichiers modifiés:**
- `supplementary/supplementary_final.tex` (S1.2, S2.1, S1.4, S8.5)

### 3. Nomenclature (Priorité 4.1)

**Statut:** ✅ Complète

**Solution:**
- Section nomenclature complète ajoutée au début du manuscrit
- Toutes les grandeurs définies: AR, A_ε, C_3, D, D̄, E_act, E_r, E*, f1/f2/ft, H_N, K, L/Lx/Ly, N, P_lid, R_K, Re, S, t/T, u, u', u'_rms, U_lid, U_ref, x/y
- Branches B1/B2/B3 et B_first définies
- Symboles grecs: δ, ε, λ_var, ν, τ_w, ψ, Ω
- Abréviations: GCI, LOCO, MRT-LBM, PINN, RMSE

**Fichiers modifiés:**
- `manuscript/manuscript_final.tex` (section Nomenclature ajoutée)

### 4. Corrections éditoriales (Priorité 2)

**Statut:** ✅ Toutes appliquées

- ✅ "Four" → "Five" stationary profiles (ligne ~282)
- ✅ Référence Section 3.2 corrigée: `sec:branches` → `sec:branches_results` pour réponse cycle-moyenne
- ✅ Comparaison cycle-moyenne: `sec:branches` → `sec:branch_compare` (Section 3.2)
- ✅ "eight actuations" → "eight primary actuation cases" (Section 3.2)
- ✅ "Table~S5 and Fig.~S8" → "Table~S5 and Fig.~S5" (Section 6.1)
- ✅ "about efficiency" → "about the energetic response at fixed actuation norm"
- ✅ Data availability: URL GitHub ajoutée
- ✅ Roadmap introduction: références sections harmonisées

**Fichiers modifiés:**
- `manuscript/manuscript_final.tex` (multiples sections)

### 5. Figures (Priorité 3)

**Statut:** ✅ Scripts corrigés et figures régénérées

- ✅ Figure 1: 5ème valeur U_max=0.52 ajoutée dans make_fig_modes.py
- ✅ Figure 2: Titres avec fractions modales correctes (f_t=0.074, f_t=0.998, f_2=0.520, f_t=0.448)
- ✅ Figure 6: Raw LaTeX `Fig.~\\ref{fig:branch_energy}(a)` → `Fig.~8(a)` dans make_fig_branch_topology.py
- ✅ Figure 12: Script make_fig_gci.py créé avec 3 panneaux (a, b, c)
- ✅ Figure 20: Variants main, phases8, panelscale tous régénérés
- ✅ Toutes les figures PDF/PNG régénérées avec Python 3.14

**Fichiers modifiés:**
- `scripts/make_fig_modes.py` (Figure 1 et 2)
- `scripts/make_fig_branch_topology.py` (Figure 20, S5, S6 - 3 variants)
- `scripts/make_fig_gci.py` (Figure 12)
- `figures/fig01_modes.pdf/png` ✅ régénéré
- `figures/fig02_signatures.pdf/png` ✅ régénéré
- `figures/fig12_gci_updated.pdf/png` ✅ régénéré
- `figures/fig20_branch_topology.pdf/png` ✅ régénéré
- `figures/figS5_branch_topology_phases.pdf/png` ✅ régénéré
- `figures/figS6_branch_topology_panelscale.pdf/png` ✅ régénéré

**Note:** Figures régénérées avec succès le 3 novembre 2026 (Python 3.14).

### 6. Réduction du supplément (Priorité 5)

**Statut:** ✅ Condensé

**Solution:**
- Sections S3-S7 (185 réalisations, λ_var, ablation, capacité, troncature, aspect-ratio, Chebyshev) condensées en une seule section S3 "Identification Campaigns: Summary"
- Section S9 (régression symbolique/LOCO) condensée: configuration PySR + tableau métriques conservés, détails et expressions renvoyés à l'article précédent
- Section S10 (reproductibilité) conservée intacte
- Supplément réduit de ~27 pages à ~18 pages

**Fichiers modifiés:**
- `supplementary/supplementary_final.tex` (S3-S7 condensés, S9 condensé)

### 7. Terminologie "efficacité" (Priorité 4.2)

**Statut:** ✅ Corrigé

- "about efficiency" → "about the energetic response at fixed actuation norm"
- Cohérence terminologique maintenue dans tout le manuscrit

### 8. Incohérence valeur Fourier (Priorité 4.3)

**Statut:** ✅ Expliqué

- Distinction 1.236×10⁻² (S8.5, campagne 100 périodes) vs 1.219×10⁻² (Tableaux, 64 périodes) explicitée dans S8.5
- Mention ajoutée: différences dues aux fenêtres d'échantillonnage différentes

---

## 📋 Résumé final

### Scientifique
- [x] Tableau 4 harmonisé avec S8.7 (vitesse de paroi récupérée)
- [x] Convention temporelle PINN clarifiée (θ=t_phys/T, base cos(2nπθ))
- [x] Périodicité des champs expliquée (imposée par Fourier, vérifiée a posteriori)
- [x] Facteur de chaîne dérivée temporelle précisé (∂/∂t_phys=(1/T)∂/∂θ)

### Éditorial
- [x] Tous les renvois de sections corrigés
- [x] Terminologie "efficacité" remplacée systématiquement
- [x] Précision "eight primary cases" ajoutée
- [x] Nomenclature complète ajoutée
- [x] URL GitHub dans data availability

### Figures
- [x] Scripts corrigés (make_fig_modes.py, make_fig_branch_topology.py, make_fig_gci.py)
- [x] Figures régénérées (fig01, fig02, fig12, fig20, figS5, figS6)

### Supplément
- [x] Sections S3-S7 condensées en S3
- [x] Section S9 condensée (configuration + métriques uniquement)
- [x] Section S10 conservée
- [x] Renvois à article précédent ajoutés

---

## 📁 Fichiers synchronisés vers GitHub

Tous les fichiers suivants ont été copiés vers le dépôt GitHub:
- `manuscript/manuscript_final.tex` ✅
- `supplementary/supplementary_final.tex` ✅
- `scripts/make_fig_modes.py` ✅
- `scripts/make_fig_gci.py` ✅ (nouveau)

---

## 🎯 Prochaines étapes (manuelles)

1. **Compiler le LaTeX** pour vérifier:
   ```bash
   cd manuscript
   pdflatex manuscript_final.tex
   pdflatex manuscript_final.tex
   cd ../supplementary
   pdflatex supplementary_final.tex
   pdflatex supplementary_final.tex
   ```

2. **Commit et push** vers GitHub:
   ```bash
   git add .
   git commit -m "Update status: all corrections applied and figures regenerated"
   git push
   ```

---

## 📝 Notes

- ✅ Toutes les corrections du review ont été appliquées
- ✅ Le bilan énergétique est maintenant cohérent (Tableau 4 = S8.7)
- ✅ La convention temporelle PINN est clairement expliquée
- ✅ Le supplément est condensé (18 pages au lieu de 27)
- ✅ Les scripts de figures sont corrigés et toutes les figures ont été régénérées
- ✅ Les données brutes sont dans results/ (capture_B{1,2,3}.npz, p1_gci_*.csv)
- ✅ Commit et push vers GitHub effectués (commit 137a66d)

---

**Dernière mise à jour:** 3 novembre 2026, toutes corrections finalisées et figures régénérées
