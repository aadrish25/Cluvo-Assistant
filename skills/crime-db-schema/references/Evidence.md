# Evidence

```sql
CREATE TABLE IF NOT EXISTS Evidence (
    evidence_id TEXT PRIMARY KEY,
    evidence_type TEXT,
    description TEXT,
    collection_date TEXT,
    forensic_status TEXT,
    storage_location TEXT,
    chain_of_custody TEXT
);
```

Value guidance:
- `evidence_type`: `Bank Record`, `CCTV Footage`, `Document`, `Mobile Phone`, `Vehicle`, `Witness Statement`
- `forensic_status`: `Analyzed`, `Not Required`, `Pending`, `Submitted`