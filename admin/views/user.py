from sqladmin import ModelView
from models.user import User

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.google_id, User.nickname, User.created_at]
    name = "User"
    name_plural = "Users"
