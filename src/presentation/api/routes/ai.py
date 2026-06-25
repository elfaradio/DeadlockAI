from __future__ import annotations

from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.application.dtos.schemas import AIExplainRequestDTO
from src.application.services.ai_explainer import AIExplainerService, DeadlockExplanation
from src.application.services.report import ReportService
from src.infrastructure.di.container import get_ai_explainer_service, get_report_service

router = APIRouter(prefix="/api/ai", tags=["AI Explainer"])


@router.post("/explain", response_model=DeadlockExplanation)
async def explain_deadlock(
    dto: AIExplainRequestDTO,
    ai_service: AIExplainerService = Depends(get_ai_explainer_service),
):
    try:
        explanation = await ai_service.explain_deadlock(
            deadlock_cycle=dto.deadlock_cycle,
            processes=dto.processes,
            resources=dto.resources,
            banker_summary=dto.banker_summary,
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {e}",
        )


@router.post("/report")
async def download_report(
    payload: dict,
    report_service: ReportService = Depends(get_report_service),
):
    try:
        processes = payload.get("processes", [])
        resources = payload.get("resources", [])
        allocations = payload.get("allocations", [])
        deadlock_cycle = payload.get("deadlock_cycle", [])
        ai_exp_data = payload.get("ai_explanation")

        if isinstance(ai_exp_data, dict):
            ai_explanation = DeadlockExplanation(**ai_exp_data)
        else:
            ai_explanation = str(ai_exp_data or "")

        pdf_bytes = report_service.generate_pdf_report(
            processes=processes,
            resources=resources,
            allocations=allocations,
            deadlock_cycle=deadlock_cycle,
            ai_explanation=ai_explanation,
        )

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=deadlockai_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {e}",
        )
