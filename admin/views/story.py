from sqladmin import ModelView
from models.story import Story

class StoryAdmin(ModelView, model=Story):
    # 컬럼 목록에 문자열로 user_nickname 지정
    column_list = [Story.id, "user_nickname", Story.title, Story.created_at]

    # SQLAdmin의 column_formatters는 (obj, prop) 함수 시그니처를 사용함
    column_formatters = {
        "user_nickname": lambda obj, prop: obj.user.nickname
    }

    name = "Story"
    name_plural = "Stories"
