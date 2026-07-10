# Cluvo Frontend

Dependency-free browser frontend for the Cluvo KSP crime intelligence assistant.

## Run

Start the backend from `D:\Intelligent_Conversational_Assistant_KSP`:

```bash
uvicorn main:app --reload
```

Then open this file in your browser:

```text
D:\Cluvo_frontend\index.html
```

The frontend connects to:

```text
ws://127.0.0.1:8000/ws/chat
```

Artifacts are loaded from:

```text
http://127.0.0.1:8000/reports/...
http://127.0.0.1:8000/graph_artifacts/...
```
