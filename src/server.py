from concurrent import futures

import grpc

import auth_pb2_grpc
import conversation_pb2_grpc
import event_pb2_grpc
from config import SERVER_PORT
from services.auth_service import AuthService
from services.conversation_service import ConversationService
from services.event_service import EventService
from db.db_helper import DbHelper

if __name__ == '__main__':
    db_helper = DbHelper()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(db_helper), server)
    conversation_pb2_grpc.add_ConversationServiceServicer_to_server(ConversationService(db_helper), server)
    event_pb2_grpc.add_EventServiceServicer_to_server(EventService(db_helper), server)
    server.add_insecure_port(f'[::]:{SERVER_PORT}')
    server.start()
    server.wait_for_termination()
