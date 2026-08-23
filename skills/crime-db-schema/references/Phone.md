# Phone

```sql
CREATE TABLE IF NOT EXISTS Phone (
    phone_id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    imei TEXT UNIQUE,
    network_provider TEXT
);
```

Value guidance:
- `network_provider`: `Airtel`, `BSNL`, `Jio`, `Vi`