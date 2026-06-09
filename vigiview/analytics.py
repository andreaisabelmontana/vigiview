"""VigiView analytics engine.

Pure functions over lists of dicts (no DB, no web), so the same logic powers the
FastAPI service, the tests, and conceptually the browser client. Filtering and
the stat aggregations mirror the original Django views:

* people  — age 9-bin histogram, gender split, qualification breakdown
            (plus death/disability rates and top countries as enrichment)
* products — usage counts, grouping any product seen <= 1 time into "Other"
* injections — counts by risk category and by formulation type
"""

from __future__ import annotations

from collections import Counter

AGE_BINS = [
    ("0-10", 0, 10), ("11-20", 11, 20), ("21-30", 21, 30), ("31-40", 31, 40),
    ("41-50", 41, 50), ("51-60", 51, 60), ("61-70", 61, 70), ("71-80", 71, 80),
    ("81+", 81, 999),
]


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
def filter_people(rows, *, id=None, age_min=None, age_max=None, sex=None,
                  qualification=None, country=None, death=None, disability=None):
    def keep(r):
        if id not in (None, "") and r["id"] != int(id):
            return False
        if age_min not in (None, "") and (r["age"] is None or r["age"] < int(age_min)):
            return False
        if age_max not in (None, "") and (r["age"] is None or r["age"] > int(age_max)):
            return False
        if sex not in (None, "") and r["sex"] != int(sex):
            return False
        if qualification not in (None, "") and r["qualification"] != int(qualification):
            return False
        if country not in (None, "") and country.lower() not in (r["country"] or "").lower():
            return False
        if death not in (None, "") and r["death"] != int(death):
            return False
        if disability not in (None, "") and r["disability"] != int(disability):
            return False
        return True

    return [r for r in rows if keep(r)]


def filter_products(rows, *, id=None, product=None):
    def keep(r):
        if id not in (None, "") and r["id"] != int(id):
            return False
        if product not in (None, "") and product.lower() not in r["product"].lower():
            return False
        return True

    return [r for r in rows if keep(r)]


def filter_injections(rows, *, id=None, drug=None, injection=None):
    def keep(r):
        if id not in (None, "") and r["id"] != int(id):
            return False
        if drug not in (None, "") and r["drug"] != int(drug):
            return False
        if injection not in (None, "") and r["injection"] != int(injection):
            return False
        return True

    return [r for r in rows if keep(r)]


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def person_stats(people: list[dict]) -> dict:
    ages = [p["age"] for p in people if p["age"] is not None]
    age_counts = [sum(lo <= a <= hi for a in ages) for _, lo, hi in AGE_BINS]

    from .data import QUALIFICATION, SEX

    sex_counter = Counter(p["sex"] for p in people if p["sex"])
    qual_counter = Counter(p["qualification"] for p in people if p["qualification"])
    country_counter = Counter(p["country"] for p in people if p["country"])

    n = len(people) or 1
    return {
        "total": len(people),
        "age_labels": [b[0] for b in AGE_BINS],
        "age_counts": age_counts,
        "gender_labels": [SEX[k] for k in sorted(sex_counter)],
        "gender_counts": [sex_counter[k] for k in sorted(sex_counter)],
        "qualification_labels": [QUALIFICATION[k] for k in sorted(qual_counter)],
        "qualification_counts": [qual_counter[k] for k in sorted(qual_counter)],
        "death_rate": round(100 * sum(1 for p in people if p["death"] == 1) / n, 1),
        "disability_rate": round(100 * sum(1 for p in people if p["disability"] == 1) / n, 1),
        "top_countries": country_counter.most_common(8),
    }


def product_stats(products: list[dict]) -> dict:
    usage = Counter(p["product"] for p in products).most_common()
    labels, counts, other = [], [], 0
    for name, count in usage:
        if count > 1:
            labels.append(name)
            counts.append(count)
        else:
            other += count
    if other:
        labels.append("Other")
        counts.append(other)
    return {"total": len(products), "product_labels": labels, "product_counts": counts}


def injection_stats(injections: list[dict]) -> dict:
    from .data import DRUG_RISK, INJECTION_TYPE

    drug_counter = Counter(i["drug"] for i in injections if i["drug"])
    type_counter = Counter(i["injection"] for i in injections if i["injection"])
    drug_order = [k for k, _ in drug_counter.most_common()]
    type_order = [k for k, _ in type_counter.most_common()]
    return {
        "total": len(injections),
        "drug_labels": [DRUG_RISK[k] for k in drug_order],
        "drug_counts": [drug_counter[k] for k in drug_order],
        "injection_labels": [INJECTION_TYPE[k] for k in type_order],
        "injection_counts": [type_counter[k] for k in type_order],
    }


def paginate(rows: list, page: int = 1, page_size: int = 25) -> dict:
    page = max(1, page)
    start = (page - 1) * page_size
    return {
        "rows": rows[start:start + page_size],
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "pages": max(1, (len(rows) + page_size - 1) // page_size),
    }
