from __future__ import annotations

from sqlalchemy import Column, String

from db.models.base import Base

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    password = Column(String, primary_key=True)
    server = Column(String(100))
    display_name = Column(String)
