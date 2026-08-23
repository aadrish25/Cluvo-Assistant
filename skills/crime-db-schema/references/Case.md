# Case

> **Note:** Table heading is `Case`, but this is a reserved SQL keyword — always quote it in SQL as `"Case"`.

```sql
CREATE TABLE IF NOT EXISTS "Case" (
    case_id TEXT PRIMARY KEY,
    case_number TEXT UNIQUE,
    title TEXT,
    description TEXT,
    priority TEXT,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Value guidance:
- `priority`: `Critical`, `High`, `Low`, `Medium`
- `status`: `Chargesheet Filed`, `Closed`, `Open`, `Under Investigation`