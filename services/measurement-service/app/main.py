"""Measurement Service — FastAPI entry point."""

from decimal import Decimal

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from . import __version__
from .config import get_settings
from .gwp import passes_gwp
from .models import CalibrationEvent, WeighEvent
from .store import get_store

app = FastAPI(
    title="MT Measurement Service",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
)


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": "measurement-service",
            "product": "FreeWeigh.Net",
            "version": __version__,
            "compliance": ["ALCOA+", "CFR-21-Part-11", "GWP"],
        }
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/weigh", status_code=status.HTTP_201_CREATED)
async def weigh(event: WeighEvent) -> dict:
    store = get_store()
    record_id = await store.append("weigh", event.to_audit_payload())
    return {"audit_id": record_id, "device_id": event.device_id}


@app.post("/calibrate", status_code=status.HTTP_201_CREATED)
async def calibrate(event: CalibrationEvent) -> dict:
    ok = passes_gwp(Decimal(event.reference_kg), Decimal(event.measured_kg))
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reading exceeds maximum permissible error for the load band.",
        )
    store = get_store()
    record_id = await store.append("calibrate", event.model_dump(mode="json"))
    return {"audit_id": record_id, "device_id": event.device_id, "gwp_pass": True}


@app.get("/audit")
async def audit(limit: int = 50) -> dict:
    s = get_settings()
    capped = max(1, min(limit, 500))
    records = await get_store().list_recent(limit=capped)
    return {
        "namespace": s.redis_namespace,
        "count": len(records),
        "records": records,
    }
