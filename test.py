import asyncio
import json
import websockets

async def test():
    uri = "ws://127.0.0.1:8000/ws/chat"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "user_id": "test-user-001",
            "session_id": "test-session-001",
            "message": "Generate a case report for FIR KSP/2023/0042."
        }))

        print(await ws.recv())
        print(await ws.recv())

asyncio.run(test())