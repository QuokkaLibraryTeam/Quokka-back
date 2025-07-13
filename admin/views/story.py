from sqladmin import ModelView
from models.story import Story

class StoryAdmin(ModelView, model=Story):
    column_list = [Story.id, Story.user_id, Story.title, Story.created_at]
    name = "Story"
    name_plural = "Stories"

    