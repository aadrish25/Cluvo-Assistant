# Vehicle

```sql
CREATE TABLE IF NOT EXISTS Vehicle (
    vehicle_id TEXT PRIMARY KEY,
    registration_number TEXT UNIQUE,
    vehicle_type TEXT,
    manufacturer TEXT,
    model TEXT,
    color TEXT,
    manufacture_year INTEGER
);
```

Value guidance:
- `vehicle_type`: `Auto Rickshaw`, `Car`, `Motorcycle`, `Scooter`, `Van`
- `manufacturer`: `Bajaj`, `Hero`, `Honda`, `Hyundai`, `Maruti`, `TVS`
- `model`: `Activa`, `Apache`, `Pulsar`, `Splendor`, `Swift`, `i20`
- `color`: `Black`, `Blue`, `Red`, `Silver`, `White`