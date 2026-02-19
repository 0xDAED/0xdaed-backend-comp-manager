import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.modules.ws.broker import WsBroker
from app.modules.ws.consumers import run_ws_fanout_consumers

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)

    broker = WsBroker()
    app.state.ws_broker = broker

    task = asyncio.create_task(run_ws_fanout_consumers(broker))
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except Exception:
            pass
