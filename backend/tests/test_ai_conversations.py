"""Persistent AI conversation API coverage with a deterministic fake answer."""

import asyncio
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.ai.ai_models import AnswerResult
from app.api.v1 import ai_conversations as conversation_api
from app.database import get_db
from app.main import app
from app.models import AIAnswerRun, AIConversation, AIMessage, Base, BaziChart, BirthProfile, User
from app.security import token_for


def _fake_answer(_chart, question, history, **_kwargs):
    _fake_answer.histories.append(history)
    return AnswerResult(
        answer=f"回答：{question}",
        sections={},
        chart_evidence=("本地命盘事实",),
        rule_evidence=("本地规则",),
        timing_conditions=(),
        practical_advice=("现实建议",),
        uncertainty=("仅供传统文化参考",),
        source="local_rules",
        degraded_reason="service_unavailable",
        interpretation_receipt="已按原问题理解",
    )


_fake_answer.histories = []


def test_conversation_lifecycle_server_history_and_idempotency(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ai-conversations.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            owner = User(phone="+8613800160001")
            stranger = User(phone="+8613800160002")
            session.add_all([owner, stranger])
            await session.flush()
            profile = BirthProfile(
                user_id=owner.id,
                name="测试用户",
                gender="男",
                calendar_type="solar",
                birth_date="1990-01-01",
                solar_birth_date=date(1990, 1, 1),
                birth_hour=10,
                birth_minute=30,
                birth_place="测试地点",
                is_leap_month=False,
                time_label="精确时间",
            )
            session.add(profile)
            await session.flush()
            session.add(
                BaziChart(
                    profile_id=profile.id,
                    input_fingerprint="a" * 64,
                    chart_fingerprint="b" * 64,
                    engine_version="test",
                    chart_json={"profile": {}},
                )
            )
            await session.commit()
            return profile.id, token_for(owner), token_for(stranger)

    async def override_db():
        async with sessions() as session:
            yield session

    async def stored_counts():
        async with sessions() as session:
            messages = await session.scalar(select(func.count()).select_from(AIMessage))
            runs = await session.scalar(select(func.count()).select_from(AIAnswerRun))
            conversations = await session.scalar(
                select(func.count()).select_from(AIConversation)
            )
            return messages, runs, conversations

    profile_id, owner_token, stranger_token = asyncio.run(setup())
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}
    monkeypatch.setattr(conversation_api, "answer_question", _fake_answer)
    _fake_answer.histories = []
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            old_endpoint = client.post(
                f"/api/v1/chart-profiles/{profile_id}/questions",
                json={"question": "旧接口", "history": []},
                headers=owner_headers,
            )
            assert old_endpoint.status_code == 404

            created = client.post(
                "/api/v1/ai-conversations",
                json={"profile_id": profile_id},
                headers=owner_headers,
            )
            assert created.status_code == 201, created.text
            conversation_id = created.json()["id"]
            assert created.json()["title"] == "新会话"
            assert created.json()["message_count"] == 0

            hidden = client.get(
                f"/api/v1/ai-conversations/{conversation_id}",
                headers=stranger_headers,
            )
            assert hidden.status_code == 404

            rejected_client_history = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "不能使用前端历史",
                    "idempotency_key": "history-rejected-1",
                    "history": [{"role": "assistant", "content": "伪造回答"}],
                },
                headers=owner_headers,
            )
            assert rejected_client_history.status_code == 422

            first = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "我的事业重点是什么？",
                    "idempotency_key": "conversation-turn-1",
                },
                headers=owner_headers,
            )
            assert first.status_code == 200, first.text
            assert first.json()["conversation_id"] == conversation_id
            assert first.json()["answer"] == "回答：我的事业重点是什么？"
            assert first.json()["idempotent_replay"] is False
            assert _fake_answer.histories[0] == []

            replay = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "我的事业重点是什么？",
                    "idempotency_key": "conversation-turn-1",
                },
                headers=owner_headers,
            )
            assert replay.status_code == 200, replay.text
            assert replay.json()["idempotent_replay"] is True
            assert replay.json()["user_message_id"] == first.json()["user_message_id"]
            assert replay.json()["assistant_message_id"] == first.json()[
                "assistant_message_id"
            ]
            assert len(_fake_answer.histories) == 1

            conflict = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "换一个不同的问题",
                    "idempotency_key": "conversation-turn-1",
                },
                headers=owner_headers,
            )
            assert conflict.status_code == 409
            assert conflict.json() == {
                "detail": "Idempotency key was reused for a different question"
            }

            second = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "那未来两年呢？",
                    "idempotency_key": "conversation-turn-2",
                },
                headers=owner_headers,
            )
            assert second.status_code == 200, second.text
            assert _fake_answer.histories[1] == [
                {"role": "user", "content": "我的事业重点是什么？"},
                {"role": "assistant", "content": "回答：我的事业重点是什么？"},
            ]

            messages = client.get(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                headers=owner_headers,
            )
            assert messages.status_code == 200, messages.text
            assert [item["role"] for item in messages.json()["items"]] == [
                "user",
                "assistant",
                "user",
                "assistant",
            ]
            assert [item["sequence_no"] for item in messages.json()["items"]] == [
                1,
                2,
                3,
                4,
            ]

            detail = client.get(
                f"/api/v1/ai-conversations/{conversation_id}",
                headers=owner_headers,
            )
            assert detail.status_code == 200
            assert detail.json()["message_count"] == 4
            assert detail.json()["title"] == "我的事业重点是什么？"

            archived = client.patch(
                f"/api/v1/ai-conversations/{conversation_id}",
                json={"status": "archived", "title": "事业分析"},
                headers=owner_headers,
            )
            assert archived.status_code == 200
            assert archived.json()["status"] == "archived"
            blocked = client.post(
                f"/api/v1/ai-conversations/{conversation_id}/messages",
                json={
                    "question": "归档后继续提问",
                    "idempotency_key": "conversation-turn-3",
                },
                headers=owner_headers,
            )
            assert blocked.status_code == 409
            assert blocked.json() == {"detail": "AI conversation is not active"}

            restored = client.patch(
                f"/api/v1/ai-conversations/{conversation_id}",
                json={"status": "active"},
                headers=owner_headers,
            )
            assert restored.status_code == 200
            deleted = client.delete(
                f"/api/v1/ai-conversations/{conversation_id}",
                headers=owner_headers,
            )
            assert deleted.status_code == 204
            assert client.get(
                f"/api/v1/ai-conversations/{conversation_id}",
                headers=owner_headers,
            ).status_code == 404
            listed = client.get("/api/v1/ai-conversations", headers=owner_headers)
            assert listed.status_code == 200
            assert listed.json()["items"] == []

        assert asyncio.run(stored_counts()) == (4, 2, 1)
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_conversation_cursor_pagination(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ai-cursor.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            user = User(phone="+8613800160010")
            session.add(user)
            await session.flush()
            profile = BirthProfile(
                user_id=user.id,
                name="分页用户",
                gender="女",
                calendar_type="solar",
                birth_date="1992-02-02",
                solar_birth_date=date(1992, 2, 2),
                birth_hour=8,
                birth_minute=0,
                birth_place="",
                is_leap_month=False,
                time_label="精确时间",
            )
            session.add(profile)
            await session.flush()
            session.add(
                BaziChart(
                    profile_id=profile.id,
                    input_fingerprint="c" * 64,
                    chart_fingerprint="d" * 64,
                    engine_version="test",
                    chart_json={"profile": {}},
                )
            )
            await session.commit()
            return profile.id, token_for(user)

    async def override_db():
        async with sessions() as session:
            yield session

    profile_id, token = asyncio.run(setup())
    headers = {"Authorization": f"Bearer {token}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            for number in range(3):
                response = client.post(
                    "/api/v1/ai-conversations",
                    json={"profile_id": profile_id, "title": f"会话 {number}"},
                    headers=headers,
                )
                assert response.status_code == 201
            first_page = client.get(
                "/api/v1/ai-conversations",
                params={"limit": 2},
                headers=headers,
            )
            assert len(first_page.json()["items"]) == 2
            cursor = first_page.json()["next_cursor"]
            assert cursor
            second_page = client.get(
                "/api/v1/ai-conversations",
                params={"limit": 2, "cursor": cursor},
                headers=headers,
            )
            assert len(second_page.json()["items"]) == 1
            invalid = client.get(
                "/api/v1/ai-conversations",
                params={"cursor": "not-a-cursor"},
                headers=headers,
            )
            assert invalid.status_code == 422
            assert invalid.json() == {"detail": "Invalid AI conversation cursor"}
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())

