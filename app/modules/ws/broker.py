from collections import defaultdict
from fastapi import WebSocket

class WsBroker:
    def __init__(self):
        self.ws_to_subs: dict[WebSocket, dict] = {}
        self.pc_to_ws: dict[str, set[WebSocket]] = defaultdict(set)

    async def subscribe(self, ws: WebSocket, pc_ids: list[str], streams: list[str], procs_filter: dict | None):
        subs = self.ws_to_subs.get(ws) or {"pc_ids": set(), "streams": set(), "procs_filter": None}
        subs["pc_ids"].update(pc_ids)
        subs["streams"].update(streams)
        subs["procs_filter"] = procs_filter
        self.ws_to_subs[ws] = subs

        for pc in pc_ids:
            self.pc_to_ws[pc].add(ws)

    async def unsubscribe(self, ws: WebSocket, pc_ids: list[str]):
        subs = self.ws_to_subs.get(ws)
        if not subs:
            return
        for pc in pc_ids:
            subs["pc_ids"].discard(pc)
            self.pc_to_ws[pc].discard(ws)

    async def disconnect(self, ws: WebSocket):
        subs = self.ws_to_subs.pop(ws, None)
        if subs:
            for pc in list(subs["pc_ids"]):
                self.pc_to_ws[pc].discard(ws)

    def targets_for_pc(self, pc_id: str) -> list[WebSocket]:
        return list(self.pc_to_ws.get(pc_id, set()))

    def subs_for_ws(self, ws: WebSocket) -> dict | None:
        return self.ws_to_subs.get(ws)
    
    async def send_to_pc(self, pc_id: str, message: dict):
        for ws in self.targets_for_pc(pc_id):
            try:
                await ws.send_json(message)
            except Exception:
                pass
                