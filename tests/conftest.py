import os

import dotenv
import pytest
from alembic import config
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionmaker  # noqa: N812
from sqlalchemy.ext.asyncio import create_async_engine

dotenv.load_dotenv(".env")
pytest_plugins = [
    "anyio",
    "sqlalchemy_pytest.database",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def worker_id() -> str:
    return "main"


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def engine(sqlalchemy_pytest_database_url: str) -> AsyncEngine:
    return create_async_engine(
        url=sqlalchemy_pytest_database_url,
    )


@pytest.fixture
def async_sessionmaker(engine: AsyncEngine) -> AsyncSessionmaker[AsyncSession]:
    return AsyncSessionmaker(bind=engine)


@pytest.fixture(scope="session")
def alembic_config() -> config.Config | None:
    return None
