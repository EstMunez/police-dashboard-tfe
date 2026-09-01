from __future__ import annotations

from typing import Any

import pandas as pd


def json_number(value: Any) -> int | float:
    """Convertit une valeur Pandas/NumPy en nombre compatible JSON."""
    if pd.isna(value):
        return 0

    number = float(value)

    if number.is_integer():
        return int(number)

    return round(number, 2)


def clean_text(series: pd.Series) -> pd.Series:
    """Nettoie une colonne textuelle."""
    return (
        series
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
        .replace("", "Non renseigné")
    )


def detect_column_type(series: pd.Series) -> str:
    """
    Détecte automatiquement le type d'une colonne.
    """

    non_empty = series.dropna()

    if non_empty.empty:
        return "empty"

    # Date déjà reconnue par Pandas
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # Colonne numérique
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    text_values = non_empty.astype(str).str.strip()

    # Test numérique
    numeric_values = pd.to_numeric(
        text_values.str.replace(",", ".", regex=False),
        errors="coerce"
    )

    if numeric_values.notna().mean() >= 0.90:
        return "numeric"

    # Test date
    date_values = pd.to_datetime(
        text_values,
        errors="coerce",
        dayfirst=True
    )

    if date_values.notna().mean() >= 0.80:
        return "date"

    # Test catégorie
    distinct_count = text_values.nunique()

    distinct_rate = (
        distinct_count / len(text_values)
        if len(text_values) > 0
        else 0
    )

    if distinct_count <= 100 and distinct_rate <= 0.60:
        return "categorical"

    return "text"


def profile_columns(
    df: pd.DataFrame
) -> list[dict]:

    profile = []

    row_count = len(df)

    for column in df.columns:

        series = df[column]

        column_type = detect_column_type(
            series
        )

        distinct_count = int(
            series.nunique(dropna=True)
        )

        role = detect_column_role(
            column_name=str(column),
            column_type=column_type,
            distinct_count=distinct_count,
            row_count=row_count,
        )

        missing_rate = round(
            series.isna().mean() * 100,
            2
        )

        score = calculate_analysis_score(
            role=role,
            distinct_count=distinct_count,
            row_count=row_count,
            missing_rate=missing_rate,
        )

        profile.append({
            "name": str(column),
            "type": column_type,
            "role": role,
            "score": score,
            "distinct_count": distinct_count,
            "missing_count": int(
                series.isna().sum()
            ),
            "missing_rate": missing_rate,
        })

    return profile


def select_category_column(profile: list[dict]) -> str | None:
    """Choisit automatiquement une colonne catégorielle."""

    candidates = [
        column
        for column in profile
        if column["type"] == "categorical"
        and 2 <= column["distinct_count"] <= 50
    ]

    if not candidates:
        candidates = [
            column
            for column in profile
            if column["type"] in {"categorical", "text"}
            and column["distinct_count"] >= 2
        ]

    if not candidates:
        return None

    # On privilégie une catégorie possédant
    # un nombre raisonnable de valeurs.
    candidates.sort(
        key=lambda column: column["distinct_count"]
    )

    return candidates[0]["name"]


def select_numeric_column(
    profile: list[dict]
) -> str | None:
    """
    Sélectionne automatiquement la meilleure mesure numérique.

    Les coordonnées géographiques, années, identifiants
    et autres colonnes techniques ne doivent pas être
    utilisées comme mesures statistiques.
    """

    excluded_keywords = [
        "latitude",
        "longitude",
        "lat",
        "lng",
        "lon",
        "année",
        "annee",
        "year",
        "id",
        "code",
        "zip",
        "postal",
    ]

    preferred_keywords = [
        "nombre",
        "nb",
        "total",
        "quantité",
        "quantite",
        "count",
        "amount",
        "montant",
        "valeur",
        "value",
        "effectif",
    ]

    candidates = []

    for column in profile:

        if column["type"] != "numeric":
            continue

        name = column["name"].lower().strip()

        # Exclure les colonnes techniques
        if any(
            keyword == name or keyword in name
            for keyword in excluded_keywords
        ):
            continue

        candidates.append(column)

    if not candidates:
        return None

    # Priorité aux colonnes ressemblant à une mesure
    for column in candidates:

        name = column["name"].lower().strip()

        if any(
            keyword in name
            for keyword in preferred_keywords
        ):
            return column["name"]

    # Sinon on utilise la première colonne numérique exploitable
    return candidates[0]["name"]


