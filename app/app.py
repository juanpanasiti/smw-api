from fastapi import FastAPI

from .core import api_description
app = FastAPI(**api_description)

