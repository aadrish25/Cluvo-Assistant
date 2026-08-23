# PersonAddress

```sql
CREATE TABLE IF NOT EXISTS PersonAddress (
    person_address_id TEXT PRIMARY KEY,
    person_id TEXT,
    location_id TEXT,
    address_type TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);
```

Value guidance:
- `address_type`: `Current`, `Permanent`