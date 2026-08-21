import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base, FeatureRule, User
from app.services import consume, credit


@pytest.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_ledger_idempotency_and_no_overdraft(db):
    user = User(phone="+8613800138000")
    db.add(user)
    await db.flush()
    first = await credit(db, user.id, 10, "bonus", "bonus:1")
    duplicate = await credit(db, user.id, 10, "bonus", "bonus:1")
    assert first.id == duplicate.id and first.balance_after == 10
    db.add(FeatureRule(feature_code="report", points_cost=3))
    await db.flush()
    spent = await consume(db, user.id, "report", "use:1")
    again = await consume(db, user.id, "report", "use:1")
    assert spent.id == again.id and spent.balance_after == 7


@pytest.mark.asyncio
async def test_idempotency_key_is_scoped_to_user(db):
    first, second = User(phone="+8613800138001"), User(phone="+8613800138002")
    db.add_all([first, second])
    await db.flush()
    a = await credit(db, first.id, 5, "bonus", "shared-client-key")
    b = await credit(db, second.id, 8, "bonus", "shared-client-key")
    assert a.user_id != b.user_id
    assert a.balance_after == 5 and b.balance_after == 8
