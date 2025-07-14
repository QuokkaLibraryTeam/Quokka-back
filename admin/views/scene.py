from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter
from models.scene import Scene
from models.story import Story

class SceneAdmin(ModelView, model=Scene):
    can_create    = True
    can_edit      = True
    can_delete    = True

    column_list = [
        Scene.id,
        Scene.story_id,
        Scene.order_idx,
        Scene.text,
        Scene.image_url,
        Scene.created_at,
    ]

    # 문자열이 아니라 ColumnFilter 객체로 교체
    column_filters = [
        ForeignKeyFilter(
            Scene.story_id,      # FK 컬럼
            Story.title,         # 표시할 관계 모델의 필드
            title="Story"        # 필터 패널에 표시될 레이블
        )
    ]

    column_editable_list = ["order_idx", "text", "image_url"]
    form_columns         = ["story_id", "order_idx", "text", "image_url"]

    name        = "Scene"
    name_plural = "Scenes"
