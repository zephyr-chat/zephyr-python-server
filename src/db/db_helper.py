import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_URL, SERVER_HOST, SERVER_PORT
from db.models.user import User

ENCODING = 'utf-8'
SERVER_NAME = f"{SERVER_HOST}:{SERVER_PORT}"

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

    def add_user(self, username: str, password: str, display_name: str):
        session = self.session_factory()
        user = User(
            username=username, 
            password=self.__get_password_hash(password), 
            server=SERVER_NAME, 
            display_name=display_name)
        try:
            session.add(user)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        
    def verify_password_and_get_user(self, username: str, password: str) -> User | None:
        session = self.session_factory()
        try:
            user = session.query(User).filter_by(username=username, server=SERVER_NAME).first()
            if not self.__check_password_hash(password, user.password):
                return None
        except Exception as e:
            raise e
        return user
