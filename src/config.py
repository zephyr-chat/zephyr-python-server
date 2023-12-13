import os

SECRET_KEY = os.environ.get("ZEPHYR_SERVER_KEY", "secret_key")

SQLALCHEMY_URL = os.environ.get("ZEPHYR_DB_URL", "sqlite:///db.sqlite3")

SERVER_HOST = os.environ.get("ZEPHYR_SERVER_HOST", "localhost")
SERVER_PORT = os.environ.get("ZEPHYR_SERVER_PORT", "50051")
