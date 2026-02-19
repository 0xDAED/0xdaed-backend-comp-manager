from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/pcs", response_model=DashboardResponse)
async def get_dashboard(session: AsyncSession = Depends(get_session)):
    svc = DashboardService()
    return await svc.get_pcs(session)
