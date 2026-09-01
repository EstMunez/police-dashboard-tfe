import pandas as pd
import pytest
from fastapi import HTTPException

import app.api.dashboard as dashboard


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Quartier": ["A", "A", "B"],
            "Nombre": [2, 3, 4],
            "Latitude": ["50,1", "50.2", None],
            "Longitude": ["4,1", "4.2", "4.3"],
        }
    )


def test_apply_filters(sample_df):
    result = dashboard.apply_filters(
        sample_df,
        "Quartier",
        "A",
    )

    assert len(result) == 2


def test_apply_filters_unknown_column(sample_df):
    with pytest.raises(HTTPException) as exc:
        dashboard.apply_filters(
            sample_df,
            "Inconnue",
            "A",
        )

    assert exc.value.status_code == 400


def test_get_values_defaults_to_one(sample_df):
    values = dashboard.get_values(
        sample_df,
        None,
    )

    assert values.sum() == 3


def test_get_values_numeric(sample_df):
    values = dashboard.get_values(
        sample_df,
        "Nombre",
    )

    assert values.sum() == 9


def test_dynamic_chart_count(monkeypatch, sample_df):
    monkeypatch.setattr(
        dashboard,
        "load_excel_data",
        lambda sheet_name=None: sample_df,
    )

    result = dashboard.get_dynamic_chart(
        category="Quartier",
        top=10,
    )

    assert result["labels"][0] == "A"
    assert result["values"][0] == 2


def test_kpis(monkeypatch, sample_df):
    monkeypatch.setattr(
        dashboard,
        "load_excel_data",
        lambda sheet_name=None: sample_df,
    )

    result = dashboard.get_kpis(
        category_column="Quartier",
        value_column="Nombre",
    )

    assert result == {
        "records": 3,
        "total": 9,
        "distinct_categories": 2,
        "top_category": "A",
    }


def test_map_points(monkeypatch, sample_df):
    monkeypatch.setattr(
        dashboard,
        "load_excel_data",
        lambda sheet_name=None: sample_df,
    )

    result = dashboard.get_map_points(
        latitude_column="Latitude",
        longitude_column="Longitude",
        label_column="Quartier",
        limit=5000,
    )

    assert result["count"] == 2
    assert result["points"][0]["lat"] == 50.1