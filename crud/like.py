from crud.base import CRUDBase
from models.like import Like
from schemas.like import LikeCreate  # 업데이트 필요 없음

like_crud = CRUDBase[Like, LikeCreate, LikeCreate](Like)