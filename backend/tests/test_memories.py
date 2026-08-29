import asyncio
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base, MemoryEntry, User
from app.security import token_for


def test_memory_archive_crud_filters_overview_and_ownership(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'memories.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            owner = User(phone="+8613900002001")
            stranger = User(phone="+8613900002002")
            session.add_all([owner, stranger])
            await session.commit()
            await session.refresh(owner)
            await session.refresh(stranger)
            return token_for(owner), token_for(stranger)

    async def add_feedback(memory_id: str):
        async with sessions() as session:
            entry = await session.get(MemoryEntry, memory_id)
            assert entry is not None
            entry.feedback = "AI 已在职业建议中引用这条记忆。"
            entry.ai_use_count = 1
            await session.commit()

    async def override_db():
        async with sessions() as session:
            yield session

    owner_token, stranger_token = asyncio.run(setup())
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/memories").status_code == 401

            empty = client.get("/api/v1/memories/overview", headers=owner_headers)
            assert empty.status_code == 200
            assert empty.json()["total_memories"] == 0
            assert len(empty.json()["categories"]) == 8
            assert empty.json()["focus_tags"] == []

            career = client.post(
                "/api/v1/memories",
                headers=owner_headers,
                json={
                    "title": "  准备启动咖啡项目  ",
                    "category": "职业事业",
                    "content": "  正在验证产品定位和启动预算。  ",
                    "occurred_on": "2026-08-20",
                },
            )
            assert career.status_code == 201, career.text
            career_body = career.json()
            assert career_body["title"] == "准备启动咖啡项目"
            assert career_body["content"] == "正在验证产品定位和启动预算。"
            assert career_body["occurred_on"] == "2026-08-20"
            assert career_body["source"] == "manual"
            assert career_body["deletable"] is True
            assert career_body["created_at"].endswith(("Z", "+00:00"))
            assert career_body["updated_at"].endswith(("Z", "+00:00"))
            career_id = career_body["id"]

            goal = client.post(
                "/api/v1/memories",
                headers=owner_headers,
                json={
                    "title": "提升表达能力",
                    "category": "目标愿望",
                    "content": "希望三个月内完成一次公开分享。",
                    "occurred_on": "2026-08-21",
                    "is_timeline_event": False,
                },
            )
            assert goal.status_code == 201, goal.text
            goal_id = goal.json()["id"]

            person = client.post(
                "/api/v1/memories",
                headers=owner_headers,
                json={
                    "title": "认识行业前辈",
                    "category": "重要人物",
                    "content": "希望持续交流品牌经营经验。",
                    "occurred_on": "2026-08-22",
                },
            )
            assert person.status_code == 201, person.text

            invalid_category = client.post(
                "/api/v1/memories",
                headers=owner_headers,
                json={"title": "无效", "category": "未知分类", "content": "内容"},
            )
            assert invalid_category.status_code == 422
            assert client.post(
                "/api/v1/memories",
                headers=owner_headers,
                json={"title": "  ", "category": "基本信息", "content": "内容"},
            ).status_code == 422

            listed = client.get("/api/v1/memories", headers=owner_headers)
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [
                person.json()["id"],
                goal_id,
                career_id,
            ]

            goals = client.get(
                "/api/v1/memories?category=目标愿望", headers=owner_headers
            )
            assert [item["id"] for item in goals.json()] == [goal_id]
            searched = client.get(
                "/api/v1/memories?search=咖啡", headers=owner_headers
            )
            assert [item["id"] for item in searched.json()] == [career_id]
            timeline = client.get(
                "/api/v1/memories?timeline_only=true", headers=owner_headers
            )
            assert {item["id"] for item in timeline.json()} == {
                career_id,
                person.json()["id"],
            }

            overview = client.get("/api/v1/memories/overview", headers=owner_headers)
            assert overview.status_code == 200
            overview_body = overview.json()
            assert overview_body["total_memories"] == 3
            assert overview_body["goal_count"] == 1
            assert overview_body["important_people_count"] == 1
            assert overview_body["life_event_count"] == 2
            assert overview_body["feedback_count"] == 0
            assert overview_body["latest_updated_at"] is not None
            assert overview_body["latest_updated_at"].endswith(("Z", "+00:00"))
            category_counts = {
                item["category"]: item["count"] for item in overview_body["categories"]
            }
            assert category_counts["职业事业"] == 1
            assert category_counts["目标愿望"] == 1
            assert category_counts["重要人物"] == 1

            detail = client.get(f"/api/v1/memories/{career_id}", headers=owner_headers)
            assert detail.status_code == 200
            assert detail.json()["title"] == "准备启动咖啡项目"
            hidden = client.get(
                f"/api/v1/memories/{career_id}", headers=stranger_headers
            )
            assert hidden.status_code == 404
            assert hidden.json() == {"detail": "Memory entry not found"}

            asyncio.run(add_feedback(career_id))
            feedback = client.get(
                "/api/v1/memories?has_feedback=true", headers=owner_headers
            )
            assert [item["id"] for item in feedback.json()] == [career_id]
            assert feedback.json()[0]["ai_use_count"] == 1
            assert client.get(
                "/api/v1/memories/overview", headers=owner_headers
            ).json()["feedback_count"] == 1

            assert client.delete(
                f"/api/v1/memories/{goal_id}", headers=stranger_headers
            ).status_code == 404
            deleted = client.delete(
                f"/api/v1/memories/{goal_id}", headers=owner_headers
            )
            assert deleted.status_code == 204
            assert deleted.content == b""
            assert client.get(
                f"/api/v1/memories/{goal_id}", headers=owner_headers
            ).status_code == 404
            assert client.delete(
                f"/api/v1/memories/{goal_id}", headers=owner_headers
            ).status_code == 404
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_memory_create_uses_server_date_when_omitted(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'memory-date.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            user = User(phone="+8613900002003")
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return token_for(user)

    async def override_db():
        async with sessions() as session:
            yield session

    headers = {"Authorization": f"Bearer {asyncio.run(setup())}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/memories",
                headers=headers,
                json={
                    "title": "今天的记录",
                    "category": "其他记忆",
                    "content": "未显式填写发生日期。",
                },
            )
            assert created.status_code == 201, created.text
            assert date.fromisoformat(created.json()["occurred_on"])
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
