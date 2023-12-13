from __future__ import annotations
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.models.base import Base

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    members = relationship("ConversationMember")

class ConversationMember(Base):
    __tablename__ = 'conversation_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User")
