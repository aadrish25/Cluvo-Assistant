# FIR

```sql
CREATE TABLE IF NOT EXISTS FIR (
    fir_id TEXT PRIMARY KEY,
    case_id TEXT,
    fir_number TEXT UNIQUE,
    police_station_id TEXT,
    filing_date TEXT,
    complainant_name TEXT,
    description TEXT,
    status TEXT,
    FOREIGN KEY (case_id) REFERENCES "Case"(case_id),
    FOREIGN KEY (police_station_id) REFERENCES PoliceStation(station_id)
);
```

Value guidance:
- `status`: `Chargesheet Filed`, `Closed`, `Registered`, `Under Investigation`