"""Create first-run production and SSH-tunnel environment files.

Run this only on the target server. Existing files are never overwritten.
Generated secrets are intentionally not printed.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

# By default the files are created in the current deployment directory. Set
# MINGSHU_DEPLOY_DIR when the script is invoked from somewhere else.
TARGET_DIR = Path(os.environ.get("MINGSHU_DEPLOY_DIR", ".")).expanduser().resolve()
PRODUCTION_ENV = TARGET_DIR / ".env"
LOCAL_CLIENT_ENV = TARGET_DIR / ".env.local-client"


def _write_private(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def main() -> None:
    if PRODUCTION_ENV.exists() or LOCAL_CLIENT_ENV.exists():
        raise SystemExit("Refusing to overwrite an existing environment file")

    mysql_password = secrets.token_hex(32)
    mysql_root_password = secrets.token_hex(32)
    redis_password = secrets.token_hex(32)
    jwt_secret = secrets.token_hex(48)

    production = f"""ENVIRONMENT=production
DATABASE_URL=mysql+asyncmy://mingshu:{mysql_password}@mysql:3306/mingshu?charset=utf8mb4
MYSQL_DATABASE=mingshu
MYSQL_USER=mingshu
MYSQL_PASSWORD={mysql_password}
MYSQL_ROOT_PASSWORD={mysql_root_password}
MYSQL_HOST_PORT=3306
REDIS_PASSWORD={redis_password}
REDIS_URL=redis://:{redis_password}@redis:6379/0
REDIS_HOST_PORT=6379
JWT_SECRET={jwt_secret}
JWT_ISSUER=mingshu-api
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=30
REGISTRATION_BONUS_POINTS=20
OTP_TTL_SECONDS=300
OTP_RESEND_SECONDS=60
OTP_DAILY_LIMIT=10
OTP_MAX_ATTEMPTS=5
CORS_ORIGINS=[]
API_BIND_ADDRESS=127.0.0.1
API_PORT=8000
PIP_INDEX_URL=https://pypi.org/simple
WECHAT_APP_ID=
WECHAT_APP_SECRET=
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
"""
    local_client = f"""ENVIRONMENT=development
DATABASE_URL=mysql+asyncmy://mingshu:{mysql_password}@127.0.0.1:13306/mingshu?charset=utf8mb4
REDIS_URL=redis://:{redis_password}@127.0.0.1:16379/0
JWT_SECRET=local-development-only-change-before-production-2026
JWT_ISSUER=mingshu-api
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=30
REGISTRATION_BONUS_POINTS=20
OTP_TTL_SECONDS=300
OTP_RESEND_SECONDS=60
OTP_DAILY_LIMIT=10
OTP_MAX_ATTEMPTS=5
CORS_ORIGINS=["http://localhost:3000"]
WECHAT_APP_ID=
WECHAT_APP_SECRET=
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
"""

    TARGET_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    _write_private(PRODUCTION_ENV, production)
    _write_private(LOCAL_CLIENT_ENV, local_client)


if __name__ == "__main__":
    main()
