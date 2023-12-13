from concurrent import futures

import grpc

import auth_pb2_grpc
from config import SERVER_PORT
from services.auth_service import AuthService
from db.db_helper import DbHelper

if __name__ == '__main__':
    db_helper = DbHelper()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(db_helper), server)
    server.add_insecure_port(f'[::]:{SERVER_PORT}')
    server.start()
    server.wait_for_termination()
