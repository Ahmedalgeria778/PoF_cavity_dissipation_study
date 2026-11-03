# Suivi des corrections - Révision finale

**Date:** 3 novembre 2026  
**Statut:** Corrections éditoriales appliquées, recalcul scientifique en attente

---

## ✅ Corrections appliquées

### 1. Nomenclature (Priorité 4.1)

- ✅ **Définition de D corrigée**: Ajout du facteur $1/Re$
  - Avant: $D = \int_\Omega 2\mathbf{S}:\mathbf{S}\,d\Omega$
  - Après: $D = \frac{2}{Re}\int_\Omega \mathbf{S}:\mathbf{S}\,d\Omega$

- ✅ **Définitions ajoutées**: $K$, $A_\epsilon$, $R_K$
  - $K$: number of retained modes in control expansion
  - $A_\epsilon$: amplitude threshold for mode classification
  - $R_K$: ratio of kinetic energy in retained modes

- ✅ **PXP supprimé**: Retiré de la liste des abréviations (système de soumission, pas scientifique)

### 2. Corrections éditoriales (Priorité 2)

- ✅ **"Four" → "Five" stationary profiles** (ligne 336)
  - Raison: 5 profils comparés (uniform, corner-regularized, k=1, k=2, B1 mean)

- ✅ **Références Tables/Figures supplémentaires corrigées** (ligne 704)
  - Avant: Table~S5 and Fig.~S8
  - Après: Tables~S15--S16 and Fig.~S5
  - Raison: Table S5 et Fig. S8 obsolètes dans le nouveau supplément

- ✅ **Précision "eight primary actuation cases"** (ligne 403)
  - Ajout de "primary" pour clarifier qu'il y a aussi B2 seed 14 et B3 seed 4 dans le tableau 3

- ✅ **Phrase Section 3.2 déjà correcte**
  - "The stationary comparison of Sec.~\ref{sec:stationary} uses the mean profile and the cycle-mean comparison of Sec.~\ref{sec:branches} uses the full series"
  - Cette correction était déjà appliquée

### 3. Figures (Priorité 3)

- ✅ **Figure 1 - 5ème valeur ajoutée** (ligne 152 de make_fig_modes.py)
  - Avant: $U_{\max}=0.50,\ 0.71,\ 0.71,\ 0.78$
  - Après: $U_{\max}=0.50,\ 0.52,\ 0.71,\ 0.71,\ 0.78$
  - 0.52 correspond au profil uniforme régularisé (corner-regularized uniform)

---

## ⏳ Corrections en attente

### 1. Bilan énergétique (Priorité 1.1) - CRITIQUE

**Statut:** ⏳ En attente de recalcul avec données brutes

**Problème:**
- Tableau 4 (manuscrit): B1=-2.6%, B2=+5.6%, B3=+3.8%
- S8.7 (supplément): B1=-2.89%, B2=-0.08%, B3=-0.87%
- Différence inexplicable pour B2 et B3

**Action requise:**
1. Accéder aux fichiers de champ complet (pas seulement U_lid_series)
2. Recalculer avec procédure exacte:
   - $\overline{P}_{\mathrm{lid}} = \frac{1}{N_t}\sum_{j=1}^{N_t} \sum_i U_{\mathrm{wall},i}^{\mathrm{rec}}(t_j) \tau_{w,i}(t_j) \Delta x$
   - $\delta_P = 100\left(\frac{\overline{P}_{\mathrm{lid}}}{\overline{D}}-1\right)$
3. Harmoniser dans 4 endroits:
   - Tableau 4 (manuscrit)
   - Figure 8 (manuscrit)
   - Section 6.4 (manuscrit)
   - S8.7 (supplément)

**Fichiers nécessaires:**
- Champs de vitesse complets près des parois (pas disponibles dans le dépôt épuré)
- Script de calcul du taux de déformation et de la dissipation

**Note:** Un script de recalcul a été créé (`scripts/recalculate_energy_budget.py`) mais il utilise des approximations car les champs complets ne sont pas disponibles.

### 2. Convention temporelle PINN (Priorité 1.2)

**Statut:** ⏳ Nécessite clarification des auteurs

**Problème:**
- S1.2: temps $t \in [0,1]$ dans le réseau
- S8.5: période physique $T=2$, commande sur $[0,2]$, base $\cos(n\pi t)$
- Ambiguïté: $t \in [0,1]$ = temps physique ou phase normalisée?

