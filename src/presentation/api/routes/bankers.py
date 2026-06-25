from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos.schemas import BankerEvaluateDTO
from src.application.services.bankers import BankersService
from src.infrastructure.di.container import get_bankers_service

router = APIRouter(prefix="/api/bankers", tags=["Banker's Algorithm"])


@router.post("/evaluate")
async def evaluate_bankers(
    dto: BankerEvaluateDTO,
    service: BankersService = Depends(get_bankers_service),
):
    try:
        result = service.evaluate(
            allocation=dto.allocation,
            maximum=dto.maximum,
            available=dto.available,
            process_names=dto.process_names,
        )
        return {
            "safe": result.safe,
            "safe_sequence": result.safe_sequence,
            "need_matrix": result.need_matrix,
            "work_trace": result.work_trace,
            "explanation": result.explanation,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
