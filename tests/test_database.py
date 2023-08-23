import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio]


async def test(session: AsyncSession) -> None:
    await session.execute(text("select 1"))
