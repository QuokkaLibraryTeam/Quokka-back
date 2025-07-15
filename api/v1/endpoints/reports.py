# routers/community_report.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import verify_token
from db.base import get_db
from schemas.report import ReportCreate
from services.report import submit_report

router = APIRouter()

@router.post("", status_code=status.HTTP_201_CREATED)
def report_content(
    data: ReportCreate,
    reporter_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        report = submit_report(db, data=data, reporter_id=reporter_id)
        return {"message": "신고가 접수되었습니다.", "report_id": report.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
