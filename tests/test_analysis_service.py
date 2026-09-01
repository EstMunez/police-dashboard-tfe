import pandas as pd

from app.services.analysis_service import (
    analyze_dataframe,
    build_analysis_interpretation,
    calculate_analysis_score,
    detect_column_role,
    detect_column_type,
    profile_columns,
    select_numeric_column,
)


def test_detect_column_type_numeric():
    series = pd.Series(["1", "2,5", "3"])
    assert detect_column_type(series) == "numeric"


def test_detect_column_type_date():
    series = pd.Series(["01/01/2025", "02/01/2025", "03/01/2025"])
    assert detect_column_type(series) == "date"


def test_detect_column_type_categorical():
    series = pd.Series(["A", "A", "B", "B", "A", "B"])
    assert detect_column_type(series) == "categorical"


def test_detect_geographic_roles():
    assert detect_column_role("Latitude", "numeric", 10, 10) == "latitude"
    assert detect_column_role("Longitude", "numeric", 10, 10) == "longitude"


def test_detect_location_role():
    assert detect_column_role("Quartier", "categorical", 3, 10) == "location"


def test_detect_identifier_role():
    assert detect_column_role("ID", "numeric", 10, 10) == "identifier"


def test_detect_measure_role():
    assert detect_column_role("Nombre de faits", "numeric", 5, 20) == "measure"


def test_category_score_is_positive():
    assert calculate_analysis_score("category", 4, 100, 0) > 0


def test_latitude_score_is_negative():
    assert calculate_analysis_score("latitude", 100, 100, 0) < 0


def test_select_numeric_column_excludes_coordinates_and_year():
    df = pd.DataFrame(
        {
            "Latitude": [50.1, 50.2, 50.3],
            "Longitude": [4.1, 4.2, 4.3],
            "Année": [2024, 2025, 2026],
            "Nombre de faits": [2, 3, 4],
        }
    )

    profile = profile_columns(df)

    assert select_numeric_column(profile) == "Nombre de faits"


def test_interpretation_uses_full_total():
    result = build_analysis_interpretation(
        column="Quartier",
        labels=["A", "B"],
        values=[40, 20],
        calculation="count",
        full_total=100,
    )

    assert result["top_percentage"] == 40.0


def test_analyze_dataframe_empty():
    result = analyze_dataframe(pd.DataFrame())

    assert result["has_data"] is False


def test_analyze_dataframe_returns_kpis():
    df = pd.DataFrame(
        {
            "Quartier": ["A", "A", "B", "B", "C", "C"],
            "Nombre de faits": [1, 2, 3, 4, 5, 6],
        }
    )

    result = analyze_dataframe(df)

    assert result["has_data"] is True
    assert result["kpis"]["records"] == 6
    assert result["kpis"]["total"] == 21
    assert "profile" in result
    assert "automatic_analyses" in result
