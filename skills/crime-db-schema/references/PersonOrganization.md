# PersonOrganization

```sql
CREATE TABLE IF NOT EXISTS PersonOrganization (
    person_org_id TEXT PRIMARY KEY,
    person_id TEXT,
    organization_id TEXT,
    role TEXT,
    joined_date TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES Organization(organization_id) ON DELETE CASCADE
);
```

Value guidance:
- `role`: `Leader`, `Member`