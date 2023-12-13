from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.models.base import Base

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User")
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    type = Column(Integer)
    content = Column(String)
    previous_event_id = Column(Integer)
    timestamp = Column(Integer)
