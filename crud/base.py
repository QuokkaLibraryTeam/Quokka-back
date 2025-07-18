from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    # ───── R ─────────────────────────────────────────────
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return (
            db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_by_user(self, db: Session, user_id: str) -> List[ModelType]:
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .all()
        )

    def get_all(self, db: Session) -> List[ModelType]:
        return db.query(self.model).all()

    # ───── C ─────────────────────────────────────────────
    def create(
        self, db: Session, obj_in: CreateSchemaType, **extra
    ) -> ModelType:
        db_obj = self.model(**obj_in.dict(), **extra)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ───── U ─────────────────────────────────────────────
    def update(
        self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ───── D ─────────────────────────────────────────────
    def remove(self, db: Session, id: int) -> Optional[ModelType]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
