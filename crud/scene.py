from crud.base import CRUDBase
from models.scene import Scene
from schemas.scene import SceneBase, SceneCreate, SceneUpdate


class CRUDScene(CRUDBase[SceneBase, SceneCreate, SceneUpdate]):
    pass

scene_crud = CRUDScene(Scene)