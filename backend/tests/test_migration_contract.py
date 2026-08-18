from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

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
