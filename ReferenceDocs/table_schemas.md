# Table Name: Case
case_id              UUID (PK)
case_number          VARCHAR(30) UNIQUE
title                VARCHAR(255)
description          TEXT
priority             VARCHAR(20)
status               VARCHAR(20)
created_at           TIMESTAMP
updated_at           TIMESTAMP


# Table Name: PoliceStation
station_id           UUID (PK)
station_name         VARCHAR(150)
district             VARCHAR(100)
city                 VARCHAR(100)
address              TEXT
latitude             DECIMAL(10,7)
longitude            DECIMAL(10,7)


# Table Name: FIR
fir_id               UUID (PK)
case_id              UUID (FK -> Case)
fir_number           VARCHAR(30) UNIQUE
police_station_id    UUID (FK)
filing_date          DATE
complainant_name     VARCHAR(100)
description          TEXT
status               VARCHAR(20)


# Table Name: CrimeIncident
incident_id          UUID (PK)
fir_id               UUID (FK)
crime_type_id        UUID (FK)
mo_id                UUID (FK)
location_id          UUID (FK)
crime_datetime       TIMESTAMP
weapon_used          VARCHAR(100)
severity             SMALLINT
status               VARCHAR(20)
description          TEXT


# Table Name: Person
person_id            UUID (PK)
first_name           VARCHAR(100)
last_name            VARCHAR(100)
gender               VARCHAR(20)
date_of_birth        DATE
occupation           VARCHAR(100)
education_level      VARCHAR(100)
income_group         VARCHAR(50)
nationality          VARCHAR(50)
created_at           TIMESTAMP


# Table Name: Officer
officer_id           UUID (PK)
name                 VARCHAR(100)
badge_number         VARCHAR(30)
rank                 VARCHAR(50)
station_id           UUID (FK)
years_of_service     INT
specialization       VARCHAR(100)


# Table Name: Investigation
investigation_id     UUID (PK)
incident_id          UUID (FK)
officer_id           UUID (FK)
status               VARCHAR(20)
priority             VARCHAR(20)
assigned_date        DATE
closed_date          DATE
next_action          TEXT
remarks              TEXT


# Table Name: Evidence
evidence_id          UUID (PK)
evidence_type        VARCHAR(50)
description          TEXT
collection_date      DATE
forensic_status      VARCHAR(30)
storage_location     VARCHAR(100)
chain_of_custody     TEXT


# Table Name: Location
location_id          UUID (PK)
location_name        VARCHAR(150)
address              TEXT
district             VARCHAR(100)
city                 VARCHAR(100)
state                VARCHAR(100)
postal_code          VARCHAR(20)
latitude             DECIMAL(10,7)
longitude            DECIMAL(10,7)


# Table Name: Vehicle
vehicle_id           UUID (PK)
registration_number  VARCHAR(20)
vehicle_type         VARCHAR(50)
manufacturer         VARCHAR(100)
model                VARCHAR(100)
color                VARCHAR(50)
manufacture_year     INT


# Table Name: Phone
phone_id             UUID (PK)
phone_number         VARCHAR(20)
imei                 VARCHAR(30)
network_provider     VARCHAR(50)


# Table Name: BankAccount
account_id           UUID (PK)
bank_name            VARCHAR(100)
account_number       VARCHAR(30)
ifsc                 VARCHAR(20)
account_type         VARCHAR(30)


# Table Name: FinancialTransaction
transaction_id       UUID (PK)
from_account_id      UUID (FK)
to_account_id        UUID (FK)
amount               DECIMAL(12,2)
transaction_date     TIMESTAMP
transaction_type     VARCHAR(50)
remarks              TEXT


# Table Name: Organization
organization_id      UUID (PK)
organization_name    VARCHAR(150)
organization_type    VARCHAR(50)
description          TEXT


# Table Name: CrimeType
crime_type_id        UUID (PK)
crime_name           VARCHAR(100)
category             VARCHAR(100)
default_severity     SMALLINT


# Table Name: ModusOperandi
mo_id                UUID (PK)
mo_name              VARCHAR(150)
description          TEXT


# Table Name: TimelineEvent
event_id             UUID (PK)
incident_id          UUID (FK)
officer_id           UUID (FK)
event_time           TIMESTAMP
event_type           VARCHAR(50)
description          TEXT


# Table Name: Conversation
conversation_id      UUID (PK)
user_id              VARCHAR(100)
started_at           TIMESTAMP


# Table Name: Message
message_id           UUID (PK)
conversation_id      UUID (FK)
sender               VARCHAR(20)
content              TEXT
created_at           TIMESTAMP


### Relationship Tables

# Table Name: CrimeParticipant
participant_id       UUID (PK)
incident_id          UUID (FK)
person_id            UUID (FK)
role                 VARCHAR(30) --> (Accused,Victim,Witness,Complainant)
injury_status        VARCHAR(30)
arrest_status        VARCHAR(30)
remarks              TEXT


# Table Name: PersonAddress
person_address_id    UUID (PK)
person_id            UUID (FK)
location_id          UUID (FK)
address_type         VARCHAR(30)


# Table Name: PersonVehicle
person_vehicle_id    UUID (PK)
person_id            UUID (FK)
vehicle_id           UUID (FK)
ownership_type       VARCHAR(30)
registered_from      DATE
registered_to        DATE


# Table Name: PersonPhone
person_phone_id      UUID (PK)
person_id            UUID (FK)
phone_id             UUID (FK)
start_date           DATE
end_date             DATE


# Table Name: PersonBankAccount
person_bank_id       UUID (PK)
person_id            UUID (FK)
account_id           UUID (FK)
relation_type        VARCHAR(30)


# Table Name: PersonOrganization
person_org_id        UUID (PK)
person_id            UUID (FK)
organization_id      UUID (FK)
role                 VARCHAR(50)
joined_date          DATE


# TableName: CrimeEvidence
crime_evidence_id    UUID (PK)
incident_id          UUID (FK)
evidence_id          UUID (FK)
