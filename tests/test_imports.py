import asyncio
import io

from fastapi import HTTPException, UploadFile

import app.api.imports as imports


def make_upload(filename, content=b"test"):
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
    )


def test_import_excel_rejects_non_xlsx(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = imports.import_excel(
        make_upload("data.csv")
    )

    assert "error" in result


def test_import_excel_saves_xlsx(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = imports.import_excel(
        make_upload("data.xlsx", b"abc")
    )

    assert result["message"] == "Fichier importé avec succès"

    saved_file = (
        tmp_path
        / "data"
        / "fichier_importe.xlsx"
    )

    assert saved_file.read_bytes() == b"abc"


def test_geo_reference_rejects_non_xlsx():
    try:
        asyncio.run(
            imports.import_geographic_reference(
                make_upload("geo.csv")
            )
        )
        assert False, "Une HTTPException était attendue"

    except HTTPException as exc:
        assert exc.status_code == 400
