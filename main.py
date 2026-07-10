import asyncio
from pathlib import Path
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from backend.orchestrator.router import InvestigationTeam

Path("reports").mkdir(parents=True,exist_ok=True)
Path("graph_artifacts").mkdir(parents=True,exist_ok=True)

# create the fast api app - Cluvo
app = FastAPI(title="Cluvo")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/graph_artifacts", StaticFiles(directory="graph_artifacts"), name="graph_artifacts")

team = InvestigationTeam()
initialized_sessions = set()


def initialize_chat_session(user_id:str,session_id:str):
    try:
        session_key = (user_id,session_id)
        
        if session_key in initialized_sessions:
            return
        
        team.initialize_session(
            user_id=user_id,
            session_id=session_id
        )
        initialized_sessions.add(session_key)
        
    except Exception as e:
        print(f"[MAIN] Exception in initializing chat session: {e}")


def build_ws_response(response):
    try:
        session_state = response.session_state or {}
        
        return {
            "type":"assistant_message",
            "message":response.content,
            "artifacts":{
                "graph_html_paths":session_state.get("graph_html_paths") or [],
                "summary_report_pdf_path":session_state.get("summary_report_pdf_path"),
                "chart_data":session_state.get("chart_data"),
                "map_data":session_state.get("map_data"),
                "table_data":session_state.get("table_data") or [],
            },
        }
    except Exception as e:
        print(f"[MAIN] Exception in building ws response: {e}")
        
        
        
@app.websocket("/ws/chat")
async def chat_websocket(websocket:WebSocket):
    await websocket.accept()
    
    try:
        while True:
            payload = await websocket.receive_json()
            
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            message = payload.get("message")

            if not user_id or not session_id or not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "user_id, session_id, and message are required.",
                })
                continue
            
            initialize_chat_session(
                user_id=user_id,
                session_id=session_id
            )
            
            await websocket.send_json({
                "type":"status",
                "message":"Cluvo is thinking...",
            })
            
            response = await asyncio.to_thread(
                team.team_run,
                message,
                user_id,
                session_id,
            )
            
            await websocket.send_json(build_ws_response(response))
            
    except WebSocketDisconnect:
        print(f"[MAIN] Client disconnected!")
    except Exception as e:
        print(f"[MAIN] Error in websocket connection: {e}")
        
        
        


