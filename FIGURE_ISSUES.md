# Problèmes de figures - Documentation

**Date:** 3 novembre 2026  
**Statut:** Corrections nécessitant les scripts originaux

---

## Figure 3 du manuscrit (fig12_gci_updated dans figures/)

### Problème identifié par le reviewer

La figure montre actuellement seulement les panneaux (a) et (b), mais sa légende décrit également un panneau (c), normalisé par la référence uniforme régularisée.

### Valeurs manquantes pour le panneau (c)

Pour $N=512$, les valeurs sont (selon le reviewer, source: Tableau S14):
- $k=1$: 0.823
- $k=2$: 1.368
- Profil moyen B1: 1.443

### Action requise

1. Localiser le script de génération de cette figure (probablement dans l'ancien dépôt complet)
2. Ajouter un troisième panneau (c) avec normalisation par la référence uniforme régularisée
3. Utiliser les valeurs du Tableau S14 pour $N=512$

### Fichier concerné

- `figures/fig12_gci_updated.pdf` et `figures/fig12_gci_updated.png`
- Script de génération: non disponible dans le dépôt épuré

---

## Figure 6 du manuscrit (fig20_branch_topology dans figures/)

### Problème identifié par le reviewer

Dans l'annotation de la figure, page 14 du PDF, le texte brut `Fig.~\ref{fig:branch_energy}(a)` apparaît dans le PDF au lieu d'une référence résolue.

### Action requise

1. Localiser le script de génération de cette figure
2. Remplacer le texte LaTeX brut par une référence résolue: « Fig. 8(a) »
3. Régénérer la figure

### Fichier concerné

- `figures/fig20_branch_topology.pdf` et `figures/fig20_branch_topology.png`
- Script de génération: non disponible dans le dépôt épuré

---

## Figures supplémentaires

### Figure S5 et S6

Ces figures existent dans le dossier figures/:
- `figures/figS5_branch_topology_phases.pdf/png`
- `figures/figS6_branch_topology_panelscale.pdf/png`

Aucun problème signalé par le reviewer pour ces figures.

---

## Recommandations

### Option 1: Récupérer les scripts originaux

Les scripts de génération des figures 3-8 du manuscrit ne sont pas dans le dépôt épuré. Ils se trouvent probablement dans:
- L'ancien dépôt complet (1.5 GB avec tous les résultats)
- Le répertoire `scripts/` de l'ancienne version

### Option 2: Recréer les figures

Si les scripts originaux ne sont pas disponibles, il faut recréer les figures à partir des données brutes. Cela nécessite:
- Accès aux fichiers de résultats complets
- Connaissance de la structure exacte des données
- Temps de développement pour recréer les visualisations

### Option 3: Corrections manuelles minimales

Pour la Figure 6, une correction rapide serait possible si on peut éditer le PDF directement pour remplacer le texte LaTeX brut par « Fig. 8(a) ». Cependant, cette approche n'est pas recommandée car:
- Elle ne résout pas la cause racine
- Elle rend la figure non reproductible
- Elle peut introduire des artefacts visuels

---

## Priorité

**Figure 6** est plus critique car elle contient une erreur visible (texte LaTeX brut).

**Figure 3** est moins critique car le panneau manquant est une amélioration plutôt qu'une correction d'erreur.

---

## Note pour les auteurs

Pour compléter ces corrections, veuillez:
1. Fournir les scripts de génération des figures 3 et 6 (fig12_gci_updated et fig20_branch_topology)
2. Ou autoriser la recréation de ces figures à partir des données brutes
3. Ou fournir les figures corrigées directement

---

**Dernière mise à jour:** 3 novembre 2026
