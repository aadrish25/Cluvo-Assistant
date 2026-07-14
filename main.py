import asyncio
import base64
import uuid
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.orchestrator.router import InvestigationTeam
from backend.config import REPORTS_DIR, GRAPH_DIR, LISTEN_PORT
import uvicorn

app = FastAPI(title="Cluvo")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/graph_artifacts", StaticFiles(directory=str(GRAPH_DIR)), name="graph_artifacts")


team = InvestigationTeam()
initialized_sessions = set()
job_store: dict[str, dict] = {}  # job_id -> {"events": [...], "done": bool}


def initialize_chat_session(user_id: str, session_id: str):
    try:
        session_key = (user_id, session_id)
        if session_key in initialized_sessions:
            return
        team.initialize_session(user_id=user_id, session_id=session_id)
        initialized_sessions.add(session_key)
    except Exception as e:
        print(f"[MAIN] Exception in initializing chat session: {e}")


def build_ws_response(final_event):
    try:
        session_state = final_event.get("session_state") or {}
        return {
            "type": "assistant_message",
            "message": final_event["message"],
            "artifacts": {
                "graph_html_path": session_state.get("graph_html_path") or [],
                "summary_report_pdf_path": session_state.get("summary_report_pdf_path"),
                "chart_data": session_state.get("chart_data"),
                "map_data": session_state.get("map_data"),
                "table_data": session_state.get("table_data") or [],
            },
        }
    except Exception as e:
        print(f"[MAIN] Exception in building ws response: {e}")


async def run_text_job(job_id: str, message: str, user_id: str, session_id: str):
    try:
        async for chunk in team.team_run_stream_from_text(message, user_id, session_id):
            job_store[job_id]["events"].append(chunk)
    except Exception as e:
        job_store[job_id]["events"].append({"type": "error", "message": "Something went wrong."})
        print(f"[MAIN] Error in text job {job_id}: {e}")
    finally:
        job_store[job_id]["done"] = True


async def run_audio_job(job_id: str, audio_bytes: bytes, user_id: str, session_id: str, mime_type: str):
    try:
        async for chunk in team.team_run_stream_from_audio(audio_bytes, session_id, user_id, mime_type):
            job_store[job_id]["events"].append(chunk)
    except Exception as e:
        job_store[job_id]["events"].append({"type": "error", "message": "Something went wrong."})
        print(f"[MAIN] Error in audio job {job_id}: {e}")
    finally:
        job_store[job_id]["done"] = True
        
        
@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/chat/message")
async def start_text_job(payload: dict):
    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    message = payload.get("message")

    if not user_id or not session_id or not message:
        return {"error": "user_id, session_id, and message are required."}

    initialize_chat_session(user_id=user_id, session_id=session_id)

    job_id = str(uuid.uuid4())
    job_store[job_id] = {"events": [], "done": False}
    asyncio.create_task(run_text_job(job_id, message, user_id, session_id))

    return {"job_id": job_id}


@app.post("/chat/voice")
async def start_voice_job(payload: dict):
    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    audio_b64 = payload.get("audio")
    mime_type = payload.get("mime_type", "audio/webm")

    if not user_id or not session_id or not audio_b64:
        return {"error": "user_id, session_id, and audio are required."}

    initialize_chat_session(user_id=user_id, session_id=session_id)

    audio_bytes = base64.b64decode(audio_b64)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"events": [], "done": False}
    asyncio.create_task(run_audio_job(job_id, audio_bytes, user_id, session_id, mime_type))

    return {"job_id": job_id}


@app.get("/chat/poll/{job_id}")
async def poll_job(job_id: str, since: int = Query(0)):
    job = job_store.get(job_id)
    if job is None:
        return {"error": "Unknown job_id."}

    new_events = job["events"][since:]
    processed = []
    for chunk in new_events:
        if chunk["type"] == "assistant_message":
            processed.append(build_ws_response(chunk))
        else:
            processed.append(chunk)

    return {"events": processed, "cursor": len(job["events"]), "done": job["done"]}


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=LISTEN_PORT)