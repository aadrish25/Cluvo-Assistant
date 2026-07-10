# Cluvo - KSP Crime Intelligence Assistant

Cluvo is a conversational crime intelligence prototype for the KSP Datathon 2026.
It lets users ask natural-language questions over a synthetic crime database and
routes each request to the right specialist agent.

## What Cluvo Can Do

- Answer FIR, case, person, officer, evidence, vehicle, phone, bank account, and
  transaction lookup questions.
- Generate safe SQL-backed answers from natural language.
- Build person-centered criminal network graphs.
- Produce crime analytics such as district counts, monthly trends, hotspots,
  category breakdowns, and repeat-offender rankings.
- Generate FIR summary reports and save them as PDFs.
- Handle greetings, help requests, and ambiguous questions through a general
  fallback agent.

## Project Structure

```text
.
├── main.py                         # FastAPI WebSocket app
├── backend/
│   ├── database.py                 # SQLite helpers
│   └── orchestrator/
│       ├── router.py               # Cluvo multi-agent team
│       ├── context.py              # Shared session state
│       ├── agents/                 # General, SQL, graph, analytics, summary agents
│       └── prompts/                # System prompts
├── database/
│   ├── schema.sql                  # Database schema
│   └── seed_data.py                # Synthetic data seeding
├── AgentDocs/Text2SQL/             # SQL agent catalog and schemas
├── ReferenceDocs/                  # Implementation docs
├── graph_artifacts/                # Generated graph HTML files
└── reports/                        # Generated PDF reports
```

The frontend is currently built separately at:

```text
D:\Cluvo_frontend\index.html
```

## Requirements

- Python 3.10+
- SQLite
- A configured LLM provider/model in `backend/orchestrator/llm.py`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Database Setup

Create the SQLite database from the schema:

```bash
python -c "from backend.database import init_db; init_db()"
```

Then run your seed script:

```bash
python database/seed_data.py
```

The expected database file is:

```text
database/ksp_crime_platform.db
```

## Run The Backend

From the project root:

```bash
uvicorn main:app --reload
```

The assistant WebSocket is available at:

```text
ws://127.0.0.1:8000/ws/chat
```

Generated artifacts are served from:

```text
http://127.0.0.1:8000/reports/...
http://127.0.0.1:8000/graph_artifacts/...
```

## Run The Frontend

Start the backend first, then open:

```text
D:\Cluvo_frontend\index.html
```

The frontend sends messages to the WebSocket using:

```json
{
  "user_id": "user-001",
  "session_id": "session-001",
  "message": "Who are the accused in FIR KSP/2023/0042?"
}
```

## Demo Questions

Try these after the backend is running:

```text
Hi Cluvo
Who are the accused in FIR KSP/2023/0042?
Build a network around Ravi Kumar
Which district has the highest crime count?
Show monthly crime trends
Show crime hotspots in Karnataka
Generate a case report for FIR KSP/2023/0042
```

## Notes

- The database contains synthetic demo data through December 2023.
- The `.db` file, generated reports, generated graphs, virtual environments,
  and local secrets are ignored by Git.
- Similar-case semantic search is future scope and is not part of the current
  implementation.
