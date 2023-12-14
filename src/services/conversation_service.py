from grpc import ServicerContext, StatusCode, insecure_channel
from google.protobuf.json_format import MessageToJson

import auth_pb2
import auth_pb2_grpc
import conversation_pb2 as conv_pb2
import conversation_pb2_grpc as conv_pb2_grpc
from config import SERVER_NAME
from db.db_helper import DbHelper
from db.models.user import User
from db.models.conversation import Conversation

class ConversationService(conv_pb2_grpc.ConversationServiceServicer):

    def __init__(self, db_helper: DbHelper):
        self.db_helper = db_helper

    def __make_get_user_call(self, stub: auth_pb2_grpc.AuthServiceStub, user_id: str):
        user = None
        try:
            request = auth_pb2.GetUserDetailsRequest(user_id=user_id)
            reply: auth_pb2.UserResponse = stub.GetUserDetails(request)
            username, server = reply.user_id.split("@")
            id = self.db_helper.add_user(username, "", reply.display_name, server)
            user = User(id=id, username=username, password="", server=server, display_name=reply.display_name)
        except Exception as e:
            raise e
        return user
    
    def __make_create_conversation_call(self, stub: conv_pb2_grpc.ConversationServiceStub, request: conv_pb2.CreateConversationRequest, conversation_id: int) -> conv_pb2.ConversationReply:
        reply: conv_pb2.ConversationReply = None
        try:
            metadata = [(b'parent_conv_id', str(conversation_id).encode()), (b'parent_server', SERVER_NAME.encode())]
            reply = stub.CreateConversation(request, 10, metadata=metadata)
        except Exception as e:
            raise e
        return reply

    def CreateConversation(self, request: conv_pb2.CreateConversationRequest, context: ServicerContext) -> conv_pb2.ConversationReply:
        print(f"Trying to create conversation {request.name}")
        print(MessageToJson(request))
        parent_conv_id = None
        parent_server = None
        for item in context.invocation_metadata():
            if item.key == 'parent_conv_id':
                parent_conv_id = int(item.value)
            elif item.key == 'parent_server':
                parent_server = item.value

        reply = conv_pb2.ConversationReply(name=request.name)

        try:
            federated_users = {}
            members = []
            for id in request.member_ids:
                if '@' not in id:
                    id = f"{id}@{SERVER_NAME}"
                username, server = id.split("@")
                user = self.db_helper.get_user(username, server)
                if user is None: 
                    if server != SERVER_NAME:
                        if server in federated_users:
                            federated_users[server].append(id)
                        else:
                            federated_users[server] = [id]
                else:
                    members.append(user)

            for server, user_ids in federated_users.items():
                channel = insecure_channel(server)
                service_stub = auth_pb2_grpc.AuthServiceStub(channel)
                for id in user_ids:
                    user = self.__make_get_user_call(service_stub, id)
                    members.append(user)

            conversation = self.db_helper.add_conversation(request.name)

            for member in members:
                self.db_helper.add_conversation_member(conversation, member)

            if not parent_conv_id:
                fed_servers = set([id.split("@")[1] for id in request.member_ids if '@' in id and id.split("@")[1] != SERVER_NAME])
                for server in fed_servers:
                    channel = insecure_channel(server)
                    stub = conv_pb2_grpc.ConversationServiceStub(channel)
                    fed_reply = self.__make_create_conversation_call(stub, request, conversation.id)
                    self.db_helper.add_fed_conv_mapping(conversation.id, server, fed_reply.id)
            else:
                self.db_helper.add_fed_conv_mapping(conversation.id, parent_server, parent_conv_id)

            reply.id = conversation.id
        except Exception as e:
            raise e
            message = f'Error while creating conversation: {str(e)}'
            print(message)
            context.abort(code=StatusCode.ABORTED, details=message)
        return reply
    
    def GetConversations(self, request: conv_pb2.Empty, context: ServicerContext) -> conv_pb2.GetConversationsReply:
        if not (user := self.db_helper.verify_access_token_and_get_user(context.invocation_metadata())):
            context.abort(code=StatusCode.UNAUTHENTICATED, details="Invalid access token")

        reply = conv_pb2.GetConversationsReply()
        try:
            conversations: list[Conversation] = self.db_helper.get_conversations(user.id)
            if conversations:
                for conversation in conversations:
                    reply.conversations.append(conv_pb2.ConversationReply(
                        id=conversation.id,
                        name=conversation.name
                    ))
        except Exception as e:
            message = f'Error while getting conversations: {str(e)}'
            print(message)
            context.abort(code=StatusCode.ABORTED, details=message)

        return reply