def select_date_column(profile: list[dict]) -> str | None:
    """Choisit automatiquement une colonne de date."""

    candidates = [
        column
        for column in profile
        if column["type"] == "date"
    ]

    if not candidates:
        return None

    return candidates[0]["name"]


def build_distribution(
    df: pd.DataFrame,
    category_column: str,
    value_column: str | None = None,
    top: int = 10,
) -> dict:

    categories = clean_text(
        df[category_column]
    )

    if value_column:

        values = pd.to_numeric(
            df[value_column],
            errors="coerce"
        ).fillna(0)

        work = pd.DataFrame({
            "category": categories,
            "value": values
        })

        full_result = (
            work
            .groupby("category")["value"]
            .sum()
            .sort_values(ascending=False)
        )

        result = full_result.head(10)

        full_total = full_result.sum()

        calculation = "sum"

    else:

        full_result = (
            categories
            .value_counts()
        )

        result = full_result.head(10)

        full_total = full_result.sum()

        calculation = "count"

    return {
        "labels": [
            str(label)
            for label in result.index
        ],
        "values": [
            json_number(value)
            for value in result.values
        ],
        "calculation": calculation
    }


def build_time_series(
    df: pd.DataFrame,
    date_column: str,
    value_column: str | None = None,
) -> dict:

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce",
        dayfirst=True
    )

    work = df.copy()

    work["_date"] = dates

    work = work.dropna(
        subset=["_date"]
    )

    if work.empty:
        return {
            "labels": [],
            "values": []
        }

    date_range = (
        work["_date"].max()
        - work["_date"].min()
    ).days

    if date_range > 730:

        work["_period"] = (
            work["_date"].dt.to_period("Y")
        )

        frequency = "année"

    elif date_range > 90:

        work["_period"] = (
            work["_date"].dt.to_period("M")
        )

        frequency = "mois"

    else:

        work["_period"] = (
            work["_date"].dt.to_period("D")
        )

        frequency = "jour"

    if value_column:

        work["_value"] = pd.to_numeric(
            work[value_column],
            errors="coerce"
        ).fillna(0)

        result = (
            work
            .groupby("_period")["_value"]
            .sum()
            .sort_index()
        )

    else:

        result = (
            work
            .groupby("_period")
            .size()
            .sort_index()
        )

    return {
        "labels": [
            str(period)
            for period in result.index
        ],
        "values": [
            json_number(value)
            for value in result.values
        ],
        "frequency": frequency
    }
def select_analysis_columns(
    profile: list[dict]
) -> list[str]:
    """
    Sélectionne automatiquement plusieurs colonnes intéressantes
    pour produire des analyses et graphiques.
    """

    candidates = []

    for column in profile:
        column_type = column.get("type")
        distinct_count = column.get("distinct_count", 0)
        column_name = column.get("name")

        if not column_name:
            continue

        # Colonne vide ou constante = inutile pour un graphique
        if column_type == "empty" or distinct_count <= 1:
            continue

        # Colonnes catégorielles
        if (
            column_type == "categorical"
            and distinct_count <= 30
        ):
            candidates.append(column_name)

        # Colonnes textuelles :
        # utile par exemple pour Rue, Localité, Lieu...
        elif (
            column_type == "text"
            and distinct_count <= 200
        ):
            candidates.append(column_name)

    return candidates

