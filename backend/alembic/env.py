from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from alembic import context
from app.config import settings
from app.models import Base

config = context.config
# The API uses an async DB driver, while Alembic deliberately runs through a
# synchronous driver. Escaping percent signs is required by ConfigParser when
# credentials contain URL-encoded characters such as ``%40``.
database_url = make_url(settings.database_url)
sync_drivers = {
    "mysql+asyncmy": "mysql+pymysql",
    "sqlite+aiosqlite": "sqlite",
}
database_url = database_url.set(
    drivername=sync_drivers.get(database_url.drivername, database_url.drivername)
)
config.set_main_option(
    "sqlalchemy.url",
    database_url.render_as_string(hide_password=False).replace("%", "%%"),
)
target_metadata = Base.metadata


def get_sqlalchemy_url() -> str:
    """Return Alembic's configured database URL or fail with a clear error."""
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    if not sqlalchemy_url:
        raise RuntimeError("Alembic sqlalchemy.url is not configured")
    return sqlalchemy_url


def run_migrations_offline():
    context.configure(
        url=get_sqlalchemy_url(),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(get_sqlalchemy_url(), pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
