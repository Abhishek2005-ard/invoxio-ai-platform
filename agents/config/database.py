"""
Invoxio Agent — Database Configuration
Provides an async MongoDB client using motor.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Global client instance
_client: AsyncIOMotorClient = None
_db = None

async def get_db():
    """
    Returns the async MongoDB database instance.
    If MONGODB_URI is not set, returns None so callers can fall back to stub data.
    """
    global _client, _db

    if not settings.mongodb_uri:
        logger.warning("MONGODB_URI is not set. Database operations will fall back to stub data.")
        return None

    if _client is None:
        try:
            _client = AsyncIOMotorClient(settings.mongodb_uri)
            _db = _client.get_default_database("invoxio")
            # Verify connection
            await _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            _client = None
            return None

    return _db
