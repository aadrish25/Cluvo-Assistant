# Organization

```sql
CREATE TABLE IF NOT EXISTS Organization (
    organization_id TEXT PRIMARY KEY,
    organization_name TEXT,
    organization_type TEXT,
    description TEXT
);
```

Value guidance:
- `organization_name`: `Bengaluru North Gang`, `Mysuru Fraud Ring`
- `organization_type`: `Criminal Gang`, `Financial Crime Network`