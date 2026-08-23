# Person

```sql
CREATE TABLE IF NOT EXISTS Person (
    person_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    date_of_birth TEXT,
    occupation TEXT,
    education_level TEXT,
    income_group TEXT,
    nationality TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Value guidance:
- `gender`: `Female`, `Male`
- `occupation`: `Daily wage`, `Driver`, `Shop owner`, `Student`, `Technician`, `Unemployed`
- `education_level`: `Graduate`, `PUC`, `Primary`, `Secondary`, `Unknown`
- `income_group`: `Low`, `Lower Middle`, `Middle`, `Upper Middle`
- `nationality`: `Indian`