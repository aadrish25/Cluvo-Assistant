from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

from agno.run import RunContext
from backend.config import SQL_AGENT_DOC_DIR
from backend.database import create_connection
import re


# tool to read the table catalog
def read_table_catalog():
    """
    Return the Text2SQL table catalog as markdown.

    Args:
        None.

    Returns:
        str: Table descriptions, usage guidance, and relationship paths. Use this
        first to decide which tables are relevant before requesting exact schemas.
    """
    try:
        table_catalog_path = SQL_AGENT_DOC_DIR / "table_catalog.md"
        with open(table_catalog_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[SQL AGENT]Error reading table catalog: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }
    
    
    

# execute sql query
def execute_sql_query(run_context:RunContext,query:str):
    """
    Execute a read-only SQLite query against the crime database.

    Args:
        query (str): A complete SQLite SELECT statement, optionally starting
        with a read-only WITH/CTE clause. Do not pass INSERT, UPDATE, DELETE,
        DROP, ALTER, PRAGMA, or multiple statements.

    Returns:
        list: Query result rows as tuples. Returns an empty list if validation
        fails, execution fails, or the query has no matching rows.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        cleaned_query = query.strip().rstrip(";").strip()
        query_lower = cleaned_query.lower()

        if ";" in cleaned_query:
            raise ValueError("[SQL AGENT]Only one SQL statement is allowed.")

        if not (query_lower.startswith("select") or query_lower.startswith("with")):
            raise ValueError("[SQL AGENT]Only SELECT or read-only WITH queries are allowed.")

        blocked_keywords = [
            "insert", "update", "delete", "drop", "alter", "create", "replace",
            "truncate", "attach", "detach", "vacuum", "pragma",
        ]
        blocked_pattern = r"\b(" + "|".join(blocked_keywords) + r")\b"
        if re.search(blocked_pattern, query_lower):
            raise ValueError("[SQL AGENT]Write or schema-changing SQL is not allowed.")
        
        cursor.execute(cleaned_query)
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        conn.close()
        
        # writing entity ids into the context
        if run_context.session_state is None:
            run_context.session_state = {}
            
        id_column_map = {
            "person_id": "person_ids", "case_id": "case_ids",
            "fir_id": "fir_ids", "incident_id": "incident_ids",
            "account_id": "account_ids", "vehicle_id": "vehicle_ids",
            "location_id": "location_ids", "organization_id": "organization_ids",
        }
        
        for col_name,state_key in id_column_map.items():
            if col_name in column_names:
                idx = column_names.index(col_name)
                run_context.session_state[state_key] = [row[idx] for row in results]
                
        run_context.session_state["last_sql_query"] = cleaned_query
        print(f"[SQL AGENT] Session state: {run_context.session_state}\n")
        return [dict(row) for row in results]
    except Exception as e:
        print(f"[SQL AGENT]Error executing SQL query: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }