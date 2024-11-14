"""
Core module initialization.
Exposes key database, configuration, redis, and citation query components.
"""

from .database import (
    Base,
    engine,
    async_session_maker,
    get_db,
    get_async_session,
)

from .config import (
    settings,
    Settings,
    LLMConfig,
    RedisConfig,
)

from .redis import (
    redis_client,
    RedisClient,
)

from .citation_queries import (
    CITATION_QUERY,
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY,
    CATEGORY_CITATION_QUERY,
    CITATION_SEARCH_QUERY,
    )

__all__ = [
    # Database components
    "Base",
    "engine",
    "async_session_maker",
    "get_db",
    "get_async_session",
    
    # Configuration components
    "settings",
    "Settings",
    "LLMConfig", 
    "RedisConfig",
    
    # Redis components
    "redis_client",
    "RedisClient",
    
    # Citation query constants
    "CITATION_QUERY",
    "LEMMA_CITATION_QUERY",
    "TEXT_CITATION_QUERY",
    "CATEGORY_CITATION_QUERY",
    "CITATION_SEARCH_QUERY",
]
