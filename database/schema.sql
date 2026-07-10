PRAGMA foreign_keys = ON;

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

CREATE TABLE IF NOT EXISTS PoliceStation (
    station_id TEXT PRIMARY KEY,
    station_name TEXT,
    district TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL
);

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

CREATE TABLE IF NOT EXISTS CrimeType (
    crime_type_id TEXT PRIMARY KEY,
    crime_name TEXT,
    category TEXT,
    default_severity INTEGER
);

CREATE TABLE IF NOT EXISTS ModusOperandi (
    mo_id TEXT PRIMARY KEY,
    mo_name TEXT,
    description TEXT
);

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

CREATE TABLE IF NOT EXISTS Evidence (
    evidence_id TEXT PRIMARY KEY,
    evidence_type TEXT,
    description TEXT,
    collection_date TEXT,
    forensic_status TEXT,
    storage_location TEXT,
    chain_of_custody TEXT
);

CREATE TABLE IF NOT EXISTS Vehicle (
    vehicle_id TEXT PRIMARY KEY,
    registration_number TEXT UNIQUE,
    vehicle_type TEXT,
    manufacturer TEXT,
    model TEXT,
    color TEXT,
    manufacture_year INTEGER
);

CREATE TABLE IF NOT EXISTS Phone (
    phone_id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE,
    imei TEXT UNIQUE,
    network_provider TEXT
);

CREATE TABLE IF NOT EXISTS BankAccount (
    account_id TEXT PRIMARY KEY,
    bank_name TEXT,
    account_number TEXT UNIQUE,
    ifsc TEXT,
    account_type TEXT
);

CREATE TABLE IF NOT EXISTS Organization (
    organization_id TEXT PRIMARY KEY,
    organization_name TEXT,
    organization_type TEXT,
    description TEXT
);

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

CREATE TABLE IF NOT EXISTS Conversation (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Message (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    sender TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES Conversation(conversation_id) ON DELETE CASCADE
);

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

CREATE TABLE IF NOT EXISTS PersonAddress (
    person_address_id TEXT PRIMARY KEY,
    person_id TEXT,
    location_id TEXT,
    address_type TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);

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

CREATE TABLE IF NOT EXISTS PersonPhone (
    person_phone_id TEXT PRIMARY KEY,
    person_id TEXT,
    phone_id TEXT,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (phone_id) REFERENCES Phone(phone_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PersonBankAccount (
    person_bank_id TEXT PRIMARY KEY,
    person_id TEXT,
    account_id TEXT,
    relation_type TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES BankAccount(account_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PersonOrganization (
    person_org_id TEXT PRIMARY KEY,
    person_id TEXT,
    organization_id TEXT,
    role TEXT,
    joined_date TEXT,
    FOREIGN KEY (person_id) REFERENCES Person(person_id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES Organization(organization_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CrimeEvidence (
    crime_evidence_id TEXT PRIMARY KEY,
    incident_id TEXT,
    evidence_id TEXT,
    FOREIGN KEY (incident_id) REFERENCES CrimeIncident(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES Evidence(evidence_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fir_case_id ON FIR(case_id);
CREATE INDEX IF NOT EXISTS idx_fir_police_station_id ON FIR(police_station_id);
CREATE INDEX IF NOT EXISTS idx_crime_incident_fir_id ON CrimeIncident(fir_id);
CREATE INDEX IF NOT EXISTS idx_crime_incident_crime_type_id ON CrimeIncident(crime_type_id);
CREATE INDEX IF NOT EXISTS idx_crime_incident_location_id ON CrimeIncident(location_id);
CREATE INDEX IF NOT EXISTS idx_crime_participant_incident_id ON CrimeParticipant(incident_id);
CREATE INDEX IF NOT EXISTS idx_crime_participant_person_id ON CrimeParticipant(person_id);
CREATE INDEX IF NOT EXISTS idx_crime_participant_role ON CrimeParticipant(role);
CREATE INDEX IF NOT EXISTS idx_timeline_event_incident_id ON TimelineEvent(incident_id);
CREATE INDEX IF NOT EXISTS idx_message_conversation_id ON Message(conversation_id);
CREATE INDEX IF NOT EXISTS idx_person_vehicle_person_id ON PersonVehicle(person_id);
CREATE INDEX IF NOT EXISTS idx_person_phone_person_id ON PersonPhone(person_id);
CREATE INDEX IF NOT EXISTS idx_person_bank_account_person_id ON PersonBankAccount(person_id);
CREATE INDEX IF NOT EXISTS idx_person_organization_person_id ON PersonOrganization(person_id);
CREATE INDEX IF NOT EXISTS idx_financial_transaction_from_account_id ON FinancialTransaction(from_account_id);
CREATE INDEX IF NOT EXISTS idx_financial_transaction_to_account_id ON FinancialTransaction(to_account_id);
