# Investigation

```sql
CREATE TABLE IF NOT EXISTS Investigation (
    investigation_id TEXT PRIMARY KEY,
    incident_id TEXT,
    officer_id TEXT,
    status TEXT,
    priority TEXT,
    assigned_date TEXT,
    closed_date TEXT,
    next_action TEXT,
    remarks TEXT,
    FOREIGN KEY (incident_id) REFERENCES CrimeIncident(incident_id),
    FOREIGN KEY (officer_id) REFERENCES Officer(officer_id)
);
```

Value guidance:
- `status`: `Chargesheet Filed`, `Closed`, `Evidence Review`, `Field Inquiry`, `Open`
- `priority`: `High`, `Low`, `Medium`