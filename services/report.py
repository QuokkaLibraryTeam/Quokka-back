# services/report_service.py
from datetime import datetime

from sqlalchemy.orm import Session

from crud.comment import comment_crud
from crud.report import report_crud
from crud.story import story_crud
from schemas.report import ReportCreate, ReportOut


def submit_report(db: Session, *, data: ReportCreate, reporter_id: str) -> ReportOut:
    if data.story_id:
        if not story_crud.get(db, id=data.story_id):
            raise ValueError("Story not found")
    if data.comment_id:
        if not comment_crud.get(db, id=data.comment_id):
            raise ValueError("Comment not found")

    db_report = report_crud.create(
        db,
        obj_in=data,
        reporter_id=reporter_id,
        created_at=datetime.utcnow(),
    )
    return ReportOut.model_validate(db_report)
