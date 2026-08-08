"""RFP API routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.rfp_bridge import (
    RfpDocumentResponse,
    RfpResumeRequest,
    RfpTicketResponse,
    RfpUploadResponse,
    create_rfp_ticket,
    get_rfp_document,
    get_rfp_ticket,
    resume_rfp_ticket,
)

router = APIRouter(prefix="/api/rfp", tags=["rfp"])


@router.post("/upload", response_model=RfpUploadResponse)
async def upload_rfp(file: UploadFile = File(...)) -> RfpUploadResponse:
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="PDF or text upload required.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Upload is empty.")
    try:
        return create_rfp_ticket(filename=filename, content=content)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{ticket_id}", response_model=RfpTicketResponse)
def fetch_rfp_ticket(ticket_id: str) -> RfpTicketResponse:
    try:
        return get_rfp_ticket(ticket_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc


@router.post("/{ticket_id}/resume")
def resume_rfp(ticket_id: str, body: RfpResumeRequest) -> dict:
    try:
        return resume_rfp_ticket(ticket_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{ticket_id}/document", response_model=RfpDocumentResponse)
def fetch_rfp_document(ticket_id: str) -> RfpDocumentResponse:
    try:
        return get_rfp_document(ticket_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
