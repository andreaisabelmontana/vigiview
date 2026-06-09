"""VigiView FastAPI service.

A compact mirror of the original Django backend: a filterable/paginated table
endpoint over the three case tables, plus a stats endpoint per table. The data
is the in-memory synthetic dataset; the static client (``docs/``) computes the
same things in-browser, so the API isn't required to use the app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import analytics
from .data import generate

DATASET = generate()

app = FastAPI(title="VigiView API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/table")
def table(
    table: str = Query("Product", pattern="^(Product|Person|Injection)$"),
    page: int = 1,
    page_size: int = Query(25, ge=1, le=200),
    id: Optional[str] = None,
    # person filters
    age_min: Optional[str] = None, age_max: Optional[str] = None,
    sex: Optional[str] = None, qualification: Optional[str] = None,
    country: Optional[str] = None, death: Optional[str] = None,
    disability: Optional[str] = None,
    # product filter
    product: Optional[str] = None,
    # injection filters
    drug: Optional[str] = None, injection: Optional[str] = None,
) -> dict:
    if table == "Product":
        rows = analytics.filter_products(DATASET["products"], id=id, product=product)
    elif table == "Person":
        rows = analytics.filter_people(
            DATASET["people"], id=id, age_min=age_min, age_max=age_max, sex=sex,
            qualification=qualification, country=country, death=death,
            disability=disability,
        )
    else:
        rows = analytics.filter_injections(
            DATASET["injections"], id=id, drug=drug, injection=injection
        )
    return analytics.paginate(rows, page=page, page_size=page_size)


@app.get("/api/stats/{table}")
def stats(table: str) -> dict:
    if table == "person":
        return analytics.person_stats(DATASET["people"])
    if table == "product":
        return analytics.product_stats(DATASET["products"])
    if table == "injection":
        return analytics.injection_stats(DATASET["injections"])
    raise HTTPException(status_code=404, detail="unknown table")


# Serve the static client (also the GitHub Pages folder) at /.
_WEB = Path(__file__).resolve().parent.parent / "docs"
if _WEB.is_dir():
    app.mount("/", StaticFiles(directory=str(_WEB), html=True), name="web")
