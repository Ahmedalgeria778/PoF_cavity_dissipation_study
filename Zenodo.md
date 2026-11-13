# Instructions pour créer un DOI via Zenodo

Ce document explique comment obtenir un DOI (Digital Object Identifier) permanent pour ce dépôt de recherche via Zenodo.

## 🎯 Qu'est-ce que Zenodo?

Zenodo est une plateforme de dépôt ouverte développée par le CERN qui:
- Attribue des DOI permanents aux dépôts de recherche
- Assure l'archivage à long terme
- Permet la citation formelle des logiciels et données
- Est gratuit et ouvert à tous les chercheurs

## 📋 Prérequis

- Un compte GitHub (déjà configuré)
- Un compte Zenodo (à créer)
- Le dépôt GitHub doit être public ✅ (déjà fait)

## 🚀 Étapes pour créer le DOI

### Étape 1: Créer un compte Zenodo

1. Aller sur https://zenodo.org/
2. Cliquer sur **"Sign up"** en haut à droite
3. Choisir **"Log in with GitHub"** pour lier les comptes
4. Autoriser Zenodo à accéder à votre compte GitHub

### Étape 2: Activer l'intégration GitHub-Zenodo

1. Une fois connecté, aller sur https://zenodo.org/account/settings/github/
2. Vous verrez la liste de vos dépôts GitHub
3. Trouver **Ahmedalgeria778/PoF_cavity_dissipation_study**
4. Cliquer sur le bouton **ON** (interrupteur) à côté du dépôt
5. Zenodo va maintenant surveiller ce dépôt

### Étape 3: Créer une release GitHub

1. Aller sur https://github.com/Ahmedalgeria778/PoF_cavity_dissipation_study
2. Cliquer sur **"Releases"** (à droite, sous "About")
3. Cliquer sur **"Create a new release"**
4. Remplir les informations:
   - **Tag version:** `v1.0.0`
   - **Release title:** `Initial release - v1.0.0`
   - **Description:**
     ```
     First public release of the complete study:
     - Main manuscript (clean and marked-up versions)
     - Supplementary material (clean and marked-up versions)
     - Response to editor letter
     - All figures (26 figures in PDF and PNG)
     - Analysis and visualization scripts
     - Documentation (README, LICENSE, CITATION)
     ```
5. Cliquer sur **"Publish release"**

### Étape 4: Zenodo crée automatiquement le DOI

1. Dès que la release est publiée, Zenodo détecte automatiquement le changement
2. Zenodo archive la release et crée un DOI permanent
3. Le DOI apparaît sur la page Zenodo du dépôt
4. Format du DOI: `10.5281/zenodo.XXXXXXX`

### Étape 5: Récupérer le DOI

1. Aller sur https://zenodo.org/
2. Chercher votre dépôt ou aller dans vos dépôts
3. Le DOI est affiché en haut de la page
4. Exemple: `10.5281/zenodo.1234567`

## 📝 Mettre à jour le README avec le DOI

Une fois le DOI obtenu, mettre à jour le fichier README.md:

### Ajouter le badge DOI

Remplacer la ligne:
```markdown
[![Physics of Fluids](https://img.shields.io/badge/Journal-Physics%20of%20Fluids-blue.svg)](https://aip.scitation.org/journal/phf)
```

Par:
```markdown
[![Physics of Fluids](https://img.shields.io/badge/Journal-Physics%20of%20Fluids-blue.svg)](https://aip.scitation.org/journal/phf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

(Remplacer `10.5281/zenodo.XXXXXXX` par votre vrai DOI)

### Mettre à jour la section Citation

Remplacer la section Citation du README par:
```markdown
## Citation

If you use this work, please cite:

```bibtex
@software{beniaiche2026_pof_cavity_dissipation,
  author       = {Beniaiche, Ahmed and Larabi, Abderrahim and Belkadi, Mebarek},
  title        = {Spatio-temporal wall-actuation modes and cycle-mean viscous dissipation in a lid-driven cavity},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {v1.0.0},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

Et pour l'article:

```bibtex
@article{beniaiche2026spatiotemporal,
  title={Spatio-temporal wall-actuation modes and cycle-mean viscous dissipation in a lid-driven cavity},
  author={Beniaiche, Ahmed and Larabi, Abderrahim and Belkadi, Mebarek},
  journal={Physics of Fluids},
  year={2026},
  publisher={AIP Publishing}
}
```
```

## 🔄 Créer une nouvelle version (release)

Pour chaque nouvelle version du dépôt:

1. **Créer une nouvelle release GitHub:**
   - Tag: `v1.1.0`, `v2.0.0`, etc.
   - Description des changements

2. **Zenodo crée automatiquement un nouveau DOI:**
   - Chaque release a son propre DOI versionné
   - Un DOI conceptuel pointe vers la dernière version

3. **Mettre à jour CITATION.cff:**
   ```yaml
   version: 1.1.0
   date-released: 2026-11-15
   ```

## 📊 Types de DOI Zenodo

Zenodo attribue deux types de DOI:

1. **DOI Conceptuel:** `10.5281/zenodo.1234567`
   - Pointe toujours vers la dernière version
   - À utiliser dans les citations générales

2. **DOI Versionné:** `10.5281/zenodo.1234568`
   - Pointe vers une version spécifique
   - À utiliser pour la reproductibilité exacte

## ✅ Avantages du DOI

- **Permanent:** Ne change jamais, même si le dépôt est supprimé
- **Citable:** Format standard pour les publications scientifiques
- **Archivé:** Zenodo archive chaque version indéfiniment
- **Reconnu:** Accepté par tous les éditeurs scientifiques
- **Gratuit:** Service gratuit du CERN

## 🔗 Liens utiles

- Zenodo: https://zenodo.org/
- Documentation Zenodo: https://help.zenodo.org/
- Intégration GitHub: https://zenodo.org/account/settings/github/
- Guide DOI: https://www.doi.org/the-identifier/what-is-a-doi/

## 📧 Support

Pour toute question sur Zenodo:
- Email: info@zenodo.org
- Documentation: https://help.zenodo.org/

---

**Dernière mise à jour:** Novembre 2026
