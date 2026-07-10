# Text2SQL Table Catalog

This catalog is for table discovery and relationship reasoning only. It should help the SQL agent decide which tables are relevant before it loads exact schemas from the separate schema document.

Do not treat this file as the source of table schemas. Use it for:
- table purpose
- when a table is relevant
- important foreign-key relationships
- common join paths
- domain interpretation rules

## Core Rules

- Generate read-only SQLite queries only.
- Prefer human-readable fields in final results, such as FIR number, case number, person name, police station name, organization name, crime name, and district.
- Do not assume `Person` has a permanent role. A person becomes accused, victim, or witness through `CrimeParticipant.role`.
- Complainants are stored as free-text in `FIR.complainant_name`; do not search for `CrimeParticipant.role = 'Complainant'`.
- For FIR-level participant questions, use `FIR -> CrimeIncident -> CrimeParticipant -> Person`.
- For district, city, map, and hotspot questions, usually use `CrimeIncident -> Location`.
- For FIR filing jurisdiction, use `FIR -> PoliceStation`.
- Quote `"Case"` in SQL because `CASE` is SQL syntax.
- If a user asks for only 2 or 3 obvious entities, still include required bridge tables.

## Common Relationship Paths

### FIR To Incidents

Path: `FIR -> CrimeIncident`

Use when the user asks for incidents, crime type, modus operandi, location, severity, or incident status under a FIR.

### FIR To People

Path: `FIR -> CrimeIncident -> CrimeParticipant -> Person`

Use when the user asks for accused persons, victims, witnesses, co-accused, or people linked to a FIR.

Role filters:
- Accused: `CrimeParticipant.role = 'Accused'`
- Victim: `CrimeParticipant.role = 'Victim'`
- Witness: `CrimeParticipant.role = 'Witness'`
Complainants are not participant-role rows in the seeded data; use `FIR.complainant_name`.

### FIR To Police Station

Path: `FIR -> PoliceStation`

Use when the user asks where a FIR was filed, station-wise FIRs, station district, station city, or police station jurisdiction.

### Incident To Crime Location

Path: `CrimeIncident -> Location`

Use when the user asks about crime district, city, address, coordinates, hotspots, maps, or geographic distribution.

### Incident To Crime Classification

Path: `CrimeIncident -> CrimeType`

Use when the user asks about chain snatching, vehicle theft, fraud, robbery, assault, crime category, property crime, violent crime, economic crime, or crime-type trends.

### Incident To Modus Operandi

Path: `CrimeIncident -> ModusOperandi`

Use when the user asks about method, pattern, MO, distract-and-snatch, forced entry, phishing, gang attack, or similar operating style.

### Incident To Investigation And Officer

Path: `CrimeIncident -> Investigation -> Officer -> PoliceStation`

Use when the user asks about assigned officer, investigation status, next action, officer workload, officer station, rank, or badge number.

### Incident Timeline

Path: `CrimeIncident -> TimelineEvent -> Officer`

Use when the user asks for investigation timeline, case chronology, FIR registration event, evidence collection event, arrest event, or witness examination event.

### Incident Evidence

Path: `CrimeIncident -> CrimeEvidence -> Evidence`

Use when the user asks what evidence was collected, forensic status, storage location, CCTV, documents, bank records, vehicles, or chain of custody.

### Organization Members

Path: `Organization -> PersonOrganization -> Person`

Use when the user asks for gang members, organization leaders, associates, or people connected to an organization.

### Organization Cases

Path: `Organization -> PersonOrganization -> Person -> CrimeParticipant -> CrimeIncident -> FIR`

Use when the user asks for FIRs or incidents involving a gang, syndicate, or organization.

Usually filter participants to accused:
`CrimeParticipant.role = 'Accused'`

### Person Vehicles

Path: `Person -> PersonVehicle -> Vehicle`

Use when the user asks about vehicles owned, used, borrowed, suspected, registration number, vehicle color, or shared vehicles.

### Person Phones

Path: `Person -> PersonPhone -> Phone`

Use when the user asks about phone numbers, IMEI, active SIMs, network provider, or phones linked to a person.

### Person Addresses

Path: `Person -> PersonAddress -> Location`

Use when the user asks where a person lives, known addresses, current address, permanent address, or person-associated district.

### Person Bank Accounts

Path: `Person -> PersonBankAccount -> BankAccount`

Use when the user asks about bank accounts linked to a person, account holders, suspected beneficiaries, or financial profile.

### Financial Trail

Path: `Person -> PersonBankAccount -> BankAccount -> FinancialTransaction -> BankAccount -> PersonBankAccount -> Person`

