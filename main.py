from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.api.imports import router as imports_router

from app.api.dashboard import router as dashboard_router

app = FastAPI(title="Police Dashboard API")

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

app.include_router(imports_router, prefix="/import", tags=["Import"])

@app.get("/")
def home():
    return {"message": "API Police opérationnelle OK"}


@app.get("/dashboard-page")
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={}
    )

@app.get("/conditions-utilisation")
def conditions_utilisation(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="conditions_utilisation.html",
        context={}
    )


@app.get("/mentions-legales")
def mentions_legales(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="mentions_legales.html",
        context={}
    )