from typing import Generic
from typing import List
from typing import TypeVar
from uuid import UUID

from ..database.models import BaseModel
from ..repositories import BaseRepository

InputSchemaType = TypeVar('InputSchemaType')
OutputSchemaType = TypeVar('OutputSchemaType')
ModelType = TypeVar('ModelType', bound=BaseModel)
RepoType = TypeVar('RepoType', bound=BaseRepository)


class BaseService(Generic[ModelType, InputSchemaType, OutputSchemaType, RepoType]):
    def __init__(self, RepoClass):
        self.repo: RepoType = RepoClass()

    def create(self, new_resource_dto: InputSchemaType) -> OutputSchemaType:
        new_resource_model: ModelType = self.repo.create_db(
            self._to_model(new_resource_dto))

        return self._to_schema(new_resource_model)

    def get_all(self, limit: int = 10, offset: int = 0) -> List[OutputSchemaType]:
        resource_list = self.repo.get_all(limit, offset)

        return [self._to_schema(model_resource) for model_resource in resource_list]

    def get_by_id(self, id: UUID):
        return self.repo.get_by_id(id)

    def update(self, resource: InputSchemaType) -> OutputSchemaType:
        return self.repo.update(resource)

    def delete(self, id: UUID):
        return self.repo.delete(id)

    def _to_schema(self, model_object: ModelType) -> OutputSchemaType:
        raise NotImplementedError(
            'This method "__to_dto" must be implemented in subclasses')

    def _to_model(self, dto_object: InputSchemaType) -> ModelType:
        raise NotImplementedError(
            'This method "__to_model" must be implemented in subclasses')
