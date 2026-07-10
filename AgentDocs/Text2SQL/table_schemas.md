# Text2SQL Table Schemas

Use this file as the exact schema source for selected tables. Retrieve schemas by table heading name.

Retrieval rule:
- Each table starts with `## TableName`.
- The schema for that table ends before the next `## TableName`.
- Use heading `## Case` for lookup, but generate SQL using quoted table name `"Case"`.
- `Value guidance` lists seeded/expected values for categorical columns. Prefer these exact values in WHERE filters.
- If a column is not listed under `Value guidance`, treat it as free-form text, identifier, date/time, or numeric data and inspect/query as needed.

## Case

```sql
CREATE TABLE IF NOT EXISTS "Case" (
    case_id TEXT PRIMARY KEY,
    case_number TEXT UNIQUE,
    title TEXT,
    description TEXT,
    priority TEXT,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Value guidance:
- `priority`: `Critical`, `High`, `Low`, `Medium`
- `status`: `Chargesheet Filed`, `Closed`, `Open`, `Under Investigation`

## PoliceStation

```sql
CREATE TABLE IF NOT EXISTS PoliceStation (
    station_id TEXT PRIMARY KEY,
    station_name TEXT,
    district TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL
);
```

Value guidance:
- `district`: Karnataka district names such as `Bengaluru Urban`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi-Dharwad`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `city`: city names such as `Bengaluru`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi`, `Kalaburagi`, `Shivamogga`, `Tumakuru`

## Location

```sql
CREATE TABLE IF NOT EXISTS Location (
    location_id TEXT PRIMARY KEY,
    location_name TEXT,
    address TEXT,
    district TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    latitude REAL,
    longitude REAL
);
```

Value guidance:
- `district`: `Bengaluru Urban`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi-Dharwad`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `city`: `Bengaluru`, `Mysuru`, `Belagavi`, `Mangaluru`, `Hubballi`, `Kalaburagi`, `Shivamogga`, `Tumakuru`
- `state`: `Karnataka`

## CrimeType

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

## ModusOperandi

```sql
CREATE TABLE IF NOT EXISTS ModusOperandi (
    mo_id TEXT PRIMARY KEY,
    mo_name TEXT,
    description TEXT
);
```

Value guidance:
- `mo_name`: `Distract-and-snatch`, `Forced entry`, `Gang attack`, `Phishing call`, `Vehicle lift-and-strip`

## Person

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

## Officer

```sql
CREATE TABLE IF NOT EXISTS Officer (
    officer_id TEXT PRIMARY KEY,
    name TEXT,
    badge_number TEXT UNIQUE,
    rank TEXT,
    station_id TEXT,
    years_of_service INTEGER,
    specialization TEXT,
    FOREIGN KEY (station_id) REFERENCES PoliceStation(station_id)
);
```

Value guidance:
- `rank`: `Assistant Commissioner`, `Deputy Superintendent`, `Inspector`, `Sub Inspector`
- `specialization`: `Cyber Crime`, `Financial Crime`, `Organized Crime`, `Property Crime`

## Evidence

```sql
CREATE TABLE IF NOT EXISTS Evidence (
    evidence_id TEXT PRIMARY KEY,
    evidence_type TEXT,
    description TEXT,
    collection_date TEXT,
    forensic_status TEXT,
    storage_location TEXT,
    chain_of_custody TEXT
);
```

Value guidance:
- `evidence_type`: `Bank Record`, `CCTV Footage`, `Document`, `Mobile Phone`, `Vehicle`, `Witness Statement`
- `forensic_status`: `Analyzed`, `Not Required`, `Pending`, `Submitted`

## Vehicle

```sql
CREATE TABLE IF NOT EXISTS Vehicle (
    vehicle_id TEXT PRIMARY KEY,
    registration_number TEXT UNIQUE,
    vehicle_type TEXT,
    manufacturer TEXT,
    model TEXT,
    color TEXT,
    manufacture_year INTEGER
);
```

