from agno.agent import Agent

from pathlib import Path
import sqlite3
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# print(f"[SQL AGENT] BASE_DIR: {BASE_DIR}")

from backend.config import SCHEMA_SKILLS_DIR,DEBUG_MODE
from agno.tools.reasoning import ReasoningTools
from agno.skills import Skills,LocalSkills
from backend.orchestrator.llm import gemma4_31b
from backend.orchestrator.prompts.text_to_sql_agent import TEXT_TO_SQL_AGENT_SYSTEM_PROMPT
from backend.database import memory_db
from backend.agno_tools.sql_tools import read_table_catalog,execute_sql_query





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
              execute_sql_query,
              ReasoningTools(add_instructions=True),
          ],
          skills=Skills(loaders=[LocalSkills(path=str(SCHEMA_SKILLS_DIR))]),
          db=memory_db,
          add_history_to_context=True,
          num_history_runs=10,
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
        
