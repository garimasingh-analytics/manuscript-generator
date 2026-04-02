from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.settings import settings

_client = None  # type: AsyncIOMotorClient


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_url)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    client = get_client()
    return client[settings.mongo_db_name]


def users_col():
    return get_db()["users"]


def projects_col():
    return get_db()["projects"]


def jobs_col():
    return get_db()["generation_jobs"]

