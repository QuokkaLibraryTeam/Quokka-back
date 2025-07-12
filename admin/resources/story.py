from fastapi_admin.resources import Model
from fastapi_admin.widgets import displays, fields
from models.story import Story

class StoryResource(Model):
    label = "Story"
    model = Story
    page_pre_title = "Stories"
    page_title = "Story List"

    fields = [
        displays.Display(name="id", label="ID"),
        fields.ForeignKey(name="user", label="Author"),
        fields.Input(name="title"),
        fields.Switch(name="original", label="Original"),
        displays.Datetime(name="created_at"),
        displays.Datetime(name="updated_at"),
        displays.Display(name="comment_count", label="Comments", getter=lambda obj: len(obj.comments)),
        displays.Display(name="like_count", label="Likes", getter=lambda obj: len(obj.likes)),
    ]
