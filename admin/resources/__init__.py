# admin/resources/__init__.py
from .user import UserResource
from .report import ReportResource
from .story import StoryResource

resources = [
    UserResource,
    ReportResource,
    StoryResource,
]