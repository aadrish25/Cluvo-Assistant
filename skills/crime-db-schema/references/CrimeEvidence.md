# CrimeEvidence

```sql
CREATE TABLE IF NOT EXISTS CrimeEvidence (
    crime_evidence_id TEXT PRIMARY KEY,
    incident_id TEXT,
    evidence_id TEXT,
    FOREIGN KEY (incident_id) REFERENCES CrimeIncident(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id) ON DELETE CASCADE
);
```

Value guidance:
- No categorical columns. Use this bridge table to connect incidents to evidence items.