import uuid
import json
import redis
from google.protobuf.json_format import MessageToJson, Parse

import event_pb2
from config import *

class RedisHelper:
    def __init__(self) -> None:
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self.client_map = {}

    def start_channel(self, user_id: str) -> str:
        id = str(uuid.uuid4())
        if user_id in self.client_map:
            self.client_map[user_id].append(id)
        else:
            self.client_map[user_id] = [id]
        return id
    
    def stop_channel(self, user_id:str, id: str):
        self.client_map[user_id].remove(id)

    def push_event(self, user_id: str,  event: event_pb2.Event):
        json_string = MessageToJson(event)
        if user_id in self.client_map:
            for channel in self.client_map[user_id]:
                self.redis_client.rpush(channel, json.dumps(json.loads(json_string), separators=[",", ":"]))

    def pop_event(self, channel: str) -> event_pb2.Event:
        event_string = self.redis_client.blpop(channel)[1].decode('utf-8')
        event = Parse(event_string, event_pb2.Event())
        return event
