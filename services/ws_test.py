import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8005/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to dashboard UI websocket!")
        while True:
            response = await websocket.recv()
            print(f"Received from UI WS: {json.loads(response)}")

asyncio.get_event_loop().run_until_complete(test_ws())