def build_analysis_interpretation(
        column: str,
        labels: list[str],
        values: list,
        calculation: str,
        full_total: float | int,
) -> dict:
    """
    Génère une interprétation statistique simple
    et générique d'une répartition.

    Aucun nom de colonne particulier n'est imposé.
    """

    if not labels or not values:
        return {
            "summary": "Aucune donnée exploitable.",
            "top_label": None,
            "top_value": 0,
            "top_percentage": 0,
        }

    numeric_values = [
        float(value)
        for value in values
    ]

    total = float(full_total)

    if total <= 0:
        return {
            "summary": "Les valeurs disponibles ne permettent pas de calculer une répartition.",
            "top_label": None,
            "top_value": 0,
            "top_percentage": 0,
        }

    # La première valeur est normalement
    # déjà la plus importante.
    top_label = str(labels[0])
    top_value = numeric_values[0]

    top_percentage = round(
        (top_value / total) * 100,
        1
    )

    # ------------------------------------------
    # Niveau de concentration
    # ------------------------------------------

    if top_percentage >= 75:
        concentration = "très fortement concentrée"

    elif top_percentage >= 50:
        concentration = "majoritairement concentrée"

    elif top_percentage >= 30:
        concentration = "principalement représentée"

    else:
        concentration = "répartie entre plusieurs catégories"

    # ------------------------------------------
    # Phrase automatique
    # ------------------------------------------

    if calculation == "count":
        summary = (
            f"La catégorie « {top_label} » est la plus représentée "
            f"avec {json_number(top_value)} enregistrement(s), "
            f"soit {top_percentage} % des données affichées. "
            f"La répartition est {concentration}."
        )

    else:
        summary = (
            f"La catégorie « {top_label} » représente la valeur "
            f"la plus importante avec {json_number(top_value)}, "
            f"soit {top_percentage} % du total affiché. "
            f"La répartition est {concentration}."
        )

    return {
        "summary": summary,
        "top_label": top_label,
        "top_value": json_number(top_value),
        "top_percentage": top_percentage,
        "displayed_total": json_number(total),
    }

def build_multiple_analyses(
    df: pd.DataFrame,
    profile: list[dict],
    value_column: str | None,
    max_analyses: int = 5,
) -> list[dict]:
    """
    Génère automatiquement plusieurs analyses pertinentes
    à partir des colonnes détectées.

    Les colonnes sont classées par score de pertinence.
    Seules les meilleures analyses sont conservées.
    """

    analyses = []

    # -------------------------------------------------
    # Sélectionner uniquement les colonnes analysables
    # -------------------------------------------------

    candidates = []

    for column_info in profile:
        column_name = column_info.get("name")
        role = column_info.get("role")
        score = column_info.get("score", 0)
        distinct_count = column_info.get("distinct_count", 0)

        if not column_name:
            continue

        if column_name not in df.columns:
            continue

        # Colonnes sans intérêt statistique
        if distinct_count <= 1:
            continue

        # Coordonnées et identifiants :
        # utiles ailleurs, mais pas comme graphique classique
        if role in {
            "latitude",
            "longitude",
            "identifier",
            "numeric_identifier",
            "measure",
            "numeric",
            "temporal",
            "date",
            "unknown",
        }:
            continue

        # On écarte les colonnes ayant un score nul ou négatif
        if score <= 0:
            continue

        candidates.append(column_info)

    # -------------------------------------------------
    # Trier du plus pertinent au moins pertinent
    # -------------------------------------------------

    candidates.sort(
        key=lambda item: item.get("score", 0),
        reverse=True
    )

    # -------------------------------------------------
    # Limiter le nombre de graphiques automatiques
    # -------------------------------------------------

    candidates = candidates[:max_analyses]

    # -------------------------------------------------
    # Construire les analyses
    # -------------------------------------------------

    for column_info in candidates:

        column = column_info["name"]
        role = column_info.get("role")
        score = column_info.get("score", 0)

        categories = clean_text(df[column])

        if value_column and value_column in df.columns:

            numeric_values = pd.to_numeric(
                df[value_column],
                errors="coerce"
            ).fillna(0)

            work = pd.DataFrame({
                "category": categories,
                "value": numeric_values
            })

            # Résultat complet
            full_result = (
                work
                .groupby("category")["value"]
                .sum()
                .sort_values(ascending=False)
            )

            # Total réel sur toutes les catégories
            full_total = float(full_result.sum())

            # Seulement le Top 10 pour le graphique
            result = full_result.head(10)

            calculation = "sum"

        else:

            # Résultat complet
            full_result = (
                categories
                .value_counts()
            )

            # Total réel sur toutes les catégories
            full_total = float(full_result.sum())

            # Seulement le Top 10 pour le graphique
            result = full_result.head(10)

            calculation = "count"

        if result.empty:
            continue

        # -------------------------------------------------
        # Choisir un type de graphique conseillé
        # -------------------------------------------------

        number_of_values = len(result)

        if role == "location":
            chart_type = "bar"

        elif number_of_values <= 5:
            chart_type = "doughnut"

        else:
            chart_type = "bar"

        labels = [
            str(label)
            for label in result.index
        ]

        values = [
            json_number(value)
            for value in result.values
        ]

        interpretation = build_analysis_interpretation(
            column=str(column),
            labels=labels,
            values=values,
            calculation=calculation,
            full_total=full_total,
        )


        # -------------------------------------------------
        # Créer l'analyse
        # -------------------------------------------------

        analyses.append({
            "column": str(column),

            "title": f"Répartition par {column}",

            "role": role,

            "score": score,

            "chart_type": chart_type,

            "labels": labels,

            "values": values,

            "calculation": calculation,

            "interpretation": interpretation,
        })

    return analyses


