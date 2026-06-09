# 🩺 VigiView

Explore and visualise **FAERS-style adverse drug event data** — searchable case
tables plus pharmacovigilance dashboards.

**▶️ Live (runs entirely in your browser):** https://andreaisabelmontana.github.io/vigiview/

Built from scratch. FAERS is the FDA's Adverse Event Reporting System — a large
public database of reported adverse drug events. VigiView makes a slice of that
kind of data explorable: search the case tables, then read the safety signals
off the dashboards. It's structured like a real app — a clean, tested analytics
engine + a thin API, with a static client that doubles as the live site.

## What's inside

| Piece | What it is | Where |
|-------|------------|-------|
| **Client** | A standalone explorer: filterable/paginated case tables (People / Products / Injections) and dashboards (age histogram, gender donut, education, top countries, top drugs, injection risk & formulation). Computes everything in-browser. | `docs/` → GitHub Pages |
| **Engine** | Pure filtering + aggregation functions mirroring the original Django views. | `vigiview/analytics.py` |
| **API** | FastAPI: a filterable/paginated `/api/table` and `/api/stats/{table}`. | `vigiview/app.py` |
| **Data** | A seeded synthetic FAERS-like dataset (no public dump to ship) with the original three-table schema. | `vigiview/data.py`, `scripts/gen_data.py` |

The engine and the browser client implement the **same** aggregations (age 9-bin
histogram, gender/education breakdowns, product usage with singletons grouped as
"Other", injection counts by risk and formulation), so the dashboards match what
the API returns.

> ⚕️ The data is **synthetic** and for demonstration only — not real FAERS records.

## Run the API locally

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate elsewhere)
pip install -r requirements.txt
uvicorn vigiview.app:app --reload
```

- App + client: http://localhost:8000/
- Swagger docs: http://localhost:8000/docs

### Regenerate the sample data

```bash
python scripts/gen_data.py 600     # writes docs/data/faers_sample.json (deterministic)
```

### Docker

```bash
docker build -t vigiview .
docker run -p 8000:8000 vigiview
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Covers data generation (determinism + schema), the filtering and stat
aggregations, pagination, and the API endpoints (via `TestClient`). CI also
checks the committed dataset is reproducible and builds the Docker image.

## Layout

```
vigiview/
  data.py        synthetic FAERS dataset + coded-value maps
  analytics.py   filtering + person/product/injection aggregations (the engine)
  app.py         FastAPI: /api/table, /api/stats/{table}, static mount
docs/            static client + GitHub Pages site (index.html, app.js, charts.js)
  data/          generated faers_sample.json
scripts/gen_data.py   regenerate the dataset
tests/           pytest: data + engine + API
```

## License

MIT — see [LICENSE](LICENSE).
