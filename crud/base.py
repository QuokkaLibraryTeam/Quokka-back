from typing import TypeVar, Generic, Type, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")  # SQLAlchemy 모델
CreateSchemaType = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchema", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    # R
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_all(self, db: Session):
        return db.query(self.model).all()

    # C
    def create(self, db: Session, obj_in: CreateSchemaType, **extra) -> ModelType:
        db_obj = self.model(**obj_in.dict(), **extra)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # U
    def update(self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # D
    def remove(self, db: Session, id: int) -> ModelType | None:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
