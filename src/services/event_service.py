import time

from grpc import ServicerContext, StatusCode

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

    def CreateEvent(self, request: event_pb2.CreateEventRequest, context: ServicerContext) -> event_pb2.Event:
        if not (user := self.db_helper.verify_access_token_and_get_user(context.invocation_metadata())):
            context.abort(code=StatusCode.UNAUTHENTICATED, details="Invalid access token")

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
            event = self.db_helper.add_event(user, conversation, request.content, request.type, request.previous_event_id)
            reply.timestamp = int(event.timestamp)
            reply.id = event.id

            for member in conversation.members:
                if member.user.server == SERVER_NAME:
                    user_id = f"{member.user.username}@{SERVER_NAME}"
                    self.redis_helper.push_event(user_id, reply)
        except Exception as e:
            raise e
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
