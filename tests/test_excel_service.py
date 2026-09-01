import pandas as pd

import app.services.excel_service as excel_service


def test_get_sheet_names_when_file_does_not_exist(monkeypatch, tmp_path):
    monkeypatch.setattr(
        excel_service,
        "FILE_PATH",
        str(tmp_path / "missing.xlsx"),
    )

    assert excel_service.get_sheet_names() == []


def test_find_header_row(tmp_path):
    path = tmp_path / "headers.xlsx"

    rows = [
        ["Rapport", None, None],
        [None, None, None],
        ["Année", "Nature du fait", "Rue"],
        [2025, "Vol", "Rue A"],
    ]

    pd.DataFrame(rows).to_excel(
        path,
        index=False,
        header=False,
    )

    assert excel_service.find_header_row(
        str(path),
        "Sheet1",
    ) == 2


def test_load_excel_data_adds_compatibility_columns(monkeypatch, tmp_path):
    path = tmp_path / "data.xlsx"

    pd.DataFrame(
        {
            "Date": ["01/01/2025", "02/01/2025"],
            "Fait": ["Tapage", "Vol"],
            "Quartier": ["A", "B"],
        }
    ).to_excel(path, index=False)

    monkeypatch.setattr(
        excel_service,
        "FILE_PATH",
        str(path),
    )

    df = excel_service.load_excel_data("Sheet1")

    assert "Nombre de faits" in df.columns
    assert df["Nombre de faits"].tolist() == [1, 1]

    assert "Nature du fait" in df.columns
    assert df["Nature du fait"].tolist() == ["Tapage", "Vol"]

    assert "Année" in df.columns
    assert df["Année"].tolist() == [2025, 2025]

    assert (df["Feuille sélectionnée"] == "Sheet1").all()


def test_invalid_sheet_falls_back_to_first(monkeypatch, tmp_path):
    path = tmp_path / "multi.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Fait": ["A"]}).to_excel(
            writer,
            sheet_name="Premiere",
            index=False,
        )
        pd.DataFrame({"Fait": ["B"]}).to_excel(
            writer,
            sheet_name="Deuxieme",
            index=False,
        )

    monkeypatch.setattr(
        excel_service,
        "FILE_PATH",
        str(path),
    )

    df = excel_service.load_excel_data("Inconnue")

    assert (df["Feuille sélectionnée"] == "Premiere").all()