def detect_column_role(
    column_name: str,
    column_type: str,
    distinct_count: int,
    row_count: int,
) -> str:
    """
    Détermine le rôle probable d'une colonne.

    Le moteur combine :
    - le type détecté ;
    - le nombre de valeurs distinctes ;
    - la proportion de valeurs uniques ;
    - quelques indices sémantiques dans le nom.

    Les noms ne sont pas obligatoires :
    ils servent uniquement d'indice supplémentaire.
    """

    name = str(column_name).lower().strip()

    unique_ratio = (
        distinct_count / row_count
        if row_count > 0
        else 0
    )

    # -----------------------------------------
    # Coordonnées géographiques
    # -----------------------------------------

    latitude_keywords = [
        "latitude",
        "lat",
    ]

    longitude_keywords = [
        "longitude",
        "lng",
        "lon",
    ]

    if any(
        keyword == name or keyword in name
        for keyword in latitude_keywords
    ):
        return "latitude"

    if any(
        keyword == name or keyword in name
        for keyword in longitude_keywords
    ):
        return "longitude"

    # -----------------------------------------
    # Temps
    # -----------------------------------------

    if column_type == "date":
        return "date"

    temporal_keywords = [
        "année",
        "annee",
        "year",
        "mois",
        "month",
        "jour",
        "date",
        "heure",
        "time",
    ]

    if any(
        keyword in name
        for keyword in temporal_keywords
    ):
        return "temporal"

    # -----------------------------------------
    # Identifiants / colonnes techniques
    # -----------------------------------------

    identifier_keywords = [
        "id",
        "identifiant",
        "index",
        "numero",
        "numéro",
        "reference",
        "référence",
    ]

    if any(
        keyword == name or
        name.startswith(f"{keyword} ")
        for keyword in identifier_keywords
    ):
        return "identifier"

    # -----------------------------------------
    # Localisation
    # -----------------------------------------

    location_keywords = [
        "rue",
        "adresse",
        "lieu",
        "localité",
        "localite",
        "quartier",
        "commune",
        "ville",
        "zone",
        "secteur",
    ]

    if any(
        keyword in name
        for keyword in location_keywords
    ):
        return "location"

    # -----------------------------------------
    # Mesures
    # -----------------------------------------

    measure_keywords = [
        "nombre",
        "nb",
        "total",
        "quantité",
        "quantite",
        "montant",
        "effectif",
        "count",
        "amount",
        "value",
        "valeur",
    ]

    if (
        column_type == "numeric"
        and any(
            keyword in name
            for keyword in measure_keywords
        )
    ):
        return "measure"

    # -----------------------------------------
    # Catégories
    # -----------------------------------------

    if column_type == "categorical":
        return "category"

    # Peu de valeurs différentes =
    # probablement une dimension catégorielle.
    if (
        column_type == "text"
        and 2 <= distinct_count <= 30
    ):
        return "category"

    # -----------------------------------------
    # Texte à forte cardinalité
    # -----------------------------------------

    if column_type == "text":
        return "text"

    # -----------------------------------------
    # Numérique générique
    # -----------------------------------------

    if column_type == "numeric":

        # Une colonne presque unique par ligne
        # ressemble davantage à un identifiant.
        if unique_ratio >= 0.95:
            return "numeric_identifier"

        return "numeric"

    return "unknown"

