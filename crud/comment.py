from crud.base import CRUDBase
from models.comment import Comment
from schemas.comment import CommentCreate, CommentUpdate

comment_crud = CRUDBase[Comment, CommentCreate, CommentUpdate](Comment)
