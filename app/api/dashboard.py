from __future__ import annotations

from typing import Any

from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.excel_service import get_sheet_names, load_excel_data
from app.services.analysis_service import analyze_dataframe


router = APIRouter()


def json_number(value: Any) -> int | float:
    """Convertit les nombres Pandas/NumPy en nombres compatibles JSON."""
    if pd.isna(value):
        return 0

    number = float(value)
    return int(number) if number.is_integer() else round(number, 2)


def clean_text(series: pd.Series) -> pd.Series:
    """Nettoie une colonne utilisée comme catégorie ou filtre."""
    return (
        series
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
        .replace("", "Non renseigné")
    )


def apply_filters(
    df: pd.DataFrame,
    filter1_col: str | None = None,
    filter1_val: str | None = None,
    filter2_col: str | None = None,
    filter2_val: str | None = None,
) -> pd.DataFrame:
    """Applique au maximum deux filtres dynamiques."""
    result = df.copy()

    filters = [
        (filter1_col, filter1_val),
        (filter2_col, filter2_val),
    ]

    for column, value in filters:
        if not column or value in (None, ""):
            continue

        if column not in result.columns:
            raise HTTPException(
                status_code=400,
                detail=f"La colonne '{column}' n'existe pas."
            )

        result = result[
            clean_text(result[column]) == str(value).strip()
        ]

    return result


def get_values(
    df: pd.DataFrame,
    value_column: str | None,
) -> pd.Series:
    """
    Utilise la colonne numérique sélectionnée.

    Si aucune colonne n'est choisie, chaque ligne vaut 1.
    """
    if not value_column:
        return pd.Series(1.0, index=df.index)

    if value_column not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"La colonne '{value_column}' n'existe pas."
        )

    return pd.to_numeric(
        df[value_column],
        errors="coerce"
    ).fillna(0)


@router.get("/sheets")
def get_sheets():
    """Retourne les feuilles du fichier Excel importé."""
    return {"sheets": get_sheet_names()}


@router.get("/columns")
def get_columns(sheet_name: str | None = None):
    """Retourne les colonnes de la feuille sélectionnée."""
    df = load_excel_data(sheet_name)

    if df.empty:
        return {
            "columns": [],
            "numeric_columns": [],
        }

    numeric_columns = []

    for column in df.columns:
        converted = pd.to_numeric(df[column], errors="coerce")

        if converted.notna().mean() >= 0.90:
            numeric_columns.append(str(column))

    return {
        "columns": [str(column) for column in df.columns],
        "numeric_columns": numeric_columns,
    }


@router.get("/column-values")
def get_column_values(
    column: str,
    sheet_name: str | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Retourne les valeurs distinctes d'une colonne."""
    df = load_excel_data(sheet_name)

    if df.empty:
        return {"values": []}

    if column not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"La colonne '{column}' n'existe pas."
        )

    values = clean_text(df[column]).unique().tolist()
    values = sorted(values, key=str.casefold)

    return {"values": values[:limit]}


@router.get("/kpis")
def get_kpis(
    sheet_name: str | None = None,
    category_column: str | None = None,
    value_column: str | None = None,
    filter1_col: str | None = None,
    filter1_val: str | None = None,
    filter2_col: str | None = None,
    filter2_val: str | None = None,
):
    """Calcule les quatre KPI principaux du dashboard."""
    df = load_excel_data(sheet_name)

    if df.empty:
        return {
            "records": 0,
            "total": 0,
            "distinct_categories": 0,
            "top_category": None,
        }

    df = apply_filters(
        df,
        filter1_col,
        filter1_val,
        filter2_col,
        filter2_val,
    )

    values = get_values(df, value_column)

    distinct_categories = 0
    top_category = None

    if category_column:
        if category_column not in df.columns:
            raise HTTPException(
                status_code=404,
                detail=f"La colonne '{category_column}' n'existe pas."
            )

        work = pd.DataFrame({
            "category": clean_text(df[category_column]),
            "value": values,
        })

        distribution = (
            work.groupby("category")["value"]
            .sum()
            .sort_values(ascending=False)
        )

        distinct_categories = int(distribution.size)

        if not distribution.empty:
            top_category = str(distribution.index[0])

    return {
        "records": int(len(df)),
        "total": json_number(values.sum()),
        "distinct_categories": distinct_categories,
        "top_category": top_category,
    }


@router.get("/dynamic-chart")
def get_dynamic_chart(
    category: str,
    sheet_name: str | None = None,
    value: str | None = None,
    top: int = Query(default=10, ge=1, le=100),
    filter1_col: str | None = None,
    filter1_val: str | None = None,
    filter2_col: str | None = None,
    filter2_val: str | None = None,
):
    """Produit le graphique selon les colonnes choisies."""
    df = load_excel_data(sheet_name)

    if df.empty:
        return {"labels": [], "values": []}

    if category not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"La colonne '{category}' n'existe pas."
        )

    df = apply_filters(
        df,
        filter1_col,
        filter1_val,
        filter2_col,
        filter2_val,
    )

    if not value:
        result = (
            clean_text(df[category])
            .value_counts()
            .head(top)
        )
    else:
        if value not in df.columns:
            raise HTTPException(
                status_code=404,
                detail=f"La colonne '{value}' n'existe pas."
            )

        work = pd.DataFrame({
            "category": clean_text(df[category]),
            "value": pd.to_numeric(
                df[value],
                errors="coerce"
            ).fillna(0),
        })

        result = (
            work.groupby("category")["value"]
            .sum()
            .sort_values(ascending=False)
            .head(top)
        )

    return {
        "labels": [str(label) for label in result.index],
        "values": [json_number(number) for number in result.values],
    }


