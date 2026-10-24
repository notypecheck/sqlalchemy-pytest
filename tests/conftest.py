from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING, cast

import pytest
import sqlalchemy
from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionmaker  # noqa: N812
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

from sqlalchemy_pytest._utils import get_op

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy import Connection

pytest_plugins = [
    "anyio",
    "sqlalchemy_pytest.database",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(params=["postgres", "sqlite"])
def database_type(request: pytest.FixtureRequest) -> str:
    return cast("str", request.param)


@pytest.fixture(scope="session")
def postgres_container_url() -> Generator[str, None, None]:
    pg = PostgresContainer(
        "postgres:16",
        username="postgres",
        password="password",
        dbname="postgres",
        driver="asyncpg",
    )
    with pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
def worker_id() -> str:
    return "main"


@pytest.fixture
def database_url(
    database_type: str,
    postgres_container_url: str,
) -> str:
    return (
        postgres_container_url
        if database_type == "postgres"
        else "sqlite+aiosqlite:///db.sqlite3"
    )


@pytest.fixture
def engine(sqlalchemy_pytest_database_url: sqlalchemy.URL) -> AsyncEngine:
    return create_async_engine(url=sqlalchemy_pytest_database_url)


@pytest.fixture
async def sqlalchemy_pytest_database_url(
    database_url: str,
    worker_id: str,
) -> sqlalchemy.URL:
    url = make_url(database_url)
    return url.set(database=f"{url.database}-{worker_id}")


@pytest.fixture
async def _sqlalchemy_create_database(
    database_url: str,
    sqlalchemy_pytest_database_url: sqlalchemy.URL,
    reuse_db: bool,  # noqa: FBT001
) -> AsyncGenerator[None, None]:
    engine = create_async_engine(
        database_url,
        execution_options={"isolation_level": "AUTOCOMMIT"},
    )
    op = get_op(engine=engine, connection_url=sqlalchemy_pytest_database_url)
    await op.create_db_if_not_exists()
    yield
    await op.drop_db(reuse_db=reuse_db)
    await engine.dispose()


@pytest.fixture
async def sqlalchemy_pytest_engine(
    sqlalchemy_pytest_database_url: sqlalchemy.URL,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(sqlalchemy_pytest_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def alembic_config() -> Config | None:
    return None


@pytest.fixture
async def _sqlalchemy_run_migrations(
    _sqlalchemy_create_database: None,
    sqlalchemy_pytest_engine: AsyncEngine,
    alembic_config: Config | None,
    database_url: str,
) -> None:
    from alembic import command  # noqa: PLC0415

    if alembic_config is None:
        return

    def run_upgrade(connection: Connection, cfg: Config) -> None:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, revision="head")

    async with sqlalchemy_pytest_engine.begin() as conn:
        alembic_config.set_main_option("sqlalchemy.url", database_url)
        await conn.run_sync(run_upgrade, alembic_config)
        await conn.commit()


@pytest.fixture
def async_sessionmaker(engine: AsyncEngine) -> AsyncSessionmaker[AsyncSession]:
    return AsyncSessionmaker(bind=engine)
