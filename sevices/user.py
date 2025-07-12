from sqlalchemy.orm import Session
import models

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """
    주어진 ID로 사용자를 데이터베이스에서 찾아 반환합니다.
    """
    return db.get(models.User, user_id)