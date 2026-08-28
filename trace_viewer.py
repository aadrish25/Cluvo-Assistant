# trace_viewer.py — run separately, only when you want to look at traces
from agno.os import AgentOS
from backend.config import TRACES_DB
from agno.db.sqlite import SqliteDb

traces_db = SqliteDb(db_file=TRACES_DB)
agent_os = AgentOS(tracing=True, db=traces_db)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="trace_viewer:app",port=7777)