from time import time

import jwt
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from config import *
from db.models.user import User
from db.models.conversation import Conversation, ConversationMember, FederatedConversationMapping
from db.models.event import Event

ENCODING = 'utf-8'

class DbHelper:
    
    def __init__(self):
        db_engine = create_engine(SQLALCHEMY_URL)
        self.session_factory = sessionmaker(bind=db_engine)

    @classmethod
    def __get_password_hash(cls, password: str) -> str:
        return bcrypt.hashpw(
            password.encode(ENCODING), bcrypt.gensalt()
        ).decode(ENCODING)

    @classmethod
    def __check_password_hash(cls, password: str, hash: str) -> bool:
        return bcrypt.checkpw(
            password.encode(ENCODING), hash.encode(ENCODING)) 

    def add_user(self, username: str, password: str, display_name: str, server: str=SERVER_NAME) -> str:
        session = self.session_factory()
        user = User(
            username=username, 
            password=self.__get_password_hash(password), 
            server=server, 
            display_name=display_name)
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as e:
            session.rollback()
            raise e
        return user.id
        
    def get_user(self, username: str, server: str) -> User | None:
        session = self.session_factory()
        user = None
        try:
            user = session.query(User).filter_by(username=username, server=server).first()
        except Exception as e:
            print(f"Error occured while getting user {str(e)}")
        return user
        
    def verify_password_and_get_user(self, username: str, password: str) -> User | None:
        user = None
        try:
            user = self.get_user(username, SERVER_NAME)
            if user and not self.__check_password_hash(password, user.password):
                user = None
        except Exception as e:
            raise e
        return user
    
    def __verify_jwt_token(self, token: str) -> User:
        user = None
        try:
            decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_SIGNING_ALGORITHM])
            username = decoded_payload['user_id'].split("@")[0]
            user = self.get_user(username, SERVER_NAME)
        except Exception as e:
            print(f"Error validating JWT token: {str(e)}")
        
        return user
    
    def verify_access_token_and_get_user(self, metadata: tuple) -> User | None:
        access_token = None
        user = None
        for item in metadata:
            if item.key == "authorization":
                access_token = item.value
                break
        if access_token:
            user = self.__verify_jwt_token(access_token)
        return user
    
    def add_conversation(self, name: str) -> Conversation:
        conversation = Conversation(name=name)
        session = self.session_factory()
        try:
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        except Exception as e:
            session.rollback()
            raise e
        return conversation
    
    def get_conversation(self, id: str, load_relation = False) -> Conversation:
        session = self.session_factory()
        conversation = None
        try:
            if load_relation:
                conversation = session.query(Conversation).filter_by(id=id).options(
                    joinedload('*')).first()
            else:
                conversation = session.query(Conversation).filter_by(id=id).first()
        except Exception as e:
            raise e
        return conversation
    
    def get_conversations(self, user_id: str) -> list[Conversation]:
        session = self.session_factory()
        conversations = None
        try:
            conversations = session.query(Conversation).join(ConversationMember).filter(
                ConversationMember.user_id == user_id).all()
        except Exception as e:
            raise e
        return conversations
        
    def add_conversation_member(self, conversation: Conversation, member: User):
        conversation_member = ConversationMember(
            conversation_id=conversation.id,
            user_id=member.id
        )
        session = self.session_factory()
        try:
            session.add(conversation_member)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        
    def add_event(self, user: User, conversation: Conversation, content: str, type: int, previous_event_id: int) -> Event:
        event = Event(
            user_id=user.id,
            conversation_id=conversation.id,
            type=type,
            content=content,
            previous_event_id=previous_event_id,
            timestamp=int(time())
        )
        session = self.session_factory()
        try:
            session.add(event)
            session.commit()
            session.refresh(event)
        except Exception as e:
            session.rollback()
            raise e
        return event
    
    def add_fed_conv_mapping(self, conversation_id: str, fed_conv_id: str) -> FederatedConversationMapping:
        mapping = FederatedConversationMapping(conversation_id=conversation_id, fed_conv_id=fed_conv_id)
        session = self.session_factory()
        try:
            session.add(mapping)
            session.commit()
            session.refresh(mapping)
        except Exception as e:
            session.rollback()
            raise e
        return mapping