import json
import uuid

from src.core.redis import redis_client
from src.schemas.projection import PeriodProjectionSchema
from src.schemas.response import StandardResponse
from src.services.projection_service import ProjectionService


class ProjectionController:
    def __init__(self, projection_service: ProjectionService):
        self.projection_service = projection_service

    async def get_period_projection(self, user_id: uuid.UUID, period: str) -> StandardResponse[PeriodProjectionSchema]:
        cache_key = f"user:{user_id}:projections:{period}"

        # 1. Try to fetch from Redis cache
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            # We return it directly parsing it to schema
            parsed_data = json.loads(cached_data)
            return StandardResponse(success=True, data=PeriodProjectionSchema.model_validate(parsed_data))

        # 2. Cache Miss: Calculate projection
        projection = await self.projection_service.get_period_projection(user_id, period)

        # 3. Store in Redis
        # We store the dict representation of the model.
        # model_dump(mode='json') automatically converts Decimals to floats/strings so it's JSON serializable
        projection_dict = projection.model_dump(mode="json")
        await redis_client.set(
            cache_key,
            json.dumps(projection_dict),
            ex=3600,  # 1 hour TTL
        )

        return StandardResponse(success=True, data=projection)

    async def get_multiple_projections(
        self, user_id: uuid.UUID, start_period: str, limit: int
    ) -> StandardResponse[list[PeriodProjectionSchema]]:
        periods = []
        current_period = start_period

        # Compute the list of periods
        for _ in range(limit):
            periods.append(current_period)
            year, month = map(int, current_period.split("-"))
            month += 1
            if month > 12:
                month = 1
                year += 1
            current_period = f"{year}-{month:02d}"

        # Fetch all projections for these periods
        # We can use get_period_projection for each to utilize the cache
        projections = []
        for period in periods:
            res = await self.get_period_projection(user_id, period)
            projections.append(res.data)

        return StandardResponse(success=True, data=projections)
