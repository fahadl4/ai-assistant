from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.router import api_router
from app.db.seed import seed_permissions, seed_roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_roles()
    await seed_permissions()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)