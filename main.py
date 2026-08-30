import asyncio
import base64
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from agno.tracing import setup_tracing
from agno.db.sqlite import SqliteDb
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.config import REPORTS_DIR, GRAPH_DIR, LISTEN_PORT,TRACES_DB
import uvicorn

print("========== MAIN.PY STARTING ==========")

team = None
team_ready = asyncio.Event()

async def init_team_background():
    global team
    try:
        print("[INIT] Starting InvestigationTeam initialization in background...")
        from backend.orchestrator.router import InvestigationTeam
        loop = asyncio.get_event_loop()
        team = await loop.run_in_executor(None, InvestigationTeam)
        print("[INIT] InvestigationTeam initialized successfully")
    except Exception as e:
        print(f"[INIT] FAILED to initialize InvestigationTeam: {e}")
    finally:
        team_ready.set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(init_team_background())
    yield


app = FastAPI(title="Cluvo",lifespan=lifespan)
print("FastAPI app created")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
app.mount("/graph_artifacts", StaticFiles(directory=str(GRAPH_DIR)), name="graph_artifacts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

traces_db = SqliteDb(db_file=TRACES_DB)
setup_tracing(db=traces_db)

print("Tracing initialized")



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
        await team_ready.wait()
        if team is None:
            job_store[job_id]["events"].append({"type": "error", "message": "Service still starting up, try again shortly."})
            return
        async for chunk in team.team_run_stream_from_text(message, user_id, session_id):
            job_store[job_id]["events"].append(chunk)
    except Exception as e:
        job_store[job_id]["events"].append({"type": "error", "message": "Something went wrong."})
        print(f"[MAIN] Error in text job {job_id}: {e}")
    finally:
        job_store[job_id]["done"] = True


async def run_audio_job(job_id: str, audio_bytes: bytes, user_id: str, session_id: str, mime_type: str):
    try:
        await team_ready.wait()
        if team is None:
            job_store[job_id]["events"].append({"type": "error", "message": "Service still starting up, try again shortly."})
            return
        async for chunk in team.team_run_stream_from_audio(audio_bytes, session_id, user_id, mime_type):
            job_store[job_id]["events"].append(chunk)
    except Exception as e:
        job_store[job_id]["events"].append({"type": "error", "message": "Something went wrong."})
        print(f"[MAIN] Error in audio job {job_id}: {e}")
    finally:
        job_store[job_id]["done"] = True
        
        
@app.get("/")
def root():
    return {"status": "ok","team_ready":team_ready.is_set()}


@app.post("/chat/message")
async def start_text_job(payload: dict):
    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    message = payload.get("message")

    if not user_id or not session_id or not message:
        return {"error": "user_id, session_id, and message are required."}

    if team is not None:
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

    if team is not None:
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

@app.get("/debug/traces")
async def get_traces(limit:int=20):
    traces,total = traces_db.get_traces(limit=limit)
    return {
        "total": total,
        "traces": [
            {
                "trace_id": t.trace_id,
                "name": t.name,
                "status": t.status,
                "duration_ms": round(t.duration_ms, 2),
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "total_spans": t.total_spans,
                "error_count": t.error_count,
                "run_id": t.run_id,
                "session_id": t.session_id,
                "user_id": t.user_id,
                "team_id": t.team_id,
                "agent_id": t.agent_id,
                "workflow_id": t.workflow_id,
            }
            for t in traces
        ],
    }


if __name__ == "__main__":
    print(f"Starting Uvicorn on {LISTEN_PORT}")
    uvicorn.run(app=app, host="0.0.0.0", port=LISTEN_PORT)