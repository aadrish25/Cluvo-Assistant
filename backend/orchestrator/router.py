from agno.team import Team,TeamMode
from agno.run.team import RunCompletedEvent,RunContentEvent,ToolCallStartedEvent,RunErrorEvent
from agno.db.sqlite import SqliteDb
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.llm import gemma4_31b
from backend.orchestrator.prompts.router_prompt import ROUTER_AGENT_SYSTEM_PROMPT
from backend.orchestrator.context import Context
from backend.orchestrator.agents.sql_agent import create_sql_agent
from backend.orchestrator.agents.graph_agent import create_graph_agent
from backend.orchestrator.agents.analytics_agent import create_analytics_agent,AnalyticsResponse
from backend.orchestrator.agents.summary_agent import create_summary_agent
from backend.orchestrator.agents.general_agent import create_general_agent
from dataclasses import asdict
from backend.database import memory_db


class InvestigationTeam:
    def __init__(self):
        self.sql_agent = create_sql_agent()
        self.graph_agent = create_graph_agent()
        self.analytics_agent = create_analytics_agent()
        self.summary_agent = create_summary_agent()
        self.general_agent = create_general_agent()
        self.sqlite_db = memory_db
        
        
        self._agent_status_labels = {
            "text-to-sql-agent": "Querying the case database",
            "graph-agent": "Mapping out the network",          # verify
            "analytics-agent": "Crunching the numbers",         # verify
            "summary-agent": "Putting together a summary",      # verify
            "general-agent": "Thinking it through",             # verify
        }

        self._delegate_tool_names = {
            "delegate_task_to_member",
            "transfer_task_to_member",
            "forward_task_to_member",
        }
        
        self.team = Team(
                model = gemma4_31b,
                name = "Crime Investigation Team",
                description = "A team of specialized agents for the KSP Crime Intelligence Platform.",
                system_message = ROUTER_AGENT_SYSTEM_PROMPT,
                mode = TeamMode.coordinate,
                members = [self.sql_agent,self.graph_agent,self.analytics_agent,self.summary_agent,self.general_agent],
                session_state=asdict(Context()),
                add_session_state_to_context=True,
                update_memory_on_run=True,
                enable_agentic_memory=True,
                enable_agentic_state=True,
                add_history_to_context=True,
                num_history_runs=4,
                db=self.sqlite_db,
                telemetry=True,
                debug_mode=True,
            )
            
    
    def initialize_session(self,user_id:str,session_id:str):
        try:
            initial_context = asdict(Context(user_id=user_id,session_id=session_id))
            self.team.update_session_state(
                session_state_updates=initial_context,
                session_id=session_id
            )
            
            return self.team.get_session_state(session_id=session_id)
        
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Error in initializing session: {e}")
            
    
    def team_run(self,input:str,user_id:str,session_id:str):
        try:
            
            response = self.team.run(
                input=input,
                user_id=user_id,
                session_id=session_id
            )
            
            # update the session state, if analytics response
            for member_response in response.member_responses:
                print(f"[INVESTIGATOR TEAM] Agent name: {member_response.agent_name}, Response type : {type(member_response.content)}")
                if member_response.agent_name == "Analytics Agent":
                    analytics_output : AnalyticsResponse = member_response.content
                    
                    self.team.update_session_state(
                        session_state_updates={
                            "analysis_type":analytics_output.analysis_type,
                            "analytics_answer":analytics_output.answer,
                            "chart_data":analytics_output.chart.model_dump_json() if analytics_output.chart is not None else None,
                            "map_data":analytics_output.map.model_dump_json() if analytics_output.map is not None else None,
                            "table_data":analytics_output.table,
                        },
                        session_id=session_id
                    )
                    
                # after updating the session state, add the updated session state in the response object as well
                response.session_state = self.team.get_session_state(session_id=session_id)
            
            return response
        
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Error in generating response: {e}")
            
            
    async def team_run_stream(self,input:str,user_id:str,session_id:str):
        try:
            stream = self.team.arun(
                input=input,
                user_id=user_id,
                session_id=session_id,
                stream=True,
                stream_events=True,
            )
            
            final_response = None
            
            async for event in stream:
                if isinstance(event,RunContentEvent):
                    if event.content:
                        yield {"type":"stream_chunk","content":event.content}
                elif isinstance(event,ToolCallStartedEvent):
                    tool_name = getattr(event.tool,"tool_name","") or ""
                    tool_args = getattr(event.tool,"tool_args",{}) or {}
                    
                    if tool_name in self._delegate_tool_names:
                        member_id = tool_args.get("member_id")
                        task = tool_args.get("task")
                        label = self._agent_status_labels.get(member_id,member_id or "a specialist agent")
                        message = f"{label} — {task}" if task else f"{label}..."
                        yield {"type":"status","message":message}
                    else:
                        yield {
                        "type":"status",
                        "message": f"Running {tool_name or 'a tool'}...",
                        }
                elif isinstance(event, RunErrorEvent):
                    yield {"type": "error", "message": str(getattr(event, "error", "Something went wrong."))}
                elif isinstance(event,RunCompletedEvent):
                    final_response = event
                    
            if final_response is None:
                return
            
            
            for member_response in getattr(final_response, "member_responses", []) or []:
                if member_response.agent_name == "Analytics Agent":
                    analytics_output: AnalyticsResponse = member_response.content
                    self.team.update_session_state(
                        session_state_updates={
                            "analysis_type": analytics_output.analysis_type,
                            "analytics_answer": analytics_output.answer,
                            "chart_data": analytics_output.chart.model_dump_json() if analytics_output.chart else None,
                            "map_data": analytics_output.map.model_dump_json() if analytics_output.map else None,
                            "table_data": analytics_output.table,
                        },
                        session_id=session_id,
                    )
            session_state = self.team.get_session_state(session_id=session_id)
            yield {
                "type": "assistant_message",
                "message": final_response.content,
                "session_state": session_state,
            }
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Exception in streaming agent output: {e}")
            
            

if __name__ == "__main__":
    team_obj = InvestigationTeam()
    
    user_id = "test-007"
    session_id = "team-test-001"
    while True:
        user_msg = input("User: ")
        
        if user_msg.strip() in ["bye","exit","quit"]:
            break
        
        response = team_obj.team_run(
            input=user_msg,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"Cluvo: {response.content}")
        print(f"Session state after current run: {response.session_state}")
        
