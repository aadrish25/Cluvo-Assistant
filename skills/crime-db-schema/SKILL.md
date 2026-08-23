---
name: crime-db-schema
description: Provides exact column-level SQLite schema (column names, types, constraints, keys) for the crime-records database. Use AFTER you've already decided which tables and join path are relevant (via the table catalog in your instructions). Load only the specific table(s) you need with get_skill_reference — do not load every table's schema for a single query.
metadata:
  version: "1.0.0"
  tags: ["text2sql", "schema", "crime-db"]
---

# Crime DB Schema (on-demand)

This skill holds exact schema for each table in the crime-records SQLite
database, one file per table under `references/`.

## When to use

Only after you already know which tables you need — that decision should
come from the table catalog you already have (relationship reasoning, join
paths, domain rules). This skill does not repeat that reasoning; it only
gives you exact column definitions once you know what to look up.

## How to use

Call `get_skill_reference("crime-db-schema", "<TableName>.md")` for each
table your query touches. Load only what you need — e.g. a query joining
`FIR -> CrimeIncident -> CrimeParticipant -> Person` needs four reference
calls, not twenty.

## Available tables

Case, PoliceStation, FIR, CrimeIncident, Person, Officer, Investigation,
Evidence, Location, Vehicle, Phone, BankAccount, FinancialTransaction,
Organization, CrimeType, ModusOperandi, TimelineEvent, Conversation,
Message, CrimeParticipant, PersonAddress, PersonVehicle, PersonPhone,
PersonBankAccount, PersonOrganization, CrimeEvidence

Each reference file follows the same layout: table purpose (one line),
then a column list with type, nullability, and key constraints.
