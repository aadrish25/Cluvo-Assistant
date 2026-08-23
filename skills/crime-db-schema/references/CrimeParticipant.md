# CrimeParticipant

```sql
CREATE TABLE IF NOT EXISTS CrimeParticipant (
    participant_id TEXT PRIMARY KEY,
    incident_id TEXT,
    person_id TEXT,
    role TEXT,
    injury_status TEXT,
    arrest_status TEXT,
    remarks TEXT,
    FOREIGN KEY (incident_id) REFERENCES CrimeIncident(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE
);
```

Value guidance:
- `role`: `Accused`, `Victim`, `Witness`
- `injury_status`: `Minor`, `None`, `Serious`
- `arrest_status`: `Arrested`, `Not Arrested`, `Released on Bail`
- Do not filter `role = 'Complainant'`; the seeded data does not use that role.