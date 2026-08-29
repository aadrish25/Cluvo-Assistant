import sys
from pathlib import Path
from agno.agent import Agent
from agno.tools.reasoning import ReasoningTools

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.prompts.analytics_agent_prompt import ANALYTICS_AGENT_SYSTEM_PROMPT
from backend.agno_tools.analytical_tools import (crime_count_by_district,crime_category_breakdown,
                                                 crime_hotspots,crime_type_breakdown,
                                                 monthly_crime_trend,top_repeat_offenders)
from backend.config import DEBUG_MODE
from backend.database import memory_db
from backend.orchestrator.llm import gemma4_31b
from backend.agent_schema.analytics_agent_schema import AnalyticsResponse



# define the analytics agent finally
def create_analytics_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Analytics Agent",
          id="analytics-agent",
          description = "Computes crime trends, rankings, breakdowns, and hotspot analytics from the KSP crime database.",
          system_message = ANALYTICS_AGENT_SYSTEM_PROMPT,
          tools = [
              crime_count_by_district,
              monthly_crime_trend,
              crime_type_breakdown,
              crime_category_breakdown,
              crime_hotspots,
              top_repeat_offenders,
              ReasoningTools(add_instructions=True),
          ],
          output_schema=AnalyticsResponse,
          db=memory_db,
          add_history_to_context=True,
          num_history_runs=10,
        #   add_session_state_to_context=True,
          telemetry=DEBUG_MODE,
          debug_mode = DEBUG_MODE
        )
    except Exception as e:
        print(f"[ANALYTICS AGENT] Error in creating analytics agent: {e}")
        
if __name__ == "__main__":
    agent = create_analytics_agent()
    
    response = agent.run("What are the top districts in terms of crime count?")
    print(response.content)
    
    
