from fastapi import FastAPI

from app.core.lifespan import lifespan
from app.modules.agents.api import router as agents_router
from app.modules.commands.api import router as commands_router
from app.modules.ws.api import router as ws_router
from app.modules.dashboard.api import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware
import app.modules.commands  # noqa: F401  


app = FastAPI(lifespan=lifespan)

app.include_router(agents_router, prefix="/api/v1")
app.include_router(commands_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",  
        "http://127.0.0.1:5174",
        "https://void-rp.ru",
        "http://void-rp.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)