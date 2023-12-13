import uuid

from sqlalchemy import Column, String

from db.models.base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    server = Column(String(100))
    display_name = Column(String)
