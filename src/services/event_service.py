import time

from grpc import ServicerContext, StatusCode, insecure_channel

import event_pb2
import event_pb2_grpc
from db.db_helper import DbHelper
from db.redis_helper import RedisHelper
from db.models.conversation import Conversation
from config import SERVER_NAME


class EventService(event_pb2_grpc.EventServiceServicer):

    def __init__(self, db_helper: DbHelper, redis_helper: RedisHelper):
        self.db_helper = db_helper
        self.redis_helper = redis_helper

    def __make_create_event_call(self, stub: event_pb2_grpc.EventServiceStub, request: event_pb2.CreateEventRequest, user_id: str, conversation_id: int) -> event_pb2.Event:
        reply: event_pb2.Event = None
        try:
            metadata = [(b'federated_user', user_id.encode()), (b'conversation_id', str(conversation_id).encode())]
            reply = stub.CreateEvent(request, metadata=metadata)
        except Exception as e:
            raise e
        return reply

    def CreateEvent(self, request: event_pb2.CreateEventRequest, context: ServicerContext) -> event_pb2.Event:
        print(context.invocation_metadata())
        federated_user = None
        fed_conv_id = None
        user = None
        for item in context.invocation_metadata():
            if item.key == 'federated_user':
                federated_user = item.value
                username, server = federated_user.split('@')
                user = self.db_helper.get_user(username, server)
                print(user.id)
                print("Found federated user")
            elif item.key == 'conversation_id':
                fed_conv_id = int(item.value)


        if not user:
            if not (user := self.db_helper.verify_access_token_and_get_user(context.invocation_metadata())):
                context.abort(code=StatusCode.UNAUTHENTICATED, details="Access denied")

        reply = event_pb2.Event(
            user_id=f"{user.username}@{user.server}",
            user_display_name=user.display_name,
            conversation_id=request.conversation_id,
            type=request.type,
            content=request.content,
            previous_event_id=request.previous_event_id
        )
        
        try:
            conversation = self.db_helper.get_conversation(request.conversation_id, load_relation=True)
            print(f"Found conversation {conversation.id}")
            event = self.db_helper.add_event(user, conversation, request.content, request.type, request.previous_event_id)
            reply.timestamp = int(event.timestamp)
            reply.id = event.id

            fed_servers = set()

            for member in conversation.members:
                if member.user.server == SERVER_NAME:
                    user_id = f"{member.user.username}@{SERVER_NAME}"
                    self.redis_helper.push_event(user_id, reply)
                else:
                    fed_servers.add(member.user.server)
            
            for server in fed_servers:
                mapping = self.db_helper.get_fed_conv_mappings(conversation.id, server)
                print(f"Found mapping with fed {mapping.fed_conv_id}")
                if mapping and mapping.fed_conv_id != fed_conv_id:
                    channel = insecure_channel(server)
                    stub = event_pb2_grpc.EventServiceStub(channel)
                    request.conversation_id = mapping.fed_conv_id
                    self.__make_create_event_call(stub, request, user_id, conversation.id)
                    
        except Exception as e:
            raise
            message = f'Error while creating event: {str(e)}'
            print(message)
            context.abort(code=StatusCode.ABORTED, details=message)

        return reply
    
    def GetEvents(self, request: event_pb2.GetEventsRequest, context: ServicerContext) -> event_pb2.GetEventsReply:
        if not (user := self.db_helper.verify_access_token_and_get_user(context.invocation_metadata())):
            context.abort(code=StatusCode.UNAUTHENTICATED, details="Invalid access token")

        reply = event_pb2.GetEventsReply()

        try:
            conversation: Conversation = self.db_helper.get_conversation(request.conversation_id)
            for event in conversation.events:
                reply.events.append(event_pb2.Event(
                    id=event.id,
                    user_id=f"{event.user.username}@{event.user.server}",
                    user_display_name=event.user.display_name,
                    conversation_id=conversation.id,
                    type=event.type,
                    content=event.content,
                    previous_event_id=event.previous_event_id,
                    timestamp=event.timestamp
                ))
        except Exception as e:
            message = f'Error while getting events: {str(e)}'
            print(message)
            context.abort(code=StatusCode.ABORTED, details=message)

        return reply
    
    def StreamEvents(self, request: event_pb2.EmptyRequest, context: ServicerContext):
        if not (user := self.db_helper.verify_access_token_and_get_user(context.invocation_metadata())):
            context.abort(code=StatusCode.UNAUTHENTICATED, details="Invalid access token")
        
        user_id = f"{user.username}@{user.server}"
        uuid = self.redis_helper.start_channel(user_id)

        def stream_ended():
            print("Stream end")
            self.redis_helper.stop_channel(user_id, uuid)

        
        context.add_callback(stream_ended)

        while True:
            event = self.redis_helper.pop_event(uuid)
            if (time.time() - event.timestamp) <= 10:
                yield event
            continue
