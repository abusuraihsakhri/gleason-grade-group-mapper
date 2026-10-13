"""
FastAPI REST API Server for Gleason Grade Group Mapper.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="Gleason Grade Group Mapper API",
    description="Enterprise Distributed Component Platform (Digital Pathology & Histology Systems)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_DIRECTORY / "index.html")


@app.get("/operations", include_in_schema=False)
def operations():
    return FileResponse(WEB_DIRECTORY / "operations.html")


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "gleason-grade-group-mapper", "domain": "Digital Pathology & Histology Systems", "standard": "CAP Cancer Protocols / DICOM WSI PS3.16", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
