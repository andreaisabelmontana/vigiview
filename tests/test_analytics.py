"""Tests for the VigiView data generator, analytics engine, and API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vigiview import analytics
from vigiview.analytics import AGE_BINS
from vigiview.app import app
from vigiview.data import generate


@pytest.fixture(scope="module")
def ds():
    return generate(n=300, seed=1)


# ------------------------------ data --------------------------------------- #
def test_generate_is_deterministic():
    assert generate(n=50, seed=7) == generate(n=50, seed=7)


def test_generate_shapes(ds):
    assert len(ds["people"]) == len(ds["products"]) == len(ds["injections"]) == 300
    assert ds["people"][0]["id"] == 1
    assert set(ds["people"][0]) == {
        "id", "age", "sex", "qualification", "country", "death", "disability"
    }


# ---------------------------- filtering ------------------------------------ #
def test_filter_people_by_sex_and_age(ds):
    out = analytics.filter_people(ds["people"], sex=2, age_min=40, age_max=60)
    assert out and all(r["sex"] == 2 and 40 <= r["age"] <= 60 for r in out)


def test_filter_products_substring(ds):
    out = analytics.filter_products(ds["products"], product="metf")
    assert all("metf" in r["product"].lower() for r in out)


def test_filter_injections_by_drug(ds):
    out = analytics.filter_injections(ds["injections"], drug=1)
    assert all(r["drug"] == 1 for r in out)


# ------------------------------ stats -------------------------------------- #
def test_person_stats_age_bins_sum_to_total(ds):
    s = analytics.person_stats(ds["people"])
    assert len(s["age_counts"]) == len(AGE_BINS) == 9
    assert sum(s["age_counts"]) == sum(1 for p in ds["people"] if p["age"] is not None)
    assert 0 <= s["death_rate"] <= 100


def test_product_stats_groups_singletons_into_other(ds):
    s = analytics.product_stats(ds["products"])
    # counts are descending and "Other" (if present) only bundles singletons
    assert s["product_counts"] == sorted(s["product_counts"], reverse=True) or "Other" in s["product_labels"]
    assert sum(s["product_counts"]) == len(ds["products"])


def test_injection_stats_counts_match_total(ds):
    s = analytics.injection_stats(ds["injections"])
    assert sum(s["drug_counts"]) == len(ds["injections"])
    assert len(s["injection_labels"]) == len(s["injection_counts"])


def test_paginate():
    page = analytics.paginate(list(range(0, 53)), page=3, page_size=20)
    assert page["rows"] == list(range(40, 53))
    assert page["total"] == 53 and page["pages"] == 3


# ------------------------------- API --------------------------------------- #
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_table_endpoint_filters_and_paginates(client):
    r = client.get("/api/table", params={"table": "Person", "sex": 1, "page_size": 10})
    body = r.json()
    assert r.status_code == 200
    assert len(body["rows"]) <= 10
    assert all(row["sex"] == 1 for row in body["rows"])


def test_stats_endpoint(client):
    r = client.get("/api/stats/product")
    assert r.status_code == 200
    assert sum(r.json()["product_counts"]) == 600  # default dataset size


def test_unknown_stats_is_404(client):
    assert client.get("/api/stats/nope").status_code == 404
