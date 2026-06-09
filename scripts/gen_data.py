"""Generate the committed sample dataset used by the client and tests.

    python scripts/gen_data.py [n]

Writes docs/data/faers_sample.json (the browser client loads this directly).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a plain script without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vigiview.data import (  # noqa: E402
    DRUG_RISK, INJECTION_TYPE, QUALIFICATION, SEX, YES_NO, generate,
)

n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
dataset = generate(n=n)
dataset["meta"] = {
    "n": n,
    "maps": {
        "sex": SEX,
        "qualification": QUALIFICATION,
        "yes_no": YES_NO,
        "drug_risk": DRUG_RISK,
        "injection_type": INJECTION_TYPE,
    },
}

out = Path(__file__).resolve().parent.parent / "docs" / "data" / "faers_sample.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dataset), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB, n={n})")
