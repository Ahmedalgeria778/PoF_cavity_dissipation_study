# Plan de corrections - Révision finale avant soumission

**Date:** 3 novembre 2026  
**Statut:** Révision finale nécessaire  
**Verdict:** Fond scientifique prometteur, corrections éditoriales et scientifiques requises

---

## 🔴 PRIORITÉ 1: Problèmes scientifiques critiques

### 1.1 Incohérence bilan énergétique (Tableau 4 vs S8.7)

**Problème:**
- Tableau 4 (manuscrit): Résidus B1=-2.6%, B2=+5.6%, B3=+3.8%
- S8.7 (supplément): Résidus B1=-2.89%, B2=-0.08%, B3=-0.87%
- Différence inexplicable pour B2 et B3

**Action requise:**
1. Reprendre les fichiers bruts de capture des branches (results/06_branch_figures/)
2. Recalculer avec procédure unique:
   - $\overline{P}_{\mathrm{lid}} = \frac{1}{N_t}\sum_{j=1}^{N_t} \sum_i U_{\mathrm{wall},i}^{\mathrm{rec}}(t_j) \tau_{w,i}(t_j) \Delta x$
   - $\delta_P = 100\left(\frac{\overline{P}_{\mathrm{lid}}}{\overline{D}}-1\right)$
3. Utiliser: 64 périodes, vitesse murale récupérée, dérivée unilatérale premier ordre
4. Harmoniser dans 4 endroits:
   - Tableau 4 (manuscrit)
   - Figure 8 (manuscrit)
   - Section 6.4 (manuscrit)
   - S8.7 (supplément)

**Fichiers à modifier:**
- `manuscript_final.tex` (Tableau 4, Section 6.4)
- `supplementary_final.tex` (S8.7)
- `scripts/` (ajouter script de recalcul)

---

### 1.2 Convention temporelle PINN

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
4. Ajouter paragraphe explicite dans S8.5

**Fichiers à modifier:**
- `supplementary_final.tex` (S1.2, S8.5)

---

## 🟡 PRIORITÉ 2: Erreurs éditoriales

### 2.1 Renvois de sections (6 corrections)

