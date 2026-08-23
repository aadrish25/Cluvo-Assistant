# TimelineEvent

```sql
CREATE TABLE IF NOT EXISTS TimelineEvent (
    event_id TEXT PRIMARY KEY,
    incident_id TEXT,
    officer_id TEXT,
    event_time TEXT,
    event_type TEXT,
    description TEXT,
    FOREIGN KEY (incident_id) REFERENCES CrimeIncident(incident_id),
    FOREIGN KEY (officer_id) REFERENCES Officer(officer_id)
);
```

Value guidance:
- `event_type`: `Accused Arrested`, `Evidence Collected`, `FIR Registered`, `Witness Examined`