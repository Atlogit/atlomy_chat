import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

# Determine database connection strategy
def get_database_url():
    """
    Dynamically determine database connection URL based on deployment mode.
    Supports local, Docker, and cloud environments.
    """
    # Check for explicit DATABASE_URL environment variable
    explicit_url = os.getenv('DATABASE_URL')
    if explicit_url:
        return explicit_url

    # Default connection parameters with Docker and local environment support
    default_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'db': os.getenv('POSTGRES_DB', 'amta_greek'),
        'user': os.getenv('POSTGRES_USER', 'local_dev_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'dev_password')
    }

    # Special handling for Docker and production environments
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'development')
    if deployment_mode in ['production', 'staging']:
        # Use Docker container name or host network
        default_params['host'] = 'localhost'

    # Construct connection URL
    connection_url = (
        f"postgresql+asyncpg://{default_params['user']}:"
        f"{default_params['password']}@"
        f"{default_params['host']}:"
        f"{default_params['port']}/"
        f"{default_params['db']}"
    )

    return connection_url

# Create base class for declarative models
Base = declarative_base()

# Create async engine with enhanced configuration
engine = create_async_engine(
    get_database_url(),
    poolclass=AsyncAdaptedQueuePool,
    pool_size=int(os.getenv('DB_POOL_SIZE', 30)),  # Increased pool size
    max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 15)),  # More overflow connections
    pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 45)),  # Longer timeout
    pool_recycle=int(os.getenv('DB_POOL_RECYCLE', 3600)),  # Recycle connections every hour
    pool_pre_ping=True,  # Test connection health before use
    echo=os.getenv('DEBUG', 'False').lower() == 'true'
)

# Create async session factory with improved error handling
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Enhanced async session generators with comprehensive error handling
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session with robust error handling and logging.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in database session: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {close_error}", exc_info=True)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions with comprehensive error handling.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in database session: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {close_error}", exc_info=True)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session with comprehensive error handling and logging.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in database session: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {close_error}", exc_info=True)
