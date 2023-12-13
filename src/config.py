import os

SECRET_KEY = os.environ.get("ZEPHYR_SERVER_KEY", "secret_key")

SQLALCHEMY_URL = os.environ.get("ZEPHYR_DB_URL", "sqlite:///db.sqlite3")

SERVER_HOST = os.environ.get("ZEPHYR_SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("ZEPHYR_SERVER_PORT", "50051")
SERVER_NAME = f"{SERVER_HOST}:{SERVER_PORT}"

JWT_SIGNING_ALGORITHM = 'HS256'

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
