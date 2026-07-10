# Crime Intelligence Platform — Prototype Guide

> KSP Datathon 2026 · Karnataka State Police  
> Deadline: July 19, 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Project Vision](#2-project-vision)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Why Agentic AI?](#4-why-agentic-ai)
5. [Data Architecture](#5-data-architecture)
6. [Crime World Simulator](#6-crime-world-simulator)
7. [Agent Architecture](#7-agent-architecture)
8. [Implementation Plan](#8-implementation-plan)
9. [Folder Structure](#9-folder-structure)
10. [Development Roadmap](#10-development-roadmap)
11. [Future Scope](#11-future-scope)

---

## 1. Introduction

### The Hackathon

The KSP Datathon 2026 is a challenge issued by the Karnataka State Police to build an **Intelligent Conversational AI and Crime Analytics Platform** — a system that lets investigators, analysts, and policymakers interact with crime data using natural language, discover hidden criminal networks, and make data-driven decisions faster.

The problem statement asks for conversational AI, criminal network analysis, crime pattern detection, sociological insights, offender profiling, investigator decision support, financial crime analysis, crime forecasting, explainable AI, and role-based access control — all in one system.

### The Problem We Are Solving

Today, a police investigator sitting in a station faces a problem that has nothing to do with intelligence or effort. The problem is **access**.

Crime data exists. FIRs are filed. Accused persons are recorded. Locations are logged. Connections between cases are sometimes visible — but only to someone who knows exactly what to look for, knows how to query a database, and has the time to manually cross-reference records across dozens of files.

Most investigators don't have a data analyst sitting next to them. They don't know SQL. They can't run network graphs. They work with what they can remember and what they can find by scrolling through printed FIR copies.

The result: patterns that exist in the data go unseen. A repeat offender's history isn't surfaced during a new investigation. A gang's financial trail — spread across five bank accounts and three incidents — looks like three unrelated cases. A seasonal crime surge in a particular district gets noticed only after it's already peaked.

Our platform exists to solve this access problem. Not with a dashboard that requires training. With a conversation.

### What We Are NOT Building

We are not attempting to replicate the complete KSP crime management system. We are not building a replacement for existing police software, a real-time FIR ingestion pipeline, or an enterprise-grade data warehouse.

We are building a **working prototype** that demonstrates how conversational AI, graph analytics, and crime intelligence can assist investigators in finding answers they couldn't easily find before. The prototype uses realistic synthetic data, a carefully designed schema, and a multi-agent AI system to show what this class of tool can do.

The goal is to prove the concept convincingly enough that someone watching the demo thinks: *this should exist in every police station.*

---

## 2. Project Vision

### How Investigators Work Today

An investigator receives a new case — say, a chain snatching in Bengaluru Urban. They file the FIR. They record the accused's details. They note the location. They close the file and move on to the next one.

A week later, a similar incident happens two kilometers away. Same modus operandi. Different officer. Different file. No connection drawn.

Three months later, someone in a senior office is manually reviewing case files and notices the pattern. By then, the accused has been involved in four more incidents.

The limitation isn't human intelligence — it's that the data connecting these cases lives in a database that nobody has a natural way to question. The investigator would have to know to ask "show me all chain snatchings in this district in the last 90 days using the distract-and-snatch method" — and then know how to actually run that query.

### The Shift We Are Making

Instead of this:

```
Database → Dashboard
```

We are building this:

```
Investigator
     ↓
 Conversation
     ↓
     AI
     ↓
 Database
     ↓
  Insights
```

The investigator types a question the way they would ask a colleague: *"Show me chain-snatching cases in this district over the last six months."* The system understands the question, queries the right tables, and responds in plain language — with the data to back it up.

This is the shift from tools that require expertise to tools that amplify it.

### What Good Looks Like

A senior officer opens the platform. They type: *"Show me all cases involving accused persons linked to the Bengaluru North Gang in the last year."*

The system identifies the organization, traverses the criminal network, finds every incident where a gang member appeared as accused, and returns a structured response with FIR numbers, locations, dates, and co-accused — along with a visualization of the network.

The officer then asks: *"Among these, which ones are still under investigation?"* Without re-entering context, the system narrows the results.

Then: *"Generate a summary report for FIR KSP/2023/0042."* The system pulls the full case timeline, participants, evidence, and investigation status, and produces a readable narrative.

That entire exchange — three questions, three different kinds of analysis — takes under two minutes. Without the platform, it would take hours of manual cross-referencing, if it happened at all.

---

## 3. High-Level Architecture

```
                    User
                      │
                      ▼
             React Chat UI
       (Chat · Network · Map · Charts · PDF)
                      │
                      ▼
             FastAPI Backend
              WebSocket /ws/chat
                      │
                      ▼
        Cluvo Investigation Team
      Agno Team in coordinate mode
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 General Agent  Text2SQL Agent  Graph Agent
        │             │             │
        ├─────────────┼─────────────┤
        ▼             ▼
 Analytics Agent  Summary Agent
        │             │
        └─────────────┼─────────────┘
                      ▼
          Assistant response + artifacts
                      │
                      ▼
        SQLite + NetworkX/Pyvis + ReportLab
```

### What Each Block Does

**React Chat UI**
The user-facing interface. Four panels: a chat window for natural language conversation, a network graph viewer for criminal relationship visualization, a hotspot map for geographic crime distribution, and analytics charts for trends over time. The chat panel is the entry point for everything.

**FastAPI Backend**
A thin WebSocket layer. It accepts chat messages at `/ws/chat`, initializes the user/session context once per session, passes each message to the Cluvo investigation team, and returns the assistant response plus artifacts. No business logic lives here.

**Cluvo Investigation Team**
The brain of the system. Cluvo is implemented as an Agno `Team` in coordinate mode. It reads the user's message, uses conversation history and session state, rewrites ambiguous follow-ups when possible, and delegates the task to the correct specialist agent.

**The Agents**
Each agent is a specialized unit with its own tools, system prompt, and data-access pattern. The General Agent handles greetings and ambiguous fallback messages. The Text2SQL Agent queries structured records. The Graph Agent builds person-centered networks. The Analytics Agent computes aggregate insights. The Summary Agent generates FIR reports and saves them as PDFs.

**Response + Artifacts**
The WebSocket response always carries a natural-language message and may include artifacts from session state: graph HTML paths, PDF report paths, chart data, map data, and table data.

**Data Layer**
SQLite for all structured data (all 26 tables from the data model). NetworkX builds in-memory relationship graphs, Pyvis saves graph HTML files, and ReportLab saves FIR summary reports as PDFs. Similar-case semantic search is future scope, not part of the current implementation.

---

## 4. Why Agentic AI?

### Why Not One Giant LLM?

The first instinct when building a conversational AI system is to send everything to a single large language model and let it figure it out. Pass it the question. Pass it the schema. Tell it to generate SQL. Get an answer. Simple.

The problem is that this approach collapses under real-world complexity very quickly.

A question like *"show me crime trends in Bengaluru"* requires aggregate computation over many rows — something an LLM should not improvise. A question like *"show the network around this person"* requires graph construction — not a plain SQL answer. A question like *"generate a report for this FIR"* requires structured retrieval plus professional narrative generation and PDF export.

No single approach handles all of these. When you force one LLM to do all of it, it either fails on the hard cases or becomes so over-prompted that it starts making things up.

### Why Separate Agents?

Each agent is a specialist. It has exactly the tools it needs for its class of problem and nothing more.

- The General Agent handles greetings, appreciation, platform help, unsupported requests, and unclear messages.
- The Text2SQL Agent reads the table catalog, pulls only the needed schemas, generates safe read-only SQL, executes it, and explains the result.
- The Graph Agent builds person-centered NetworkX graphs from deterministic database queries and saves Pyvis HTML files.
- The Analytics Agent runs fixed analytics tools for district counts, monthly trends, crime type/category breakdowns, hotspots, and repeat offenders.
- The Summary Agent builds structured FIR context, writes a professional report, and saves the generated report as a PDF.

Separation also means each agent can be tested independently. If the SQL agent returns wrong results, you fix the SQL agent. If the graph agent shows incomplete networks, you adjust the traversal depth. You never have to untangle a single monolithic prompt that tries to do everything.

### Responsibilities and Dispatch

| Intent | Example query | Agent called |
|---|---|---|
| General/fallback | "Hi", "What can you do?", unclear follow-up | General Agent |
| Record lookup | "Show all FIRs in Mysuru in January 2024" | SQL Agent |
| Relationship query | "Who are the co-accused of Ravi Kumar?" | Graph Agent |
| Trend analysis | "Which district has the most thefts this year?" | Analytics Agent |
| Case summary | "Summarize FIR KSP/2023/0042" | Summary Agent |

The router does not return a JSON classification to the user. It delegates internally to the best-fit agent, rewriting the query into a standalone request when the user's message depends on context. If the request cannot be resolved safely, it delegates to the General Agent to ask a short clarification question.

---

## 5. Data Architecture

### The Entities in Our World

A crime investigation involves a small set of real-world entities. Our schema is built around them.

**Person** is the central entity. Everyone — accused, victim, witness, officer — is a Person. The role they play in a given incident is captured in the relationship, not in the person record itself. This means one person can be an accused in one case and a witness in another, without any duplication of their identity record.

**Crime Incident** is the atomic unit of crime. A single event — a theft, an assault, a fraud — that happened at a place, at a time, with a method, and involved people. Every investigation traces back to one or more incidents.

**FIR** is the formal wrapper around one or more incidents. It's what gets filed at a police station. A FIR has a number, a date, a filing officer, and a description. Incidents live inside FIRs.

**Location** is where things happen. Every incident has a location with a district, city, and geographic coordinates. These coordinates are what make hotspot maps possible.

**Organization** represents structured criminal groups — gangs, syndicates, networks. A Person can be a member of an Organization with a specific role (leader, member, associate).

**Vehicle, Phone, BankAccount** are the artifacts that link people to incidents and to each other. Two people who share a vehicle, or whose bank accounts have transacted with each other, are connected in ways that may not be obvious from case files alone.

### Why the Schema Is Designed This Way

The most important design decision in the schema is the `CrimeParticipant` table:

```
CrimeParticipant(incident_id, person_id, role)
```

This single join table is what makes every person-incident query possible. Instead of separate tables for accused and victims, one table handles all roles. The query for *"who are the accused in this FIR?"* and *"who are the victims?"* are identical in structure — only the `role` filter changes. This means the SQL agent's system prompt can describe one pattern and apply it universally.

The `TimelineEvent` table is what makes case summaries possible. Every significant event in an investigation — FIR registered, arrest made, evidence collected, chargesheet filed — is a row. To generate a narrative timeline, the summary agent just reads these rows in order and asks the LLM to turn them into prose.

Conversation continuity is handled by Agno memory plus Cluvo's session state. Each WebSocket message carries a `user_id` and `session_id`; the backend initializes that session once, then reuses the stored state and recent history for follow-up questions.

### Entity Relationships (Key Ones)

```
Person ─── CrimeParticipant ─── CrimeIncident ─── FIR ─── Case
  │                                    │
  ├── PersonVehicle ─── Vehicle        └── Location
  ├── PersonPhone ─── Phone            └── CrimeType
  ├── PersonBankAccount ─── BankAccount └── ModusOperandi
  └── PersonOrganization ─── Organization
                                        │
                              FinancialTransaction
                              (BankAccount → BankAccount)
```

Every path in this graph is a potential investigative lead. Two people who share no direct connection in the `CrimeParticipant` table might be linked through a shared organization, a shared vehicle, or a financial transaction between their accounts. The graph agent's job is to surface those paths.

---

## 6. Crime World Simulator

### Why Random Data Is Bad

The naive approach to synthetic data is to generate rows randomly. Pick a random crime type. Pick a random location. Pick a random person. Repeat 500 times.

The problem is that random data is analytically dead. When you run a hotspot query, every district looks equally active. When you build a criminal network, every accused is isolated. When you compute trends, every month looks the same. There is nothing for the AI to find because there is nothing there.

For a hackathon demo, this is fatal. The judges will ask you to show something interesting and the system will return a flat, featureless answer.

Our synthetic data generator is not a random data generator. It is a **crime world simulator**. It constructs a world with structure, with hidden patterns, with stories — and then the AI's job is to find them.

### The Crime Stories We Plant

We don't generate 500 random FIRs. We generate a world with the following stories embedded in it:

**Story 1: The Bengaluru North Gang**
A criminal organization with one leader and four members. They are responsible for a disproportionate share of chain snatchings and vehicle thefts in Bengaluru Urban. Their incidents cluster around three specific police station areas. Their bank accounts have financial transactions running between them. When an investigator pulls the network for any one member, the full gang structure emerges.

**Story 2: The Repeat Offender**
Five specific person IDs appear as accused in significantly more incidents than the average. They move across districts. They appear with different co-accused in different incidents. Their prior conviction count is high. A risk score computation will flag them immediately.

**Story 3: The Festival Season Spike**
October and November — the festival months in Karnataka — carry approximately twice the volume of property crimes compared to other months. This pattern is visible in the monthly trend chart. It's the kind of seasonal insight that a policymaker would want to act on proactively.

**Story 4: The Bengaluru Urban Hotspot**
Approximately 40% of all incidents are geographically clustered in the Bengaluru Urban district. Within that district, three specific location clusters account for a majority of those incidents. The hotspot map should make this immediately visible.

**Story 5: The Financial Trail**
The gang members' bank accounts have a series of transactions between them — amounts ranging from petty cash to large transfers, labeled with vague purposes like "goods" or "loan repayment." The financial transaction graph is a money trail that connects people who might otherwise appear unrelated.

### Hidden Patterns

Beyond the explicit stories, the simulator also generates subtler patterns that the AI can surface:

- Certain modus operandi cluster with certain crime types (the "distract-and-snatch" MO appears almost exclusively in chain snatching incidents)
- Younger accused (age 18–25) tend to appear in robbery and vehicle theft; older accused in fraud
- Incidents involving gang members have higher average severity scores than incidents involving solo accused
- The "Gang attack" MO always involves more than one accused

These correlations emerge from the rules we write into the generator — not from the data being random.

### Relationship Rules

The simulator enforces the following rules when generating data:

```
1. Repeat offenders appear as accused in 8–15 incidents each
2. Gang members always appear as co-accused in at least 3 shared incidents
3. Gang members' bank accounts must have at least 5 transactions between them
4. 40% of all incidents are assigned to Bengaluru Urban locations
5. October and November months receive 2x the incident weight
6. The "distract-and-snatch" MO is only assigned to chain snatching incidents
7. Every incident has exactly 1 victim and 1–3 accused
8. Every gang member owns a vehicle (motorcycle, typically black)
9. Repeat offenders have PersonPhone records with active SIM cards
10. Every incident generates at least one TimelineEvent (FIR registration)
```

These rules ensure that the data has the structure needed for every analytical capability we are demonstrating.

### Dataset Size

The prototype uses the following scale:

| Entity | Count | Reason |
|---|---|---|
| FIRs | 500 | Enough for trend analysis to show meaningful patterns |
| Persons | 200 | Realistic ratio of accused/victims to incident volume |
| Repeat offenders | 5 | Clearly identifiable in network and frequency analysis |
| Gang members | 5 | One organization, one leader, four members |
| Locations | 120 | 15 per district × 8 districts |
| Incidents | ~520 | Slightly more than FIRs (some FIRs have multiple incidents) |
| Timeline events | ~700 | At least one per incident, more for high-priority cases |
| Financial transactions | 30 | Enough to show a money trail between gang accounts |

This scale is small enough to seed in seconds and large enough for all analytics to produce non-trivial results.

### Generating the Data

```python
# The key insight: generate stories first, then fill the rest randomly

def seed_all():
    # 1. Create the world's geography
    seed_locations()         # 8 Karnataka districts, 15 locations each

    # 2. Create the crime taxonomy
    seed_crime_types()       # 10 crime types with IPC mappings
    seed_modus_operandi()    # 5 MO patterns with dispatch rules

    # 3. Plant Story 1: The Gang
    gang_org_id = create_gang("Bengaluru North Gang", member_count=5)

    # 4. Plant Story 2: Repeat offenders (the 5 gang members)
    repeat_offender_ids = get_gang_members(gang_org_id)

    # 5. Plant Story 5: Financial trail
    create_financial_trail(repeat_offender_ids)

    # 6. Generate 500 FIRs with embedded patterns
    for i in range(500):
        district = pick_district_with_hotspot_bias()   # Story 4
        date = pick_date_with_seasonal_bias()           # Story 3
        accused = pick_accused_with_repeat_offender_bias(repeat_offender_ids)
        create_fir_with_incident(district, date, accused)
```

The full generator code is in `database/seed_data.py`.

---

## 7. Agent Architecture

### The Flow

Every message from the user enters the WebSocket route and follows this path:

```text
User message
      |
      v
FastAPI /ws/chat
      |
      v
Session initialization
(user_id + session_id)
      |
      v
Cluvo InvestigationTeam
(Agno Team, coordinate mode)
      |
      v
Router prompt delegates to one specialist
      |
      +-- General Agent
      +-- Text2SQL Agent
      +-- Graph Agent
      +-- Analytics Agent
      +-- Summary Agent
      |
      v
Assistant response + artifacts
(message + graph paths + PDF path + chart/map/table data)
```

### Cluvo Router

The router is the parent Agno team prompt. It does not return a classification JSON to the user. It decides which member agent should handle the request and delegates the work internally.

The router is responsible for:
- reading the latest user message
- using session history to resolve references like "that FIR" or "this person"
- rewriting follow-ups into standalone specialist requests when possible
- delegating to exactly one best-fit agent
- sending unclear or unsupported requests to the General Agent

This keeps the user experience assistant-like: the user talks to Cluvo, while the specialist routing stays internal.

### The General Agent

**When it's called:** Greetings, appreciation, simple platform help, unsupported requests, and ambiguous messages that cannot be safely routed.

**How it works:** The General Agent responds conversationally, explains what Cluvo can do, or asks one short clarification question. It does not query the crime database directly.

**Example flow:**
```text
Query:  "Show me that one"
Router: No clear FIR, person, chart, or graph target in context
Agent:  General Agent
Result: "Which FIR, person, or result should I use?"
```

### The Text2SQL Agent

**When it's called:** Any query that asks about specific records. FIR lookups, accused person details, victim information, investigation status, case lists filtered by district or date.

**How it works:** The Text2SQL Agent first reads `AgentDocs/Text2SQL/table_catalog.md` to understand table purposes and relationships. It then pulls exact schemas from `AgentDocs/Text2SQL/table_schemas.md` only for the selected tables, generates one safe read-only SQLite query, executes it, and explains the returned rows.

**Tools:**
- `read_table_catalog()`
- `get_table_schema(table_name)`
- `get_table_schemas(table_names)`
- `execute_sql_query(query)`

**Important rules:** The agent may generate only `SELECT` or read-only `WITH` queries. It must use real seeded role values: `Accused`, `Victim`, and `Witness`. Complainants come from `FIR.complainant_name`, not `CrimeParticipant.role`.

**Example flow:**
```sql
-- User: "Show all accused persons in FIR KSP/2023/0042"
SELECT p.person_id, p.first_name, p.last_name, p.gender, p.occupation
FROM FIR f
JOIN CrimeIncident ci ON ci.fir_id = f.fir_id
JOIN CrimeParticipant cp ON cp.incident_id = ci.incident_id
JOIN Person p ON p.person_id = cp.person_id
WHERE f.fir_number = 'KSP/2023/0042' AND cp.role = 'Accused';
```

The agent answers from the returned rows and includes the SQL used.

### The Graph Agent

**When it's called:** Any query asking to build, show, or visualize a network around a named person.

**How it works:** The Graph Agent extracts the person name, calls `create_network_centered_around_person()`, then calls `save_person_network_html()`. If multiple people match the same name, the tool may create one graph per matched person. Each graph is saved as an HTML file.

**What the graph contains:**
- the matched person as the center node
- incidents/FIRs connected to that person
- co-accused links
- organization/gang membership
- vehicles linked to the person
- phones linked to the person
- bank accounts linked to the person
- transaction links between connected accounts

**Example flow:**
```text
Query:  "Show the criminal network for Ravi Kumar"
Step 1: Extract "Ravi Kumar"
Step 2: Build one or more NetworkX graphs for matching persons
Step 3: Save Pyvis HTML files under the graph artifacts folder
Result: The WebSocket response includes `graph_html_paths`.
```

### The Analytics Agent

**When it's called:** Any query about patterns, trends, volumes, comparisons, or hotspots. Anything that needs aggregation across multiple records rather than retrieval of specific ones.

**How it works:** The Analytics Agent chooses one deterministic analytics tool, interprets the rows, and returns a structured response with `analysis_type`, `answer`, `chart`, `map`, and `table` fields. The router stores these outputs in session state so the WebSocket response can return them as artifacts.

**What it computes:**
- crime counts by district
- monthly crime trends
- crime type breakdown
- crime category breakdown
- crime hotspots with latitude/longitude
- top repeat offenders

**Example flow:**
```text
Query:     "Which districts have the highest crime rates?"
Tool:      crime_count_by_district()
Result:    Short insight + table rows
Artifact:  Bar chart data in `chart_data`
```

### The Summary Agent

**When it's called:** Any query asking for a case summary, an investigation report, or a narrative timeline for a specific FIR.

**How it works:** The Summary Agent calls `build_fir_context(fir_number)` to fetch the FIR overview, incidents, participants, investigation information, timeline events, and evidence. It then generates a professional FIR summary report and must call `save_summary_report_pdf(report_text)` after the report is generated.

**Output format:**
```text
1. Case Overview
2. Incident Details
3. Persons Involved
4. Investigation Status
5. Timeline Of Events
6. Evidence Summary
7. Key Observations
8. Recommended Next Steps
```

The same generated report text is passed to ReportLab, and the WebSocket response includes `summary_report_pdf_path`.

---

## 8. Implementation Plan

This is the implemented build sequence. Each phase produces something testable before the next phase begins.

```text
Phase 0 - Database
     |
     v
Phase 1 - Synthetic Data
     |
     v
Phase 2 - Multi-Agent Backend
     |
     v
Phase 3 - WebSocket Assistant Layer
     |
     v
Phase 4 - Frontend
```

### Phase 0 - Database

**Goal:** SQLite database with all 26 tables created and foreign keys working.

Tasks:
- Write `database/schema.sql` with all table definitions in FK-safe order.
- Write `backend/database.py` with a SQLite connection helper using `sqlite3.Row`.
- Create the SQLite database file at `database/ksp_crime_platform.db`.
- Run the schema initializer.
- Verify all 26 tables exist.

Done when: `database/ksp_crime_platform.db` exists and SQLite lists all expected tables.

### Phase 1 - Synthetic Data

**Goal:** Populate the crime world with connected data and useful demo patterns.

Tasks:
- Write `seed_data.py` with individual seed functions for the schema tables.
- Add `seed_all()` to execute the seed functions in dependency-safe order.
- Verify the Bengaluru North Gang exists.
- Verify repeat offenders, hotspot districts, linked phones/vehicles/accounts, and financial transactions.
- Confirm the database is populated through December 2023.

Done when: the seeded database supports record lookups, graph networks, analytics, and FIR summaries.

### Phase 2 - Multi-Agent Backend

**Goal:** Cluvo can delegate user requests to the correct specialist agent.

Tasks:
- Build `backend/orchestrator/context.py` for shared session state.
- Build `backend/orchestrator/router.py` with `InvestigationTeam` using Agno `Team` in coordinate mode.
- Build prompt files under `backend/orchestrator/prompts/`.
- Build the General Agent for fallback, greetings, and clarification.
- Build the Text2SQL Agent with table catalog/schema tools and safe SQL execution.
- Build the Graph Agent with NetworkX + Pyvis person-centered graph generation.
- Build the Analytics Agent with fixed analytics tools and structured chart/map/table output.
- Build the Summary Agent with FIR context generation and PDF saving.
- Test each agent path independently.

Done when: each current agent works through `InvestigationTeam.team_run()`.

### Phase 3 - WebSocket Assistant Layer

**Goal:** One assistant-style conversation endpoint instead of separate HTTP endpoints.

Tasks:
- Create root `main.py` with `FastAPI(title="Cluvo")`.
- Create a single WebSocket route: `/ws/chat`.
- Accept JSON messages containing `user_id`, `session_id`, and `message`.
- Initialize each `(user_id, session_id)` once at session start.
- Call `team.team_run()` from the WebSocket handler using `asyncio.to_thread()`.
- Return assistant text plus artifacts from session state.

Expected incoming payload:

```json
{
  "user_id": "user-001",
  "session_id": "session-001",
  "message": "Summarize FIR KSP/2023/0042"
}
```

Expected outgoing payload:

```json
{
  "type": "assistant_message",
  "message": "...",
  "artifacts": {
    "graph_html_paths": [],
    "summary_report_pdf_path": "reports/KSP_2023_0042_summary_report.pdf",
    "chart_data": null,
    "map_data": null,
    "table_data": []
  }
}
```

Done when: a WebSocket test client can successfully exercise General, Text2SQL, Graph, Analytics, and Summary requests.

### Phase 4 - Frontend

**Goal:** React UI that feels like a single assistant, while rendering artifacts when Cluvo returns them.

Tasks:
- Build a chat screen connected to `ws://127.0.0.1:8000/ws/chat`.
- Generate or persist a `user_id` and `session_id` on the frontend.
- Render status messages such as `Cluvo is thinking...`.
- Render normal assistant messages.
- Render PDF links from `summary_report_pdf_path`.
- Render graph links or embeds from `graph_html_paths`.
- Render analytics charts from `chart_data`.
- Render hotspot maps from `map_data`.
- Render result tables from `table_data`.

Done when: the full demo can be run from the frontend without directly using the terminal test client.

---

## 9. Folder Structure

```text
Intelligent_Conversational_Assistant_KSP/
|
|-- main.py                         # FastAPI app with /ws/chat WebSocket
|-- requirements.txt
|
|-- backend/
|   |-- database.py                 # SQLite connection, init_db(), memory db
|   |
|   |-- orchestrator/
|       |-- context.py              # Shared session-state dataclass
|       |-- router.py               # Cluvo InvestigationTeam / Agno Team
|       |-- llm.py                  # Model configuration
|       |
|       |-- agents/
|       |   |-- general_agent.py    # General fallback agent
|       |   |-- sql_agent.py        # Text2SQL tools and agent
|       |   |-- graph_agent.py      # NetworkX/Pyvis graph tools and agent
|       |   |-- analytics_agent.py  # Analytics tools and response models
|       |   |-- summary_agent.py    # FIR summary + PDF tools and agent
|       |
|       |-- prompts/
|           |-- router_prompt.py
|           |-- general_agent_prompt.py
|           |-- text_to_sql_agent.py
|           |-- graph_agent_prompt.py
|           |-- analytics_agent_prompt.py
|           |-- summary_agent_prompt.py
|
|-- database/
|   |-- schema.sql                  # All 26 table definitions
|   |-- ksp_crime_platform.db       # SQLite database file
|   |-- seed_data.py                # Synthetic crime-world seeding
|
|-- AgentDocs/
|   |-- Text2SQL/
|       |-- table_catalog.md        # Table descriptions and relationships
|       |-- table_schemas.md        # Pull-by-name schema sections
|
|-- ReferenceDocs/
|   |-- KSP_Crime_Platform_Implementation_Guide.md
|   |-- table_schemas.md
|
|-- graph_artifacts/                # Generated Pyvis graph HTML files
|-- reports/                        # Generated FIR summary PDFs
|
|-- frontend/                       # React UI, built after backend validation
```

### What Goes Where

- `main.py` is intentionally thin. It owns the WebSocket route, session initialization call, and response packaging.
- `backend/orchestrator/router.py` owns Cluvo's multi-agent team and session-state updates.
- Business logic lives in agent tools, not in the WebSocket handler.
- Text2SQL documentation lives in `AgentDocs/Text2SQL/` so the SQL agent can pull catalog and schema context selectively.
- Graph HTML output goes to `graph_artifacts/`.
- FIR summary PDFs go to `reports/`.
- Similar-case semantic-search files are not part of the current implementation; they belong to future scope.

---

## 10. Development Roadmap

### Completed Backend Foundation

The backend foundation is complete when Cluvo can receive a message, route it to the correct specialist, execute the required tool chain, and return a WebSocket response with any generated artifacts.

| Area | Status |
|---|---|
| SQLite schema and `.db` file | Complete |
| Synthetic data seeding | Complete |
| Text2SQL Agent | Complete and tested |
| Graph Agent | Complete and tested |
| Analytics Agent | Complete and tested |
| Summary Agent with PDF saving | Complete and tested |
| General Agent | Complete and tested |
| Cluvo router/team leader | Complete and tested |
| WebSocket `/ws/chat` | Complete and tested |

### Backend Test Sequence

Use a WebSocket client to send one request per path:

```text
1. "Hi"                                             -> General Agent
2. "Who are the accused in FIR KSP/2023/0042?"     -> Text2SQL Agent
3. "Build a network around Ravi Kumar"             -> Graph Agent
4. "Show monthly crime trends"                     -> Analytics Agent
5. "Generate a case report for FIR KSP/2023/0042"  -> Summary Agent + PDF
```

Done when: each request returns a correct assistant message and expected artifacts in the WebSocket response.

### Frontend Build Roadmap

The next phase is the frontend assistant experience.

| Step | Task |
|---|---|
| 1 | Create the React app shell and main chat layout |
| 2 | Generate/persist frontend `user_id` and `session_id` |
| 3 | Connect to `ws://127.0.0.1:8000/ws/chat` |
| 4 | Render user messages, assistant messages, and status messages |
| 5 | Render PDF report links from `summary_report_pdf_path` |
| 6 | Render graph HTML links or iframe embeds from `graph_html_paths` |
| 7 | Render analytics charts from `chart_data` |
| 8 | Render map markers from `map_data` |
| 9 | Render analytics/result tables from `table_data` |
| 10 | Polish the demo flow and handle loading/error states |

### Demo Query Sequence

```text
1. "Hi Cluvo"
2. "Who are the accused in FIR KSP/2023/0042?"
3. "Build a network around Ravi Kumar"
4. "Which district has the highest crime count?"
5. "Show monthly crime trends"
6. "Generate a case report for FIR KSP/2023/0042"
```

---

## 11. Future Scope

### If This Prototype Became Production

The prototype proves the concept. A production system built on this foundation would add:

**Live data integration**
Replace the synthetic data with a live connection to KSP's FIR management system. Every new FIR filed would be ingested automatically and made available for querying within minutes. The schema is already designed to match real FIR structure — this is an integration problem, not a redesign problem.

**Real-time graph updates**
The NetworkX graph is rebuilt on demand for the prototype. In production, a persistent graph database (Neo4j or Amazon Neptune) would maintain the criminal network incrementally, with edges added as new case connections are established.

**Fine-tuned language models**
GPT-4o mini handles Kannada reasonably well for a prototype. A production system would fine-tune a model on Karnataka-specific legal vocabulary, IPC sections, and regional crime terminology to improve accuracy significantly.

**Multi-modal inputs**
CCTV footage analysis, vehicle registration plate recognition, and facial recognition for matching suspects to existing Person records. These are separate ML pipelines that feed into the same database — the Person and Vehicle tables are already structured to receive this data.

**Predictive models**
The analytics agent currently reports what has happened. A production system would add dedicated ML models — trained on historical incident data — to forecast where crimes are likely to occur, which offenders are likely to reoffend, and which areas need increased patrol density.

**Audit and accountability infrastructure**
Every query an officer runs, every record they access, every report they generate would be logged with timestamp, officer ID, and query content. This creates a chain of custody for information access that is essential in a law enforcement context.

### What We Are Deliberately Not Including in the Prototype

The following are real production concerns that add no demonstrable value to a hackathon prototype and would consume time better spent making the core system impressive:

- Docker and container orchestration
- Kubernetes or any auto-scaling infrastructure
- CI/CD pipelines
- Redis caching layers
- Message queues (RabbitMQ, Kafka)
- Microservice decomposition
- Load balancing

A hackathon prototype should be runnable with `uvicorn main:app` and `npm run dev`. Anything that requires an ops team to deploy is scope creep that makes the demo harder and impresses no one.

---

*This document is the single source of truth for the prototype build. Update it as decisions change. The code should match what is written here.*
