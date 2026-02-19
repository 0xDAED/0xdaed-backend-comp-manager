from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(tags=["ws"])


class WsSubscribe(BaseModel):
    action: str 
    pc_ids: list[UUID]
    streams: list[str] 
    procs_filter: dict | None = None


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    broker = ws.app.state.ws_broker  
    await ws.accept()

    try:
        while True:
            msg = await ws.receive_json()
            data = WsSubscribe(**msg)

            pc_ids = [str(x) for x in data.pc_ids]
            if data.action == "subscribe":
                await broker.subscribe(ws, pc_ids, data.streams, data.procs_filter)
                await ws.send_json({"ok": True, "subscribed": pc_ids})
            elif data.action == "unsubscribe":
                await broker.unsubscribe(ws, pc_ids)
                await ws.send_json({"ok": True, "unsubscribed": pc_ids})
            else:
                await ws.send_json({"ok": False, "error": "unknown_action"})
    except WebSocketDisconnect:
        pass
    finally:
        await broker.disconnect(ws)
