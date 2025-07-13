from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db.base import get_db
from models import Story, Comment, Report
from core.security import verify_token
from schemas.report import ReportCreate

router = APIRouter()

@router.post("/report")
def report_content(
    data: ReportCreate,
    reporter_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    report = Report(
        reporter_id=reporter_id,
        story_id=data.story_id,     # None 이거나 유효한 >0 정수
        comment_id=data.comment_id, # None 이거나 유효한 >0 정수
        reason=data.reason,
        created_at=datetime.utcnow()
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "message": "신고가 접수되었습니다.", 
        "report_id": report.id
    }