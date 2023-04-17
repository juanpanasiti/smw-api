from typing import Generic
from typing import List
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from ..database import smw_db

ModelType = TypeVar('ModelType')


class BaseRepository(Generic[ModelType]):
    def __init__(self) -> None:
        self.session_db: Session = smw_db.session
        self.model = ModelType

    def create_db(self, new_resource: ModelType) -> ModelType:
        try:
            self.session_db.add(new_resource)
            self.session_db.commit()
            self.session_db.refresh(new_resource)
            return new_resource
        except Exception as ex:
            self.session_db.rollback()
            raise ex
        finally:
            self.session_db.close()

    # TODO: AGREGAR TRY-EXCEPT A LOS SIGUIENTES METODOS
    def get_all(self, limit: int = 10, offset: int = 0) -> List[ModelType]:
        query = select(self.model.__table__).offset(offset).limit(limit)
        results = self.session_db.execute(query).fetchall()
        return [self.model(**result) for result in results]

    def get_by_id(self, id: UUID) -> ModelType:
        query = self.session_db.query(self.model).filter_by(id=id)
        try:
            return query.one()
        except NoResultFound:
            return None

    def update(self, resource: ModelType) -> ModelType:
        self.session_db.add(resource)
        self.session_db.commit()
        self.session_db.refresh(resource)
        return resource

    def delete(self, id: str) -> ModelType:
        obj = self.get_by_id(id)
        if obj:
            self.session_db.delete(obj)
            self.session_db.commit()
            return obj
        # TODO: Cambiar por lanzar NotFoundError
        return None
