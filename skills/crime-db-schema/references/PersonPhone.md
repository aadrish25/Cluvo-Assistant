# PersonPhone

```sql
CREATE TABLE IF NOT EXISTS PersonPhone (
    person_phone_id TEXT PRIMARY KEY,
    person_id TEXT,
    phone_id TEXT,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (phone_id) REFERENCES Phone(phone_id) ON DELETE CASCADE
);
```

Value guidance:
- `end_date` may be NULL for active/current phone links.