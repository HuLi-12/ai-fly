from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.models.schemas import KnowledgeDocumentDetail, KnowledgeDocumentSummary
from app.services.knowledge import get_document, list_documents


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=list[KnowledgeDocumentSummary])
def documents(keyword: str | None = Query(default=None), category: str | None = Query(default=None)) -> list[KnowledgeDocumentSummary]:
    settings = get_settings()
    return [KnowledgeDocumentSummary(**item) for item in list_documents(settings.materials_root, keyword=keyword, category=category)]


@router.get("/documents/{document_id:path}", response_model=KnowledgeDocumentDetail)
def document_detail(document_id: str) -> KnowledgeDocumentDetail:
    settings = get_settings()
    try:
        detail = get_document(settings.materials_root, document_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="资料不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeDocumentDetail(**detail)
