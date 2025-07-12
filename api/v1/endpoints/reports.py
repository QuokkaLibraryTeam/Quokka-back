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
    if not data.story_id and not data.comment_id:
        raise HTTPException(status_code=400, detail="Either story_id or comment_id must be provided")

    if data.story_id:
        story = db.query(Story).filter_by(id=data.story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="동화를 찾을 수 없습니다.")

    if data.comment_id:
        comment = db.query(Comment).filter_by(id=data.comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    report = Report(
        reporter_id=reporter_id,
        story_id=data.story_id,
        comment_id=data.comment_id,
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