from agno.agent import Agent
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.prompts.general_agent_prompt import GENERAL_AGENT_SYSTEM_PROMPT
from agno.tools.reasoning import ReasoningTools
from backend.config import DEBUG_MODE
from backend.orchestrator.llm import gemma4_31b
from backend.database import memory_db


# create the general agent
def create_general_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "General Agent",
          id="general-agent",
          description = "An agent that handles general conversation,exchanges greetings and solves any ambiguity for the user.",
          system_message = GENERAL_AGENT_SYSTEM_PROMPT,
          tools=[ReasoningTools(add_instructions=True)],
          db=memory_db,
          add_history_to_context=True,
          num_history_runs=10,
        #   add_session_state_to_context=True,
          telemetry=DEBUG_MODE,
          debug_mode = DEBUG_MODE
        )
    except Exception as e:
        print(f"[GENERAL AGENT] Exception in creating agent: {e}")