from grpc import ServicerContext, StatusCode

import conversation_pb2 as conv_pb2
import conversation_pb2_grpc as conv_pb2_grpc
from config import SERVER_NAME
from db.db_helper import DbHelper
from db.models.user import User
from db.models.conversation import Conversation

class ConversationService(conv_pb2_grpc.ConversationServiceServicer):

    def __init__(self, db_helper: DbHelper):
        self.db_helper = db_helper

    def CreateConversation(self, request: conv_pb2.CreateConversationRequest, context: ServicerContext) -> conv_pb2.ConversationReply:
        if not self.db_helper.verify_access_token_and_get_user(context.invocation_metadata()):
            context.abort(code=StatusCode.UNAUTHENTICATED, details="Invalid access token")

        reply = conv_pb2.ConversationReply(name=request.name)
        try:
            members: list[User] = []
            for id in request.member_ids:
                if '@' not in id:
                    id = f'{id}@{SERVER_NAME}'
                username, server = id.split("@")
                member = self.db_helper.get_user(username, server)
                members.append(member)
            
            conversation = self.db_helper.add_conversation(request.name)

            for member in members:
                self.db_helper.add_conversation_member(conversation, member)

            reply.id = conversation.id
        except Exception as e:
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
            else:
                context.abort(code=StatusCode.ABORTED, details="Error while getting conversations")
        except Exception as e:
            message = f'Error while getting conversations: {str(e)}'
            print(message)
            context.abort(code=StatusCode.ABORTED, details=message)

        return reply