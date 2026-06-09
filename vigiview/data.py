"""FAERS-like sample data for VigiView.

The original Medical-Data-Viewer read three MySQL tables (Product, Person,
Injection), all keyed by a shared case id. There is no public dump to ship, so
this module generates a deterministic synthetic dataset with the same schema and
realistic distributions. ``generate()`` is seeded, so the committed JSON is
reproducible and the tests are stable.
"""

from __future__ import annotations

import random

# --- Coded value maps (mirror the original Django model choices) ----------- #
SEX = {1: "Male", 2: "Female"}
QUALIFICATION = {
    1: "High School",
    2: "Associate Degree",
    3: "Bachelor's Degree",
    4: "Master's Degree",
    5: "Doctorate",
}
YES_NO = {1: "Yes", 2: "No"}
DRUG_RISK = {
    1: "One-Time High-Risk Injection (Emergency)",
    2: "Routine Injections (Multiple)",
    3: "One-Time Injection (Non-Emergency)",
}
INJECTION_TYPE = {
    1: "INJECTION, SOLUTION",
    2: "Capsule",
    3: "Dry Powder",
    4: "Solution for injection in pre-filled pen",
    5: "Solution for injection in pre-filled syringe",
}

# A pool of real-ish drug names; weights create a long tail so some appear once
# (which exercises the original's "group counts <= 1 into Other" behaviour).
DRUG_NAMES = [
    "Adalimumab", "Insulin Glargine", "Metformin", "Atorvastatin", "Etanercept",
    "Rituximab", "Methotrexate", "Pembrolizumab", "Lisinopril", "Omeprazole",
    "Warfarin", "Prednisone", "Ibuprofen", "Amoxicillin", "Levothyroxine",
    "Sumatriptan", "Clopidogrel", "Tramadol", "Sertraline", "Gabapentin",
]
COUNTRIES = ["US", "GB", "DE", "FR", "CA", "JP", "IN", "BR", "ES", "IT", "AU", "MX"]


def generate(n: int = 600, seed: int = 42) -> dict[str, list[dict]]:
    """Return ``{"people": [...], "products": [...], "injections": [...]}``.

    Each list has ``n`` rows sharing case ids 1..n, matching the original's
    one-row-per-case-per-table layout.
    """
    rng = random.Random(seed)
    people, products, injections = [], [], []

    # Skew drug popularity so a handful dominate and a few are one-offs.
    drug_weights = [max(1, int(40 * (0.7**i))) for i in range(len(DRUG_NAMES))]

    for case_id in range(1, n + 1):
        # ---- Person ----
        age = max(0, min(99, int(rng.gauss(52, 18))))
        sex = rng.choice([1, 2])
        people.append(
            {
                "id": case_id,
                "age": age,
                "sex": sex,
                "qualification": rng.choices([1, 2, 3, 4, 5], weights=[20, 15, 30, 20, 15])[0],
                "country": rng.choices(COUNTRIES, weights=[30, 12, 10, 9, 8, 6, 6, 5, 5, 4, 3, 2])[0],
                "death": rng.choices([1, 2], weights=[12, 88])[0],
                "disability": rng.choices([1, 2], weights=[18, 82])[0],
            }
        )
        # ---- Product ----
        products.append(
            {"id": case_id, "product": rng.choices(DRUG_NAMES, weights=drug_weights)[0]}
        )
        # ---- Injection ----
        injections.append(
            {
                "id": case_id,
                "drug": rng.choices([1, 2, 3], weights=[25, 45, 30])[0],
                "injection": rng.choices([1, 2, 3, 4, 5], weights=[35, 15, 10, 20, 20])[0],
            }
        )

    return {"people": people, "products": products, "injections": injections}
