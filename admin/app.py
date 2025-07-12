from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.template import templates
from starlette.requests import Request
from fastapi import FastAPI

from models.user import User
from models.report import Report
from models.story import Story
from models.comment import Comment
from models.like import Like

from admin.resources import resources

import uvicorn

async def create_admin():
    await admin_app.configure(
        logo_url="https://fastapi-admin.github.io/img/logo.png",
        template_folders=[],
        providers=[
            UsernamePasswordProvider(
                admin_model=User,
                login_logo_url="https://fastapi-admin.github.io/img/logo.png",
            )
        ],
        resources=resources,
    )