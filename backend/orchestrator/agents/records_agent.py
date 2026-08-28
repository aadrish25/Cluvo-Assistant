from agno.agent import Agent
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
# print(PROJECT_ROOT)
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.prompts.records_agent_prompt import RECORDS_AGENT_SYSTEM_PROMPT
from agno.tools.reasoning import ReasoningTools
from backend.config import DEBUG_MODE
from backend.orchestrator.llm import gemma4_31b
from backend.database import memory_db
from backend.agno_tools.knowledge_base import search_fir_knowledge



def create_records_agent():
    try:
        return Agent(
            model = gemma4_31b,
            name = "Records Agent",
            description = "Answers questions from uploaded FIR report documents by retrieving relevant text directly from the case files.",
            system_message = RECORDS_AGENT_SYSTEM_PROMPT,
            tools=[search_fir_knowledge,ReasoningTools(add_instructions=True)],
            # post_hooks=[add_citations],
            db=memory_db,
            add_history_to_context=True,
            num_history_runs=10,
            add_session_state_to_context=True,
            telemetry=DEBUG_MODE,
            debug_mode = True,
        )
    except Exception as e:
        print(f"[RAG AGENT] Exception in creating agent: {e}")
        
        
if __name__ == "__main__":
    agent = create_records_agent()
    agent.print_response(
        "What happened in the kidnapping incident? FIR number is KSP/2023/0015.",
        markdown=True,
    )