Use when the user asks about money flow, financial links, transactions between suspects, account transfers, or financial trail between gang members.

### Chat History

Path: `Conversation -> Message`

Use only for stored chat history, follow-up context, previous user messages, or assistant responses. Do not use these tables for crime records.

## Table Catalog

## "Case"

Purpose: High-level case file that groups FIRs and stores case-level status, priority, title, and description.

Use when:
- The user asks about case files or case numbers.
- The user asks for case-level status or priority.
- The user asks for a case summary that starts above the FIR level.

Relationships:
- `"Case" -> FIR`

Notes:
- Quote `"Case"` in SQL.
- Join onward to `FIR` and `CrimeIncident` for operational crime facts.

## PoliceStation

Purpose: Police station master data for FIR filing jurisdiction and officer assignment.

Use when:
- The user asks about police stations.
- The user filters FIRs by station, station district, or station city.
- The user asks which officers belong to a station.

Relationships:
- `PoliceStation -> FIR`
- `PoliceStation -> Officer`

Notes:
- Use `PoliceStation` for filing jurisdiction.
- Use `Location` for where a crime happened.

## FIR

Purpose: Formal police report for one or more crime incidents.

Use when:
- The user mentions a FIR number.
- The user asks about FIR status, filing date, complainant, or station.
- The user asks for FIRs matching a crime type, date range, district, accused person, or organization.

Relationships:
- `FIR -> "Case"`
- `FIR -> PoliceStation`
- `FIR -> CrimeIncident`

Notes:
- FIR is usually the anchor table for user-facing case lookup.
- Always include FIR number in results when returning FIR or incident records.

## CrimeIncident

Purpose: Atomic crime event connected to FIR, crime type, modus operandi, and location.

Use when:
- The user asks about incidents.
- The user asks about crime date/time, severity, weapon, status, crime type, MO, or location.
- The user asks for analytics, trends, counts, hotspots, or district crime patterns.

Relationships:
- `CrimeIncident -> FIR`
- `CrimeIncident -> CrimeType`
- `CrimeIncident -> ModusOperandi`
- `CrimeIncident -> Location`
- `CrimeIncident -> CrimeParticipant`
- `CrimeIncident -> Investigation`
- `CrimeIncident -> TimelineEvent`
- `CrimeIncident -> CrimeEvidence`

Notes:
- Most crime analytics queries start from `CrimeIncident`.

## Person

Purpose: Master person entity. People can be accused, victims, witnesses, gang members, account holders, phone users, vehicle users, or address holders depending on relationship tables.

Use when:
- The user asks about a named person.
- The user asks for accused, victims, witnesses, gang members, repeat offenders, account holders, vehicle users, phone users, or known addresses.

Relationships:
- `Person -> CrimeParticipant`
- `Person -> PersonAddress`
- `Person -> PersonVehicle`
- `Person -> PersonPhone`
- `Person -> PersonBankAccount`
- `Person -> PersonOrganization`

Notes:
- Never infer accused/victim/witness status directly from `Person`.

## Officer

Purpose: Police officer records for investigation assignment and timeline events.

Use when:
- The user asks about assigned officer, officer rank, badge, specialization, station, or officer workload.
- The user asks who performed an investigation event.

Relationships:
- `Officer -> PoliceStation`
- `Officer -> Investigation`
- `Officer -> TimelineEvent`

## Investigation

Purpose: Investigation workflow and assignment for an incident.

Use when:
- The user asks investigation status, assigned officer, priority, next action, open investigations, closed investigations, or pending work.

Relationships:
- `Investigation -> CrimeIncident`
- `Investigation -> Officer`

Notes:
- For investigation progress, prefer `Investigation.status`.
- For FIR registration status, use `FIR.status`.
- For incident status, use `CrimeIncident.status`.
- For case-level status, use `"Case".status`.

## Evidence

Purpose: Evidence item records such as CCTV, bank records, documents, vehicles, mobile devices, or witness statements.

Use when:
- The user asks what evidence exists.
- The user asks about forensic status, chain of custody, or evidence storage.

Relationships:
- `Evidence -> CrimeEvidence`

Common path:
- `FIR -> CrimeIncident -> CrimeEvidence -> Evidence`

## Location

Purpose: Geographic location for crimes and person addresses.

Use when:
- The user asks about district, city, address, coordinates, hotspots, crime maps, or where a crime happened.
- The user asks about a person's known/current/permanent address.

Relationships:
- `Location -> CrimeIncident`
- `Location -> PersonAddress`

Notes:
- For crime geography, join through `CrimeIncident`.
- For station geography, use `PoliceStation`.

## Vehicle

Purpose: Vehicle records linked to people.

