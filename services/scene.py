from crud.scene import scene_crud
from schemas.scene import SceneCreate


def create_scene(db,story_id, synopsis, chosen_url):
    scene_in = SceneCreate(text=synopsis, image_url=chosen_url,story_id=story_id)
    new_scene = scene_crud.create(db,scene_in)
    return new_scene