@router.get("/map-points")
def get_map_points(
    latitude_column: str,
    longitude_column: str,
    sheet_name: str | None = None,
    label_column: str | None = None,
    limit: int = Query(default=5000, ge=1, le=20000),
):
    """Produit les points cartographiques selon les colonnes choisies."""
    df = load_excel_data(sheet_name)

    if df.empty:
        return {"points": [], "count": 0}

    for column in [latitude_column, longitude_column]:
        if column not in df.columns:
            raise HTTPException(
                status_code=404,
                detail=f"La colonne '{column}' n'existe pas."
            )

    work = df.copy()

    work["_latitude"] = pd.to_numeric(
        work[latitude_column]
        .astype(str)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    work["_longitude"] = pd.to_numeric(
        work[longitude_column]
        .astype(str)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    work = (
        work
        .dropna(subset=["_latitude", "_longitude"])
        .head(limit)
    )

    points = []

    for _, row in work.iterrows():
        label = "Point"

        if label_column and label_column in work.columns:
            label = str(row.get(label_column, "Point"))

        points.append({
            "lat": float(row["_latitude"]),
            "lng": float(row["_longitude"]),
            "label": label,
        })

    return {
        "points": points,
        "count": len(points),
    }

@router.get("/auto-analysis")
def get_auto_analysis(sheet_name: str | None = None):
    """
    Analyse automatiquement la feuille sélectionnée
    sans imposer de nom de colonne.
    """
    df = load_excel_data(sheet_name)

    return analyze_dataframe(df)

GEO_REFERENCE_PATH = Path(
    "app/data/referentiel_geographique.xlsx"
)


@router.get("/map-zones")
def map_zones(
    sheet_name: str,
    data_column: str,
):
    """
    Agrège les données par zone puis les relie
    au référentiel géographique importé.
    """

    # -----------------------------------------
    # 1. Charger la feuille principale
    # -----------------------------------------

    df = load_excel_data(sheet_name)

    if df.empty:
        return {
            "points": [],
            "count": 0,
        }

    if data_column not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=(
                f"La colonne '{data_column}' "
                "n'existe pas dans la feuille."
            ),
        )

    # -----------------------------------------
    # 2. Vérifier le référentiel
    # -----------------------------------------

    if not GEO_REFERENCE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Aucun référentiel géographique "
                "n'a été importé."
            ),
        )

    # -----------------------------------------
    # 3. Charger le référentiel
    # -----------------------------------------

    try:
        geo_df = pd.read_excel(
            GEO_REFERENCE_PATH
        )

        geo_df.columns = (
            geo_df.columns
            .astype(str)
            .str.strip()
            .str.lower()
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de lire le référentiel "
                f"géographique : {error}"
            ),
        )

    required_columns = {
        "zone_label",
        "latitude",
        "longitude",
    }

    missing_columns = (
        required_columns
        - set(geo_df.columns)
    )

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "Le référentiel géographique doit "
                "contenir les colonnes : "
                "zone_label, latitude, longitude."
            ),
        )

    # -----------------------------------------
    # 4. Nettoyer les libellés
    # -----------------------------------------

    data_work = df.copy()

    data_work["_zone"] = (
        data_work[data_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    geo_work = geo_df.copy()

    geo_work["_zone"] = (
        geo_work["zone_label"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------
    # 5. Convertir les coordonnées
    # -----------------------------------------

    geo_work["latitude"] = pd.to_numeric(
        geo_work["latitude"],
        errors="coerce",
    )

    geo_work["longitude"] = pd.to_numeric(
        geo_work["longitude"],
        errors="coerce",
    )

    geo_work = geo_work.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    # -----------------------------------------
    # 6. Agréger les données par zone
    # -----------------------------------------

    grouped = (
        data_work[
            data_work["_zone"] != ""
        ]
        .groupby("_zone")
        .size()
        .reset_index(
            name="count"
        )
    )

    # -----------------------------------------
    # 7. Faire la jointure
    # -----------------------------------------

    merged = grouped.merge(
        geo_work[
            [
                "_zone",
                "zone_label",
                "latitude",
                "longitude",
            ]
        ],
        on="_zone",
        how="left",
    )

    # -----------------------------------------
    # 8. Identifier les zones non trouvées
    # -----------------------------------------

    unmatched = (
        merged[
            merged["latitude"].isna()
            | merged["longitude"].isna()
        ]["_zone"]
        .astype(str)
        .tolist()
    )

    # Garder uniquement les zones cartographiables
    mapped = merged.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    # -----------------------------------------
    # 9. Construire la réponse JSON
    # -----------------------------------------

    points = []

    for _, row in mapped.iterrows():
        points.append({
            "label": str(
                row["zone_label"]
            ),
            "lat": float(
                row["latitude"]
            ),
            "lng": float(
                row["longitude"]
            ),
            "count": int(
                row["count"]
            ),
        })

    return {
        "points": points,
        "count": len(points),
        "unmatched_zones": unmatched,
    }