from agno.agent import Agent
from agno.tools.reasoning import ReasoningTools
import re
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))


from backend.orchestrator.llm import gemma4_31b
from backend.orchestrator.prompts.summary_agent_prompt import SUMMARY_AGENT_SYSTEM_PROMPT
from backend.config import DEBUG_MODE
from backend.database import memory_db
from backend.agno_tools.summary_tools import build_fir_context,save_summary_report_pdf





# create the FIR summary agent
def create_summary_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Summary Agent",
          description = "An agent that summarizes and generates a report for a FIR on the KSP Crime Database.",
          system_message = SUMMARY_AGENT_SYSTEM_PROMPT,
          tools = [
              build_fir_context,
              save_summary_report_pdf,
              ReasoningTools(add_instructions=True),
          ],
          db=memory_db,
          add_history_to_context=True,
          num_history_runs=10,
          add_session_state_to_context=True,
          telemetry=DEBUG_MODE,
          debug_mode = DEBUG_MODE
        )
    except Exception as e:
        print(f"[SUMMARY AGENT] Error in creating summary agent: {e}")
        
if __name__ == "__main__":
    agent = create_summary_agent()
    
    agent.print_response("Generate me a summary for fir number KSP/2023/0040")
