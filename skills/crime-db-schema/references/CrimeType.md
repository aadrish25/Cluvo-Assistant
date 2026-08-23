# CrimeType

```sql
CREATE TABLE IF NOT EXISTS CrimeType (
    crime_type_id TEXT PRIMARY KEY,
    crime_name TEXT,
    category TEXT,
    default_severity INTEGER
);
```

Value guidance:
- `crime_name`: `Assault`, `Bank Fraud`, `Burglary`, `Chain Snatching`, `Cyber Fraud`, `Drug Trafficking`, `Extortion`, `Kidnapping`, `Robbery`, `Vehicle Theft`
- `category`: `Economic Crime`, `Organized Crime`, `Property Crime`, `Violent Crime`
- `default_severity`: `5`, `6`, `7`, `8`, `9`