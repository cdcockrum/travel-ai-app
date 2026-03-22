from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.advisory_service import build_alerts

router = APIRouter()


@router.get("/{country_code}")
def get_alerts(country_code: str) -> dict:
    try:
        alerts = build_alerts(country_code=country_code)
        return {"country_code": country_code.upper(), "alerts": alerts}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))