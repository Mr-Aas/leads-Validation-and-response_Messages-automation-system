import json
from fastapi import FastAPI, Request, WebSocket, HTTPException, WebSocketDisconnect
from typing import List
import hmac
from hashlib import sha256


app = FastAPI()

WEBSOCKET_HOOK=b'my-first-websocket-app'

class ConnectionManager:
    def __init__(self):
        self.active_connection: List[ WebSocket ] = []
    async def connect(self,connection:WebSocket):
        await connection.accept()
        self.active_connection.append(connection)
    async def disconnect(self, connection:WebSocket):
        self.active_connection.remove(connection)
    async def broadCast(self,message):
        for connection in self.active_connection:
            connection.send(message)


manager = ConnectionManager()




@app.websocket('/ws')
async def manage_connection(websocket:WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            websocket.recieve_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post('/api/v1/webhook')
async def receive_webhook(request:Request):
    payload = await request.body
    signature = request.header.get("client_signature")
    
    if not signature:
        raise HTTPException(status_code=400,message="signature is missing")
    valid_signature = hmac.new(WEBSOCKET_HOOK, payload , sha256).hexdigest
    if not hmac.compare_digest(valid_signature,signature):
        raise HTTPException(status_code=403,message="invalid signature , singature varification fails")
    event_data = json.load(payload)
    await manager.broadCast({
        "event":event_data.get("event_type"),
        "data":event_data.get("data")})
    return {"status":"success"}
    

