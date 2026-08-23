# CrimeIncident

```sql
CREATE TABLE IF NOT EXISTS CrimeIncident (
    incident_id TEXT PRIMARY KEY,
    fir_id TEXT,
    crime_type_id TEXT,
    mo_id TEXT,
    location_id TEXT,
    crime_datetime TEXT,
    weapon_used TEXT,
    severity INTEGER,
    status TEXT,
    description TEXT,
    FOREIGN KEY (fir_id) REFERENCES FIR(fir_id),
    FOREIGN KEY (crime_type_id) REFERENCES CrimeType(crime_type_id),
    FOREIGN KEY (mo_id) REFERENCES ModusOperandi(mo_id),
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);
```

Value guidance:
- `weapon_used`: `Blunt object`, `Knife`, `None`, `Unknown`
- `severity`: `4`, `5`, `6`, `7`, `8`, `9`, `10`
- `status`: `Accused Arrested`, `Closed`, `Reported`, `Under Investigation`