Use when:
- The user asks about suspect vehicles, vehicle registration, vehicle type, color, model, owner, user, or shared vehicle links.

Relationships:
- `Vehicle -> PersonVehicle`

Common path:
- `Person -> PersonVehicle -> Vehicle`

## Phone

Purpose: Phone, SIM, or device records linked to people.

Use when:
- The user asks about phone numbers, IMEI, network provider, active SIMs, or phones linked to accused/persons.

Relationships:
- `Phone -> PersonPhone`

Common path:
- `Person -> PersonPhone -> Phone`

## BankAccount

Purpose: Bank account records linked to people and transactions.

Use when:
- The user asks about bank accounts, account holders, suspicious accounts, or financial profiles.

Relationships:
- `BankAccount -> PersonBankAccount`
- `BankAccount -> FinancialTransaction` as source account
- `BankAccount -> FinancialTransaction` as destination account

Common paths:
- `Person -> PersonBankAccount -> BankAccount`
- `BankAccount -> FinancialTransaction -> BankAccount`

## FinancialTransaction

Purpose: Transfer records between bank accounts.

Use when:
- The user asks about money transfers, financial trail, transaction amounts, account-to-account links, or transactions between suspects.

Relationships:
- `FinancialTransaction -> BankAccount` source account
- `FinancialTransaction -> BankAccount` destination account

Notes:
- To identify people behind source and destination accounts, join each account through `PersonBankAccount` to `Person`.

## Organization

Purpose: Criminal organization, gang, syndicate, or financial crime network.

Use when:
- The user asks about gangs, gang members, leaders, associates, organizations, syndicates, or cases involving a named organization.

Relationships:
- `Organization -> PersonOrganization`

Common path:
- `Organization -> PersonOrganization -> Person -> CrimeParticipant -> CrimeIncident -> FIR`

## CrimeType

Purpose: Crime taxonomy such as chain snatching, vehicle theft, fraud, robbery, assault, and broader crime categories.

Use when:
- The user asks by crime name or crime category.
- The user asks for trend, count, or comparison by crime type/category.

Relationships:
- `CrimeType -> CrimeIncident`

## ModusOperandi

Purpose: Method or pattern used to commit a crime.

Use when:
- The user asks about MO, method, operating pattern, similar method, distract-and-snatch, forced entry, phishing, or gang attack.

Relationships:
- `ModusOperandi -> CrimeIncident`

## TimelineEvent

Purpose: Chronological investigation events for incident and FIR summaries.

Use when:
- The user asks for timeline, chronology, FIR registration events, evidence collection events, arrest events, witness examination, or case summary.

Relationships:
- `TimelineEvent -> CrimeIncident`
- `TimelineEvent -> Officer`

Common path:
- `FIR -> CrimeIncident -> TimelineEvent -> Officer`

## Conversation

Purpose: Chat conversation session metadata.

Use when:
- The user asks about saved chat history.
- The agent needs stored context for follow-up questions.

Relationships:
- `Conversation -> Message`

Notes:
- Do not use for crime records.

## Message

Purpose: Stored chat messages within a conversation.

Use when:
- The user asks about previous messages or conversation history.
- The agent needs previous user/assistant turns for follow-up context.

Relationships:
- `Message -> Conversation`

Notes:
- Do not use for crime records.

## CrimeParticipant

Purpose: Bridge table connecting people to incidents with a role.

Use when:
- The user asks about accused, victims, witnesses, co-accused, repeat offenders, or people linked to crimes.

Relationships:
- `CrimeParticipant -> CrimeIncident`
- `CrimeParticipant -> Person`

Important role logic:
- Accused means `CrimeParticipant.role = 'Accused'`
- Victim means `CrimeParticipant.role = 'Victim'`
- Witness means `CrimeParticipant.role = 'Witness'`
Complainants are stored in `FIR.complainant_name`, not as `CrimeParticipant.role`.

Notes:
- Repeat offenders are found by grouping accused participation by person.
- Co-accused are people who share the same incident as accused.

## PersonAddress

Purpose: Bridge table connecting people to locations as addresses.

Use when:
- The user asks for a person's address, current address, permanent address, or address district.

Relationships:
- `PersonAddress -> Person`
- `PersonAddress -> Location`

## PersonVehicle

Purpose: Bridge table connecting people to vehicles.

Use when:
- The user asks which vehicles a person owns or uses.
- The user asks who is linked to a vehicle.
- The user asks for shared vehicle connections.

Relationships:
- `PersonVehicle -> Person`
- `PersonVehicle -> Vehicle`

## PersonPhone

Purpose: Bridge table connecting people to phones.