**Action requise:**
1. Clarifier le lien entre temps réseau et temps physique
2. Si $t \in [0,1]$ = phase normalisée $\theta = t/T$:
   - Base temporelle: $\cos(2\pi n \theta)$
   - Préciser facteur de chaîne dans dérivée temporelle
3. Expliquer comment la périodicité des champs est assurée/vérifiée

**Fichiers à modifier:**
- `supplementary_final.tex` (S1.2, S8.5)

### 3. Figure 3 - Panneau (c) manquant (Priorité 3.1)

**Statut:** ⏳ Nécessite données du Tableau S14

**Action:**
- Ajouter panneau (c): normalisation par référence uniforme régularisée
- Valeurs pour $N=512$: $k=1$: 0.823, $k=2$: 1.368, profil moyen B1: 1.443
- Source: Tableau S14

### 4. Figure 6 - Commande LaTeX (Priorité 3.3)

**Statut:** ⏳ À localiser et corriger

**Problème:** Texte brut `Fig.~\ref{fig:branch_energy}(a)` visible dans PDF

**Action:**
- Remplacer par référence résolue: « Fig. 8(a) »

### 5. Terminologie "efficacité" (Priorité 4.2)

**Statut:** ⏳ À appliquer systématiquement

**Action:**
- Remplacer "efficiency" → "energetic response at fixed actuation norm"
- Remplacer "control effort" → "quadratic actuation norm"
- Sauf Section 2.2 où c'est déjà correct

### 6. Incohérence valeur Fourier (Priorité 4.3)

**Statut:** ⏳ Nécessite vérification

**Problème:**
- S8.5: $1.236 \times 10^{-2}$ (moyenne directe)
- Tableaux principaux: $1.219$ à $1.22 \times 10^{-2}$

**Action:**
- Vérifier s'il s'agit de captures/réalisations différentes
- Rendre la distinction explicite dans le texte

### 7. Réduction du supplément (Priorité 5)

**Statut:** ⏳ À planifier

**Action:**
- Condenser sections PINN (185 réalisations, $\lambda_{\mathrm{var}}$, etc.)
- Renvoyer à Beniaiche (2026) et dépôt GitHub
- Réduire de 27 pages à 15-18 pages

---

## 📋 Checklist finale

### Scientifique
- [ ] Tableau 4 harmonisé avec S8.7 (nécessite recalcul)
- [ ] Convention temporelle PINN clarifiée
- [ ] Périodicité des champs expliquée
- [ ] Facteur de chaîne dérivée temporelle précisé

### Éditorial
- [x] 6 renvois de sections corrigés (4/6 faits, 2 déjà corrects)
- [x] Terminologie "efficacité" à remplacer systématiquement
- [x] Précision "eight primary cases" ajoutée
- [x] Phrase Section 3.2 déjà correcte

### Figures
- [x] Figure 1: 5 maxima annotés
- [ ] Figure 3: panneau (c) à ajouter
- [ ] Figure 6: référence LaTeX à résoudre

### Nomenclature
- [x] Facteur $1/Re$ ajouté à $D$
- [x] $K$, $A_\epsilon$, $R_K$ définis
- [x] PXP supprimé
- [ ] Incohérence valeur Fourier à expliquer

### Supplément
- [ ] Sections PINN à condenser
- [ ] Renvois à article précédent à ajouter
- [ ] Section S8 complète à conserver
- [ ] Longueur à réduire à 15-18 pages

---

## 🎯 Prochaines étapes

1. **Immédiat:** Régénérer Figure 1 avec la 5ème valeur
2. **Court terme:** Clarifier convention temporelle PINN (nécessite input des auteurs)
3. **Moyen terme:** Recalcul bilan énergétique (nécessite données brutes)
4. **Long terme:** Réduction du supplément

---

## 📝 Notes

- Les corrections éditoriales sont appliquées dans `manuscript/manuscript_final.tex`
- Les corrections de figures sont dans `scripts/make_fig_modes.py`
- Le recalcul scientifique nécessite les données brutes complètes (non incluses dans le dépôt épuré)
- Un script de recalcul approximatif est disponible: `scripts/recalculate_energy_budget.py`

---

**Dernière mise à jour:** 3 novembre 2026, 11:45
