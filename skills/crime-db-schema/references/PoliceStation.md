# PoliceStation

```sql
CREATE TABLE IF NOT EXISTS PoliceStation (
    station_id TEXT PRIMARY KEY,
    station_name TEXT,
    district TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL
);
```

Value guidance:
- `district`: Karnataka district names such as `Bengaluru Urban`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi-Dharwad`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `city`: city names such as `Bengaluru`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi`, `Kalaburagi`, `Shivamogga`, `Tumakuru`