Use when:
- The user asks which phones a person uses.
- The user asks who is linked to a phone number or IMEI.
- The user asks for active SIMs.

Relationships:
- `PersonPhone -> Person`
- `PersonPhone -> Phone`

## PersonBankAccount

Purpose: Bridge table connecting people to bank accounts.

Use when:
- The user asks which accounts belong to a person.
- The user asks which people are linked to an account.
- The user asks for financial links involving people.

Relationships:
- `PersonBankAccount -> Person`
- `PersonBankAccount -> BankAccount`

Common path:
- `Person -> PersonBankAccount -> BankAccount -> FinancialTransaction`

## PersonOrganization

Purpose: Bridge table connecting people to organizations with membership role.

Use when:
- The user asks gang membership, leaders, members, associates, or organization role.

Relationships:
- `PersonOrganization -> Person`
- `PersonOrganization -> Organization`

Common path:
- `Organization -> PersonOrganization -> Person -> CrimeParticipant -> CrimeIncident -> FIR`

## CrimeEvidence

Purpose: Bridge table connecting incidents to evidence items.

Use when:
- The user asks evidence for an incident, FIR, or case.
- The user asks which incidents have a specific evidence type.

Relationships:
- `CrimeEvidence -> CrimeIncident`
- `CrimeEvidence -> Evidence`

Common path:
- `FIR -> CrimeIncident -> CrimeEvidence -> Evidence`

## Query Recipes

### Accused In A FIR

Tables to select:
- `FIR`
- `CrimeIncident`
- `CrimeParticipant`
- `Person`

Path:
`FIR -> CrimeIncident -> CrimeParticipant -> Person`

Filter:
- FIR number
- `CrimeParticipant.role = 'Accused'`

### Victims Or Witnesses In A FIR

Tables to select:
- `FIR`
- `CrimeIncident`
- `CrimeParticipant`
- `Person`

Path:
`FIR -> CrimeIncident -> CrimeParticipant -> Person`

Filter:
- FIR number
- participant role

### FIRs In A Crime District

Tables to select:
- `FIR`
- `CrimeIncident`
- `Location`

Path:
`FIR -> CrimeIncident -> Location`

Use this when the district is where the crime happened.

### FIRs Filed In A Police Station District

Tables to select:
- `FIR`
- `PoliceStation`

Path:
`FIR -> PoliceStation`

Use this when the district is about where the FIR was filed.

### Repeat Offenders

Tables to select:
- `CrimeParticipant`
- `Person`

Logic:
- Filter role to accused.
- Group by person.
- Sort by accused incident count descending.

### Gang Members

Tables to select:
- `Organization`
- `PersonOrganization`
- `Person`

Path:
`Organization -> PersonOrganization -> Person`

### Gang Cases

Tables to select:
- `Organization`
- `PersonOrganization`
- `Person`
- `CrimeParticipant`
- `CrimeIncident`
- `FIR`

Path:
`Organization -> PersonOrganization -> Person -> CrimeParticipant -> CrimeIncident -> FIR`

Usually filter `CrimeParticipant.role = 'Accused'`.

### Person Criminal Network

Tables to select depending on question:
- `Person`
- `CrimeParticipant`
- `CrimeIncident`
- `PersonOrganization`
- `Organization`
- `PersonVehicle`
- `Vehicle`
- `PersonPhone`
- `Phone`
- `PersonBankAccount`
- `BankAccount`

Network signals:
- co-accused via shared incidents
- organizations via `PersonOrganization`
- vehicles via `PersonVehicle`
- phones via `PersonPhone`
- accounts via `PersonBankAccount`

### Financial Trail

Tables to select:
- `Person`
- `PersonBankAccount`
- `BankAccount`
- `FinancialTransaction`

Use separate aliases for source and destination accounts and people.

### Case Timeline

Tables to select:
- `"Case"`
- `FIR`
- `CrimeIncident`
- `TimelineEvent`
- `Officer`

Path:
`"Case" -> FIR -> CrimeIncident -> TimelineEvent -> Officer`

Sort timeline events chronologically.

### Evidence For FIR

Tables to select:
- `FIR`
- `CrimeIncident`
- `CrimeEvidence`
- `Evidence`

Path:
`FIR -> CrimeIncident -> CrimeEvidence -> Evidence`

### Crime Hotspots

Tables to select:
- `CrimeIncident`
- `Location`
- optionally `CrimeType`

Group by:
- district
- city
- location
- coordinates

Useful aggregates:
- incident count
- average severity

### Monthly Crime Trend

Tables to select:
- `CrimeIncident`
- optionally `CrimeType`

Logic:
- Group incidents by month.
- Optionally break down by crime type or category.
