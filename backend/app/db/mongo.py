"""MongoDB client and collection accessors."""
from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import get_settings


@lru_cache
def get_client() -> MongoClient:
    """Cached Mongo client singleton."""
    settings = get_settings()
    return MongoClient(settings.mongodb_uri)


def get_db() -> Database:
    settings = get_settings()
    return get_client()[settings.mongodb_db]


def get_collection() -> Collection:
    """The purchase-orders collection."""
    settings = get_settings()
    return get_db()[settings.mongodb_collection]
