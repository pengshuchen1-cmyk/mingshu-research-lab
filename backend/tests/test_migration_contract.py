from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from app.config import BACKEND_DIR, settings
from app.models import Base


def test_initial_migration_matches_model_nullability_and_indexes(tmp_path, monkeypatch):
    database_path = tmp_path / "migration-contract.db"
    sync_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{database_path.as_posix()}")

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")

    inspector = inspect(create_engine(sync_url))
    for table in Base.metadata.sorted_tables:
        reflected_columns = {
            column["name"]: column["nullable"] for column in inspector.get_columns(table.name)
        }
        expected_columns = {column.name: column.nullable for column in table.columns}
        assert reflected_columns == expected_columns

        reflected_indexes = {
            (index["name"], tuple(index["column_names"]), index["unique"])
            for index in inspector.get_indexes(table.name)
        }
        expected_indexes = {
            (index.name, tuple(column.name for column in index.columns), index.unique)
            for index in table.indexes
        }
        assert reflected_indexes == expected_indexes


def test_edit_count_migration_distinguishes_creation_from_real_edit(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "edit-count-migration.db"
    sync_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setattr(
        settings,
        "database_url",
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "0002")

    engine = create_engine(sync_url)
    insert = text(
        "INSERT INTO birth_profiles "
        "(id, user_id, name, gender, calendar_type, birth_date, "
        "solar_birth_date, birth_place, is_leap_month, time_label, "
        "last_edited_at, created_at, updated_at) "
        "VALUES (:id, :user_id, '测试', '男', 'solar', '1996-09-04', "
        "'1996-09-04', '', 0, '精确时间', :last_edited_at, "
        ":created_at, :updated_at)"
    )
    with engine.begin() as connection:
        common = {
            "user_id": "synthetic-user",
            "last_edited_at": "2026-08-20 08:00:00",
            "created_at": "2026-08-20 08:00:00",
        }
        connection.execute(
            insert,
            {**common, "id": "created-only", "updated_at": common["created_at"]},
        )
        connection.execute(
            insert,
            {**common, "id": "actually-edited", "updated_at": "2026-08-21 08:00:00"},
        )

    command.upgrade(config, "head")
    with engine.connect() as connection:
        rows = dict(
            connection.execute(
                text("SELECT id, edit_count FROM birth_profiles ORDER BY id")
            ).all()
        )

    assert rows == {"actually-edited": 1, "created-only": 0}
