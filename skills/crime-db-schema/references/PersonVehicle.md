# PersonVehicle

```sql
CREATE TABLE IF NOT EXISTS PersonVehicle (
    person_vehicle_id TEXT PRIMARY KEY,
    person_id TEXT,
    vehicle_id TEXT,
    ownership_type TEXT,
    registered_from TEXT,
    registered_to TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);
```

Value guidance:
- `ownership_type`: `Borrowed`, `Owner`, `Rider`, `Suspected Use`