from agno.agent import Agent
from agno.run import RunContext
from pathlib import Path
import sqlite3
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# print(f"[SQL AGENT] BASE_DIR: {BASE_DIR}")

from backend.config import SQL_AGENT_DOC_DIR,DEBUG_MODE
from agno.tools.reasoning import ReasoningTools
from backend.orchestrator.llm import gemma4_31b
from backend.database import create_connection
from backend.orchestrator.prompts.text_to_sql_agent import TEXT_TO_SQL_AGENT_SYSTEM_PROMPT
from backend.database import memory_db

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
    
    
# tool to read table schema
def get_table_schema(table_name:str):
    """
    Return the exact SQL schema section for one table.

    Args:
        table_name (str): Exact markdown heading/table name to retrieve, such as
        "FIR", "CrimeIncident", "Person", or "Case".

    Returns:
        str: The matching markdown section containing the table's CREATE TABLE
        statement, or an empty string if the table name is not found.
    """
    try:
        table_schema_path = SQL_AGENT_DOC_DIR / "table_schemas.md"
        
        with open(table_schema_path,"r",encoding="utf-8") as f:
            table_schemas = f.read()
            
        pattern = rf"^## {re.escape(table_name)}\n(.*?)(?=^## |\Z)"
        match = re.search(pattern,table_schemas,re.DOTALL | re.MULTILINE)
        
        if not match:
            raise ValueError(f"[SQL AGENT]Schema not found for table: {table_name}")
        
        return match.group(0).strip()
    
    except Exception as e:
        print(f"[SQL AGENT]Error reading table schema for {table_name}: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }
    
    
# generate table schemas
def get_table_schemas(table_names:list):
    """
    Return exact SQL schema sections for multiple selected tables.

    Args:
        table_names (list): Exact table names to retrieve, for example
        ["FIR", "CrimeIncident", "CrimeParticipant", "Person"].

    Returns:
        str: Matching schema sections joined together. Use this after selecting
        relevant tables from the catalog and before generating SQL.
    """
    try:
        table_schemas = []
        for table_name in table_names:
            schema = get_table_schema(table_name)
            if schema:
                table_schemas.append(schema)
        return "\n\n".join(table_schemas)
    
    except Exception as e:
        print(f"[SQL AGENT]Error reading table schemas: {e}")
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
        
        return [dict(row) for row in results]
    except Exception as e:
        print(f"[SQL AGENT]Error executing SQL query: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }



# create the SQL Agent finally
def create_sql_agent()->Agent:
    try:
        return Agent(
          model = gemma4_31b,
          name = "Text to SQL Agent",
          description = "An agent that converts natural language questions into SQL queries for the KSP Crime Database.",
          system_message = TEXT_TO_SQL_AGENT_SYSTEM_PROMPT,
          tools = [
              read_table_catalog,
              get_table_schemas,
              execute_sql_query,
              ReasoningTools(add_instructions=True),
          ],
          db=memory_db,
          add_history_to_context=False,
          add_session_state_to_context=True,
          telemetry=DEBUG_MODE,
          debug_mode = DEBUG_MODE,
        )
        
    except Exception as e:
        print(f"[SQL AGENT] Error creating SQL Agent: {e}")
        return None
    
    
def test_sql_agent(query:str,user_id:str):
    try:
        sql_agent = create_sql_agent()
        if sql_agent is None:
            print(f"[SQL AGENT] Failed to create SQL Agent.")
            return None
        
        response = sql_agent.print_response(input=query,show_full_reasoning=True,user_id=user_id)
        return response
    
    except Exception as e:
        print(f"[SQL AGENT] Error testing SQL Agent: {e}")
        return None
    
    
if __name__ == "__main__":
    test_query = "Which accused persons have active phone numbers?"
    test_user_id = "test_user_001"
    test_response = test_sql_agent(query=test_query,user_id=test_user_id)
        
