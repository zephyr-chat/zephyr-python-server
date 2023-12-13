from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict

import jwt
from grpc import ServicerContext, StatusCode

import auth_pb2
import auth_pb2_grpc
from db.db_helper import DbHelper
from db.models.user import User
from config import *

@dataclass
class JwtTokenPayload:
    user_id: str
    exp: str

    dict = asdict

class AuthService(auth_pb2_grpc.AuthServiceServicer):

    def __init__(self, db_helper: DbHelper):
        self.db_helper = db_helper

    def RegisterUser(self, request: auth_pb2.RegisterUserRequest, context: ServicerContext) -> auth_pb2.RegisterUserResponse:
        print(f"Trying to register user: {request.username}")
        try:
            self.db_helper.add_user(
                username=request.username, 
                password=request.password, 
                display_name=request.display_name)
        except Exception as e:
            print(f"Error occured while registering user: {str(e)}")
            context.abort(code=StatusCode.ALREADY_EXISTS, details='Username already exists')
        return auth_pb2.RegisterUserResponse(
            user_id=f"{request.username}@{SERVER_NAME}",
            display_name=request.display_name
        )
    
    def __generate_jwt_token(self, username: str) -> str:
        payload = JwtTokenPayload(
            user_id=f"{username}@{SERVER_NAME}", 
            exp=datetime.now(tz=timezone.utc) + timedelta(weeks=1))
        token = jwt.encode(payload.dict(), SECRET_KEY, algorithm=JWT_SIGNING_ALGORITHM)
        return token
    
    def Authenticate(self, request: auth_pb2.AuthRequest, context: ServicerContext) -> auth_pb2.AuthResponse:
        print(f"Trying to authenticate user: {request.username}")
        reply = auth_pb2.AuthResponse()
        try:
            user = self.db_helper.verify_password_and_get_user(username=request.username, password=request.password)
            if not user:
                context.abort(code=StatusCode.PERMISSION_DENIED, details='Invalid credentials')
            
            reply.access_token = self.__generate_jwt_token(request.username)
        except Exception as e:
            print(f"Error occured while authenticating user: {str(e)}")
            context.abort(code=StatusCode.ABORTED, details='Error occured while authentication')
        
        return reply
    