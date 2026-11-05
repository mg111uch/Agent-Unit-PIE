# Twin series (TWN-01)

One file per city: `<city>.json`, consumed by `scripts/twin_coverage.py`.

```json
{"city_id": "city_kanpur",
 "series": [
   {"field": "population", "value": 2767031, "source": "census_2011",
    "year": 2011, "license": "public-domain",
    "truth": "THIRD_PARTY_VERIFIED",
    "url": "https://censusindia.gov.in/...",
    "note": "what exactly this number counts"}
 ]}
```

Rules enforced by `modules/digital_twins/city_series.py`:

- `field` must be one of `city_state.FIELDS` (10 series).
- `value` numeric, `year` plausible, `source` non-empty, `license` non-empty.
- Rows older than 12 years are accepted but marked `stale` (confidence 0.6).
- A rejected row is reported, never averaged in.
- `truth` and `url` are kept with the value; a press report is
  `THIRD_PARTY_VERIFIED`, not `OBSERVED`.
- Remaining gaps and candidate sources live in `manifest.json`.

Only real, cited series belong here. Do not put an estimate in this directory:
use the adapter placeholders instead, and let the coverage report show the gap.
