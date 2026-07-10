from agno.agent import Agent
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.prompts.general_agent_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from backend.orchestrator.llm import gemma4_31b
from backend.database import memory_db


# create the general agent
def create_general_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "General Agent",
          description = "An agent that handles general conversation,exchanges greetings and solves any ambiguity for the user.",
          system_message = GENERAL_AGENT_SYSTEM_PROMPT,
          reasoning = True,
          db=memory_db,
          reasoning_min_steps = 3,
          reasoning_max_steps = 7,
          add_history_to_context=False,
          add_session_state_to_context=True,
          telemetry=True,
          debug_mode = True
        )
    except Exception as e:
        print(f"[GENERAL AGENT] Exception in creating agent: {e}")