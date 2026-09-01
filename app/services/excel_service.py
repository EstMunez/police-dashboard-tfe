import os
import pandas as pd

FILE_PATH = "data/fichier_importe.xlsx"


def get_sheet_names():
    if not os.path.exists(FILE_PATH):
        return []

    excel_file = pd.ExcelFile(FILE_PATH, engine="openpyxl")
    return excel_file.sheet_names


def find_header_row(file_path, sheet_name):
    preview = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl"
    )

    keywords = [
        "Année",
        "Nature du fait",
        "Rue",
        "Latitude",
        "Longitude",
        "Nombre de faits",
        "Date",
        "Fait"
    ]

    for index, row in preview.iterrows():
        values = row.astype(str).str.strip().tolist()
        score = sum(1 for keyword in keywords if keyword in values)

        if score >= 2:
            return index

    return 0


def load_excel_data(sheet_name=None):
    if not os.path.exists(FILE_PATH):
        return pd.DataFrame()

    sheets = get_sheet_names()

    if not sheets:
        return pd.DataFrame()

    if sheet_name is None or sheet_name not in sheets:
        sheet_name = sheets[0]

    header_row = find_header_row(FILE_PATH, sheet_name)

    df = pd.read_excel(
        FILE_PATH,
        sheet_name=sheet_name,
        header=header_row,
        engine="openpyxl"
    )

    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    if "Nombre de faits" in df.columns:
        df["Nombre de faits"] = pd.to_numeric(df["Nombre de faits"], errors="coerce").fillna(0)
    else:
        df["Nombre de faits"] = 1

    if "Nature du fait" in df.columns:
        df["Nature du fait"] = df["Nature du fait"].fillna("Non renseigné")
    elif "Fait" in df.columns:
        df["Nature du fait"] = df["Fait"].fillna("Non renseigné")
    else:
        df["Nature du fait"] = "Non renseigné"

    if "Année" not in df.columns and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["Année"] = df["Date"].dt.year

    df["Feuille sélectionnée"] = sheet_name

    return df