Value guidance:
- `vehicle_type`: `Auto Rickshaw`, `Car`, `Motorcycle`, `Scooter`, `Van`
- `manufacturer`: `Bajaj`, `Hero`, `Honda`, `Hyundai`, `Maruti`, `TVS`
- `model`: `Activa`, `Apache`, `Pulsar`, `Splendor`, `Swift`, `i20`
- `color`: `Black`, `Blue`, `Red`, `Silver`, `White`

## Phone

```sql
CREATE TABLE IF NOT EXISTS Phone (
    phone_id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    imei TEXT UNIQUE,
    network_provider TEXT
);
```

Value guidance:
- `network_provider`: `Airtel`, `BSNL`, `Jio`, `Vi`

## BankAccount

```sql
CREATE TABLE IF NOT EXISTS BankAccount (
    account_id TEXT PRIMARY KEY,
    bank_name TEXT,
    account_number TEXT UNIQUE,
    ifsc TEXT,
    account_type TEXT
);
```

Value guidance:
- `bank_name`: `Canara Bank`, `HDFC Bank`, `ICICI Bank`, `Karnataka Bank`, `SBI`
- `account_type`: `Current`, `Savings`

## Organization

```sql
CREATE TABLE IF NOT EXISTS Organization (
    organization_id TEXT PRIMARY KEY,
    organization_name TEXT,
    organization_type TEXT,
    description TEXT
);
```

Value guidance:
- `organization_name`: `Bengaluru North Gang`, `Mysuru Fraud Ring`
- `organization_type`: `Criminal Gang`, `Financial Crime Network`

## FIR

```sql
CREATE TABLE IF NOT EXISTS FIR (
    fir_id TEXT PRIMARY KEY,
    case_id TEXT,
    fir_number TEXT UNIQUE,
    police_station_id TEXT,
    filing_date TEXT,
    complainant_name TEXT,
    description TEXT,
    status TEXT,
    FOREIGN KEY (case_id) REFERENCES "Case"(case_id),
    FOREIGN KEY (police_station_id) REFERENCES PoliceStation(station_id)
);
```

Value guidance:
- `status`: `Chargesheet Filed`, `Closed`, `Registered`, `Under Investigation`

## CrimeIncident

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

## Investigation

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

## FinancialTransaction

```sql
CREATE TABLE IF NOT EXISTS FinancialTransaction (
    transaction_id TEXT PRIMARY KEY,
    from_account_id TEXT,
    to_account_id TEXT,
    amount REAL,
    transaction_date TEXT,
    transaction_type TEXT,
    remarks TEXT,
    FOREIGN KEY (from_account_id) REFERENCES BankAccount(account_id),
    FOREIGN KEY (to_account_id) REFERENCES BankAccount(account_id)
);
```

Value guidance:
- `transaction_type`: `Cash Deposit`, `IMPS`, `NEFT`, `UPI`
- `remarks`: commonly `goods`, `loan repayment`, `advance`, `personal transfer`

## TimelineEvent

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

## Conversation

```sql
CREATE TABLE IF NOT EXISTS Conversation (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Value guidance:
- No fixed categorical filters are expected. Use `user_id` only when the user asks about chat history.

## Message

```sql
CREATE TABLE IF NOT EXISTS Message (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    sender TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES Conversation(conversation_id) ON DELETE CASCADE
);
```

Value guidance:
- `sender`: `assistant`, `user`

## CrimeParticipant

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

## PersonAddress

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

## PersonVehicle

```sql
CREATE TABLE IF NOT EXISTS PersonVehicle (
    person_vehicle_id TEXT PRIMARY KEY,
    person_id TEXT,
    vehicle_id TEXT,
    ownership_type TEXT,
    registered_from TEXT,
    registered_to TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);
```

Value guidance:
- `ownership_type`: `Borrowed`, `Owner`, `Rider`, `Suspected Use`

## PersonPhone

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

## PersonBankAccount

```sql
CREATE TABLE IF NOT EXISTS PersonBankAccount (
    person_bank_id TEXT PRIMARY KEY,
    person_id TEXT,
    account_id TEXT,
    relation_type TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES BankAccount(account_id) ON DELETE CASCADE
);
```

Value guidance:
- `relation_type`: `Joint Holder`, `Primary Holder`, `Suspected Beneficiary`

## PersonOrganization

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

## CrimeEvidence

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
