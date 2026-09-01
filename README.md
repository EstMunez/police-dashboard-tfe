# Police Dashboard — TFE

## Présentation

Ce projet a été réalisé dans le cadre de mon Travail de Fin d'Études (TFE) en Bachelier en informatique, orientation développement d'applications, à l'IFOSUP Wavre.

L'objectif du projet est de concevoir une application web permettant d'importer, d'analyser et de visualiser dynamiquement des données provenant de fichiers Excel.

L'application propose notamment une analyse automatique des données, des indicateurs synthétiques, des représentations graphiques et une visualisation cartographique lorsque les données nécessaires sont disponibles.

> Ce dépôt correspond à un projet académique. Les fichiers de données opérationnelles utilisés dans le cadre du projet ne sont pas publiés dans ce dépôt.

---

## Fonctionnalités principales

- Importation de fichiers Excel au format `.xlsx`
- Détection des feuilles disponibles
- Sélection d'une feuille de travail
- Lecture et nettoyage des données avec pandas
- Détection du type et du rôle des colonnes
- Génération d'indicateurs clés (KPI)
- Analyse automatique des colonnes pertinentes
- Génération dynamique de graphiques
- Analyse personnalisée à partir des colonnes sélectionnées
- Importation facultative d'un référentiel géographique
- Mise en correspondance des zones géographiques
- Visualisation cartographique interactive
- Gestion des erreurs liées aux fichiers et aux données
- API documentée automatiquement avec FastAPI
- Tests automatisés avec pytest

---

## Technologies utilisées

### Backend

- Python
- FastAPI
- pandas
- openpyxl

### Frontend

- HTML
- CSS
- JavaScript
- Chart.js

### Cartographie

- Leaflet
- OpenStreetMap

### Tests

- pytest

---

## Structure du projet

```text
police_dashboard/
├── app/
│   ├── api/
│   │   ├── dashboard.py
│   │   └── imports.py
│   ├── services/
│   │   ├── analysis_service.py
│   │   └── excel_service.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── chart.js
│   └── templates/
│       ├── dashboard.html
│       ├── conditions_utilisation.html
│       └── mentions_legales.html
├── tests/
├── main.py
├── pytest.ini
├── requirements.txt
├── README_TESTS.txt
├── README.md
└── .gitignore
```

---

## Installation

### 1. Récupérer le projet

Cloner le dépôt Git :

```bash
git clone <URL_DU_DEPOT>
```

Puis accéder au dossier :

```bash
cd police-dashboard-tfe
```

### 2. Créer un environnement virtuel

Sous Windows :

```bash
python -m venv .venv
```

Activation avec PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Lancement de l'application

Depuis la racine du projet :

```bash
uvicorn main:app --reload
```

Le serveur de développement est alors accessible localement.

### Dashboard

```text
http://127.0.0.1:8000/dashboard-page
```

### Documentation interactive de l'API

```text
http://127.0.0.1:8000/docs
```
## Jeu de données de démonstration

Afin de permettre de tester l'application sans utiliser de données
opérationnelles réelles, un jeu de données entièrement synthétique est
fourni avec le projet.

Le fichier est disponible dans :

`demo/jeu_donnees_tfe_multifeuilles_quartiers.xlsx`

Ce classeur contient plusieurs feuilles présentant volontairement des
structures différentes :

- `Faits_2024` : données fictives pour l'année 2024 ;
- `Faits_2025` : données fictives avec une structure légèrement différente ;
- `Faits_2026` : données fictives sans mesure numérique explicite ;
- `Incidents_test` : données synthétiques permettant de tester d'autres types de colonnes ;
- `Cas_limites` : valeurs manquantes, doublons, valeur atypique et zone volontairement inconnue ;
- `Referentiel_quartiers` : référentiel géographique utilisé pour les tests cartographiques ;
- `Lisez_moi` : description du contenu du classeur.

Les noms des quartiers utilisés dans le jeu de démonstration correspondent
au référentiel géographique de test afin de permettre la génération de la
carte.

> **Important :** toutes les données contenues dans ce fichier sont
> synthétiques et ont été créées uniquement à des fins de test et de
> démonstration. Aucune donnée policière opérationnelle ou donnée
> personnelle réelle n'est publiée dans ce dépôt.
---

## Utilisation

Le fonctionnement général de l'application est le suivant :

1. L'utilisateur importe un fichier Excel `.xlsx`.
2. L'application détecte les feuilles disponibles.
3. L'utilisateur sélectionne la feuille à analyser.
4. L'application charge et prépare les données.
5. L'utilisateur peut lancer l'analyse automatique.
6. Des KPI, graphiques et interprétations sont générés.
7. Une analyse personnalisée peut également être réalisée.
8. Un référentiel géographique peut être importé pour activer la représentation cartographique lorsque les données sont compatibles.

### Test rapide avec les données de démonstration

Pour tester l'application :

1. Lancer le serveur avec `uvicorn main:app --reload`.
2. Ouvrir `http://127.0.0.1:8000/dashboard-page`.
3. Importer `demo/jeu_donnees_tfe_multifeuilles_quartiers.xlsx`.
4. Sélectionner l'une des feuilles de données.
5. Lancer l'analyse automatique.
6. Tester les graphiques et les indicateurs générés.
7. Pour la cartographie, utiliser la feuille `Referentiel_quartiers`
   comme référentiel géographique.
---

## Tests

Les tests automatisés peuvent être exécutés avec :

```bash
python -m pytest -v
```

Les tests portent notamment sur les services d'analyse, la lecture des fichiers Excel, les routes d'importation et certaines fonctionnalités du dashboard.

Une documentation complémentaire concernant les tests est disponible dans :

```text
README_TESTS.txt
```

---

## Données et confidentialité

Les fichiers contenant les données métier ou opérationnelles ne sont pas versionnés dans le dépôt Git.

Le fichier `.gitignore` exclut notamment les fichiers Excel importés, les environnements virtuels, les fichiers temporaires et les éléments propres à l'environnement de développement.

L'application est développée dans un cadre académique et ne constitue pas un système officiel de production.

---

## Auteur

**Esther Mwiseneza Munezero**

Travail de Fin d'Études — Bachelier en informatique, orientation développement d'applications  
IFOSUP Wavre — Année académique 2025–2026