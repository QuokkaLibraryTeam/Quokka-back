from fastapi_admin.resources import Model
from fastapi_admin.widgets import displays, fields
from models.user import User

class UserResource(Model):
    label = "User"
    model = User
    page_pre_title = "Users"
    page_title = "User List"

    fields = [
        displays.Display(name="id", label="ID"),
        fields.Input(name="google_id", label="Google ID"),
        fields.Input(name="nickname", label="Nickname"),
        displays.Datetime(name="created_at"),
    ]
