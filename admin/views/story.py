from sqladmin import ModelView
from models.story import Story

class StoryAdmin(ModelView, model=Story):
    # CRUD 기능 활성화
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # 리스트에 표시할 컬럼
    column_list = [
        Story.id,
        "user_nickname",  # 관계된 User.nickname
        Story.user_id,
        Story.original,
        Story.title,
        Story.created_at,
        Story.updated_at,
    ]

    # 상세 및 생성/수정 폼에 포함할 필드
    form_create_columns = [
        "user_id",
        "original",
        "title",
        "created_at",
        "updated_at",
    ]
    form_edit_columns = [
        "user_id",
        "original",
        "title",
        "updated_at",
    ]

    # 렌더링된 리스트에 user_nickname 추가
    column_formatters = {
        "user_nickname": lambda obj, prop: obj.user.nickname
    }

    name = "Story"
    name_plural = "Stories"
