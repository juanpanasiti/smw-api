from fastapi import FastAPI

from .api import api_router
from .core import api_description
from .database import smw_db


app = FastAPI(**api_description)

# Router
app.include_router(api_router)


@app.on_event('startup')
async def startup_event() -> None:
    smw_db.connect()


@app.on_event('shutdown')
async def shutdown_event() -> None:
    smw_db.disconnect()
