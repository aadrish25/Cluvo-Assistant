# Location

```sql
CREATE TABLE IF NOT EXISTS Location (
    location_id TEXT PRIMARY KEY,
    location_name TEXT,
    address TEXT,
    district TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    latitude REAL,
    longitude REAL
);
```

Value guidance:
- `district`: `Bengaluru Urban`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi-Dharwad`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `city`: `Bengaluru`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `state`: `Karnataka`