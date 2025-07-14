from sqladmin import ModelView
from models.story import Story
from models.scene import Scene

class StoryAdmin(ModelView, model=Story):
    # CRUD 기능 활성화
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # 리스트에 표시할 컬럼
    column_list = [
        Story.id,
        "user_nickname",
        Story.user_id,
        Story.original,
        Story.title,
        Story.created_at,
        Story.updated_at,
    ]

    # 상세 화면에서 숨길 raw 관계 컬럼
    details_exclude_list = ["user", "comments", "likes", "shares", "reports"]

    # 생성 및 수정 폼에 표시할 필드
    form_create_columns = [
        "user_id",
        "original",
        "title",
    ]
    form_edit_columns = [
        "original",
        "title",
    ]

    # Scene 인라인 편집 설정: 상세 화면에서 Scene을 별도 폼으로
    inline_models = [
        (Scene, {
            "form_columns": ["order_idx", "text", "image_url", "created_at"],
        })
    ]

    # user_nickname 컬럼 포매터
    column_formatters = {
        "user_nickname": lambda obj, prop: obj.user.nickname if obj.user else ""
    }

        # 상세·생성·수정 폼에서 scenes 관계(raw list) 제거
    form_excluded_columns = ["scenes"]
    details_exclude_list  = [
        "user", "comments", "likes", "shares", "reports", "scenes"
    ]

    name = "Story"
    name_plural = "Stories"
