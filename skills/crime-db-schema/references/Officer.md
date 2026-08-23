# Officer

```sql
CREATE TABLE IF NOT EXISTS Officer (
    officer_id TEXT PRIMARY KEY,
    name TEXT,
    badge_number TEXT UNIQUE,
    rank TEXT,
    station_id TEXT,
    years_of_service INTEGER,
    specialization TEXT,
    FOREIGN KEY (station_id) REFERENCES PoliceStation(station_id)
);
```

Value guidance:
- `rank`: `Assistant Commissioner`, `Deputy Superintendent`, `Inspector`, `Sub Inspector`
- `specialization`: `Cyber Crime`, `Financial Crime`, `Organized Crime`, `Property Crime`