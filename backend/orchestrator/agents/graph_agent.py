from agno.agent import Agent

from agno.tools.reasoning import ReasoningTools
from pathlib import Path
import re
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))


from backend.orchestrator.prompts.graph_agent_prompt import GRAPH_AGENT_SYSTEM_PROMPT
from backend.config import DEBUG_MODE
from backend.orchestrator.llm import gemma4_31b
from backend.database import memory_db
from backend.agno_tools.graph_tools import find_matching_person,create_network_centered_around_person

        
# create the graph agent
def create_graph_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Graph Agent",
          description = "An agent that builds and saves relationship graphs, for a person on the KSP Crime Database.",
          system_message = GRAPH_AGENT_SYSTEM_PROMPT,
          tools = [
              find_matching_person,
              create_network_centered_around_person,
              ReasoningTools(add_instructions=True)
          ],
          db=memory_db,
          add_history_to_context=True,
          num_history_runs=10,
          add_session_state_to_context=True,
          telemetry=DEBUG_MODE,
          debug_mode = DEBUG_MODE
        )
    except Exception as e:
        print(f"[GRAPH AGENT] Error in creating graph agent: {e}")
        
if __name__ == "__main__":
    graph_list = create_network_centered_around_person(person_name="Deepa Gowda")
    
