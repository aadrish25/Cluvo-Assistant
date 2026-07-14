import base64
from pathlib import Path
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from backend.orchestrator.router import InvestigationTeam
from fastapi.middleware.cors import CORSMiddleware
from backend.config import REPORTS_DIR,GRAPH_DIR,LISTEN_PORT
import uvicorn

# create the fast api app - Cluvo
app = FastAPI(title="Cluvo")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/graph_artifacts", StaticFiles(directory=str(GRAPH_DIR)), name="graph_artifacts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def build_ws_response(final_event):
    try:
        session_state = final_event.get("session_state") or {}
        
        return {
            "type":"assistant_message",
            "message":final_event["message"],
            "artifacts":{
                "graph_html_path":session_state.get("graph_html_path") or [],
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
            
            msg_type = payload.get("type","message")
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")

            if not user_id or not session_id:
                await websocket.send_json({
                    "type": "error",
                    "message": "user_id and session_id are required.",
                })
                continue
            
            initialize_chat_session(
                user_id=user_id,
                session_id=session_id
            )
            
            await websocket.send_json({"type": "status", "message": "Cluvo is thinking..."})
            
            if msg_type == "voice_message":
                audio_b64 = payload.get("audio")
                if not audio_b64:
                    await websocket.send_json({"type": "error", "message": "audio is required."})
                    continue
                
                audio_bytes = base64.b64decode(audio_b64)
                stream = team.team_run_stream_from_audio(
                    audio_bytes=audio_bytes,
                    user_id=user_id,
                    session_id=session_id,
                    mime_type=payload.get("mime_type","audio/webm"),
                )
            else:
                message = payload.get("message")
                if not message:
                    await websocket.send_json({"type": "error", "message": "message is required."})
                    continue
                
                stream = team.team_run_stream_from_text(
                    input=message,
                    user_id=user_id,
                    session_id=session_id
                )
            
            async for chunk in stream:
                if chunk["type"] == "assistant_message":
                    await websocket.send_json(build_ws_response(chunk))
                else:
                    await websocket.send_json(chunk)
            
    except WebSocketDisconnect:
        print(f"[MAIN] Client disconnected!")
    except Exception as e:
        print(f"[MAIN] Error in websocket connection: {e}")
        
        
@app.get("/debug-version")
def debug_version():
    return {"version": "v2-with-ws-endpoint-fix"}
        
        
        
if __name__ == "__main__":
    uvicorn.run(app=app,host="0.0.0.0",port=LISTEN_PORT)


