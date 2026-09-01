import shutil
import os
from fastapi import APIRouter, File, HTTPException, UploadFile
from pathlib import Path


router = APIRouter()


@router.post("/excel")
def import_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        return {"error": "Veuillez importer un fichier Excel au format .xlsx"}

    os.makedirs("data", exist_ok=True)

    file_path = "data/fichier_importe.xlsx"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Fichier importé avec succès",
        "filename": file.filename
    }

DATA_DIR = Path("app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

GEO_REFERENCE_PATH = DATA_DIR / "referentiel_geographique.xlsx"


@router.post("/geographic-reference")
async def import_geographic_reference(
    file: UploadFile = File(...)
):
    """
    Importe le fichier Excel servant de référentiel géographique.
    """

    filename = file.filename or ""

    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Le référentiel doit être un fichier .xlsx."
        )

    try:
        content = await file.read()

        with open(GEO_REFERENCE_PATH, "wb") as destination:
            destination.write(content)

        return {
            "success": True,
            "message": "Référentiel géographique importé avec succès.",
            "filename": filename,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible d'importer le référentiel : {error}"
        )