def calculate_analysis_score(
    role: str,
    distinct_count: int,
    row_count: int,
    missing_rate: float,
) -> int:
    """
    Calcule un score de pertinence pour déterminer
    si une colonne mérite d'être représentée.

    Plus le score est élevé, plus l'analyse est intéressante.
    """

    score = 0

    if row_count <= 0:
        return score

    unique_ratio = distinct_count / row_count

    # -----------------------------------------
    # Importance selon le rôle
    # -----------------------------------------

    role_scores = {
        "category": 50,
        "location": 45,
        "temporal": 40,
        "date": 40,
        "measure": 30,
        "numeric": 20,
        "text": 10,

        # À ne normalement pas analyser
        "latitude": -100,
        "longitude": -100,
        "identifier": -100,
        "numeric_identifier": -100,
        "unknown": 0,
    }

    score += role_scores.get(role, 0)

    # -----------------------------------------
    # Nombre de catégories
    # -----------------------------------------

    if distinct_count <= 1:
        score -= 100

    elif 2 <= distinct_count <= 5:
        score += 30

    elif 6 <= distinct_count <= 15:
        score += 25

    elif 16 <= distinct_count <= 30:
        score += 15

    elif 31 <= distinct_count <= 100:
        score += 5

    else:
        score -= 10

    # -----------------------------------------
    # Beaucoup de valeurs uniques
    # -----------------------------------------

    if unique_ratio >= 0.95:
        score -= 25

    elif unique_ratio >= 0.75:
        score -= 10

    # -----------------------------------------
    # Données manquantes
    # -----------------------------------------

    if missing_rate >= 50:
        score -= 30

    elif missing_rate >= 25:
        score -= 15

    elif missing_rate >= 10:
        score -= 5

    return score


def analyze_dataframe(df: pd.DataFrame) -> dict:
    """
    Analyse automatiquement une feuille Excel
    sans dépendre du nom de ses colonnes.
    """

    if df.empty:
        return {
            "has_data": False,
            "message": "Cette feuille ne contient aucune donnée."
        }

    profile = profile_columns(df)

    category_column = select_category_column(
        profile
    )

    numeric_column = select_numeric_column(
        profile
    )

    date_column = select_date_column(
        profile
    )

    # -------------------------
    # KPI
    # -------------------------

    records = int(len(df))

    if numeric_column:

        numeric_values = pd.to_numeric(
            df[numeric_column],
            errors="coerce"
        ).fillna(0)

        total = json_number(
            numeric_values.sum()
        )

    else:

        total = records

    distinct_categories = 0
    top_category = None

    # -------------------------
    # Distribution
    # -------------------------

    distribution = {
        "labels": [],
        "values": []
    }

    if category_column:

        distribution = build_distribution(
            df,
            category_column,
            numeric_column
        )

        distinct_categories = int(
            clean_text(
                df[category_column]
            ).nunique()
        )

        if distribution["labels"]:
            top_category = (
                distribution["labels"][0]
            )

    # -------------------------
    # Analyse temporelle
    # -------------------------

    time_series = {
        "labels": [],
        "values": []
    }

    if date_column:

        time_series = build_time_series(
            df,
            date_column,
            numeric_column
        )

    automatic_analyses = build_multiple_analyses(
        df=df,
        profile=profile,
        value_column=numeric_column
    )

    # -------------------------
    # Réponse
    # -------------------------

    return {
        "has_data": True,

        "kpis": {
            "records": records,
            "total": total,
            "distinct_categories":
                distinct_categories,
            "top_category":
                top_category
        },

        "detected_columns": {
            "category":
                category_column,
            "numeric":
                numeric_column,
            "date":
                date_column
        },

        "distribution":
            distribution,

        "time_series":
            time_series,

        "profile":
            profile,

        "automatic_analyses":
            automatic_analyses
    }