| Emplacement | Problème | Correction |
|-------------|----------|------------|
| Introduction, p.3 | « Section 3.2 » pour réponse cycle-moyenne | → « Section 6 » ou « Section 6.2 » |
| Section 3.1, p.5 | « Four stationary profiles » (5 comparés) | → « Five stationary profiles » |
| Section 3.2, p.6 | Comparaison cycle-moyenne attribuée à Sec. 3.2 | → Sec. 6.2 |
| Section 6.1, p.12 | Cite Table S5 et Fig. S8 (obsolètes) | → Tables S15-S16 et Fig. S5 |
| Supplément S8.5, p.20 | Référence « Section 3.3 » (n'existe pas) | → Main Sec. 3.2 |
| Supplément S5, p.10 | Sommaire S5.2/S5.3, sous-sections 5.1/5.2 | → Renommer S5.1 et S5.2 |

**Fichiers à modifier:**
- `manuscript_final.tex` (Introduction, Sections 3.1, 3.2, 6.1)
- `supplementary_final.tex` (S5, S8.5)

### 2.2 Précision terminologique

**Section 3.2:**
- Ajouter: « the eight primary actuation cases summarized in Table 1 »
- Modifier: « The stationary comparison of Sec. 5 uses the mean profile and the cycle-mean comparison of Sec. 6.2 uses the full series »

---

## 🟢 PRIORITÉ 3: Corrections de figures

### 3.1 Figure 3 - Panneau manquant

**Problème:** Légende décrit panneau (c) mais seulement (a) et (b) affichés

**Action:**
- Ajouter panneau (c): normalisation par référence uniforme régularisée
- Valeurs pour $N=512$: $k=1$: 0.823, $k=2$: 1.368, profil moyen B1: 1.443
- Source: Tableau S14

**Fichier à modifier:**
- `scripts/` (script de génération Figure 3)

### 3.2 Figure 1 - Valeur manquante

**Problème:** Annotation montre 4 maxima (0.50, 0.71, 0.71, 0.78) mais 5 profils comparés

**Action:**
- Ajouter 0.52 (profil uniforme régularisé)
- Mettre à jour annotation et légende

**Fichier à modifier:**
- `scripts/make_fig_modes.py` (Figure 1)

### 3.3 Figure 6 - Commande LaTeX imprimée

**Problème:** Texte brut `Fig.~\ref{fig:branch_energy}(a)` visible dans PDF

**Action:**
- Remplacer par référence résolue: « Fig. 8(a) »

**Fichier à modifier:**
- `scripts/` (script de génération Figure 6)

---

## 🔵 PRIORITÉ 4: Nomenclature et cadrage

### 4.1 Corrections nomenclature

**À corriger:**
1. Définition de $D$: ajouter facteur $1/Re$
   - Actuel: $D = \int_\Omega 2\mathbf{S}:\mathbf{S}\,d\Omega$
   - Correct: $D = \frac{2}{Re}\int_\Omega \mathbf{S}:\mathbf{S}\,d\Omega$

2. Ajouter définitions manquantes:
   - $K$ (nombre de modes)
   - $A_\epsilon$ (amplitude)
   - $R_K$ (ratio)

3. Supprimer: PXP (système de soumission, pas scientifique)

**Fichier à modifier:**
- `manuscript_final.tex` (section Nomenclature)

### 4.2 Terminologie « efficacité énergétique »

**Problème:** $E_{\mathrm{act}}$ est norme quadratique, pas travail mécanique

**Action:**
- Remplacer systématiquement:
  - « efficiency » → « energetic response at fixed actuation norm »
  - « control effort » → « quadratic actuation norm »
- Sauf Section 2.2 où c'est déjà correct

**Fichier à modifier:**
- `manuscript_final.tex` (Introduction, Sections 2-3)

### 4.3 Incohérence valeur Fourier

**Problème:**
- S8.5: $1.236 \times 10^{-2}$ (moyenne directe)
- Tableaux principaux: $1.219$ à $1.22 \times 10^{-2}$

**Action:**
- Vérifier s'il s'agit de captures/réalisations différentes
- Rendre la distinction explicite dans le texte

**Fichier à modifier:**
- `supplementary_final.tex` (S8.5, S8.6)

---

## 🟣 PRIORITÉ 5: Réduction du supplément

### 5.1 Contenu à condenser

**Conserver (essentiel pour reproductibilité):**
- Détails architecture PINN et base de contrôle
- Données pour identifier les branches $B_1, B_2, B_3$
- Section S8 complète (vérification indépendante, convergence, bilan énergétique)

**Condenser ou renvoyer à l'article précédent:**
- Campagne 185 réalisations
- Campagne $\lambda_{\mathrm{var}}$
- Ablations
- Capacité du réseau
- Troncature de Fourier
- Rapport d'aspect
- Base de Chebyshev
- Régression symbolique

**Action:**
- Créer section « Additional sensitivity studies » condensée
- Renvoyer à Beniaiche (2026) et dépôt GitHub pour détails
- Réduire supplément de ~27 pages à ~15-18 pages

**Fichier à modifier:**
- `supplementary_final.tex`

---

## 📋 Checklist de vérification finale

### Scientifique
- [ ] Tableau 4 harmonisé avec S8.7
- [ ] Convention temporelle PINN clarifiée
- [ ] Périodicité des champs expliquée
- [ ] Facteur de chaîne dérivée temporelle précisé

### Éditorial
- [ ] 6 renvois de sections corrigés
- [ ] Terminologie « efficacité » remplacée
- [ ] Précision « eight primary cases » ajoutée
- [ ] Phrase Section 3.2 modifiée

### Figures
- [ ] Figure 1: 5 maxima annotés
- [ ] Figure 3: panneau (c) ajouté
- [ ] Figure 6: référence LaTeX résolue

### Nomenclature
- [ ] Facteur $1/Re$ ajouté à $D$
- [ ] $K$, $A_\epsilon$, $R_K$ définis
- [ ] PXP supprimé
- [ ] Incohérence valeur Fourier expliquée

### Supplément
- [ ] Sections PINN condensées
- [ ] Renvois à article précédent ajoutés
- [ ] Section S8 complète conservée
- [ ] Longueur réduite à 15-18 pages

---

## 🎯 Ordre de travail recommandé

1. **Jour 1:** Recalcul bilan énergétique (1.1) + harmonisation
2. **Jour 2:** Clarification convention PINN (1.2)
3. **Jour 3:** Corrections éditoriales (2.1, 2.2)
4. **Jour 4:** Corrections figures (3.1, 3.2, 3.3)
5. **Jour 5:** Nomenclature et terminologie (4.1, 4.2, 4.3)
6. **Jour 6:** Réduction supplément (5.1)
7. **Jour 7:** Vérification finale et compilation

---

## 📝 Notes importantes

- **Ne pas élargir la campagne numérique** - les limites sont reconnues
- **Ne pas choisir arbitrairement** une série de résidus - recalculer
- **Préparer liste de remplacements LaTeX précis** section par section
- **Vérifier cohérence** entre manuscrit et supplément après chaque modification

---

**Prochaine étape:** Commencer par le point 1.1 (bilan énergétique) car c'est le plus critique scientifiquement.
