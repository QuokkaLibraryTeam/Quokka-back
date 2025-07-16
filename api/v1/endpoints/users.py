from fastapi import APIRouter, Request, Depends

from core.security import verify_token
from schemas.story import StoriesOut
from services.story import get_all_stories_by_user_id

router = APIRouter()

@router.get("/me/stories",response_model=StoriesOut)
def list_stories_by_user(request: Request,user_id: str = Depends(verify_token)):
    db = request.state.db
    stories = get_all_stories_by_user_id(db,user_id)
    return {"stories" : stories}




