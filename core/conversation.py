# lugia/core/conversation.py
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json
from typing import List, Optional
from config import Config
from loguru import logger
import boto3
import tiktoken
from botocore.exceptions import ClientError
from cachetools import LRUCache

logger.add(Config.LOG_FILE, rotation="10 MB", compression="zip")

@dataclass
class Message:
    id: str
    role: str
    content: str
    timestamp: str

class ConversationService:
    def __init__(self):
        self.s3_client = self.init_s3_client()
        self.conversation_cache = LRUCache(maxsize=Config.CACHE_SIZE)
        self.active_conversation = None
        self.system_prompt = self.load_system_prompt()

    def init_s3_client(self):
        try:
            s3_client = boto3.client(
                's3',
                region_name='fr-par',
                endpoint_url='https://s3.fr-par.scw.cloud',
                aws_access_key_id=Config.LUGIA_ACCESS_KEY,
                aws_secret_access_key=Config.LUGIA_SECRET_KEY
            )
            return s3_client
        except ClientError as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def load_system_prompt(self) -> str:
        try:
            with open("system_prompt.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            logger.warning("System prompt file not found. Using default prompt.")
            return "You are a Senior Engineer at a major Big Corp."

    def count_tokens(self, text: str) -> int:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))

    async def list_conversations(self) -> List[str]:
        try:
            response = self.s3_client.list_objects_v2(Bucket='lugia', Prefix='conversation_history/')
            conversation_files = [obj['Key'].split('/')[-1] for obj in response.get('Contents', [])]
            return conversation_files
        except ClientError as e:
            logger.error(f"Failed to list conversation files from S3: {e}")
            return []

    async def load_conversation_history(self, conversation_file: str) -> List[Message]:
        try:
            response = self.s3_client.get_object(Bucket='lugia', Key=f'conversation_history/{conversation_file}')
            contents = response['Body'].read().decode('utf-8')
            messages_dict = json.loads(contents)
            messages = [Message(**message_dict) for message_dict in messages_dict]
            return messages
        except ClientError as e:
            logger.warning(f"Failed to load conversation history from S3: {e}")
            return []

    async def save_message(self, conversation_file: str, message: Message):
        try:
            response = self.s3_client.get_object(Bucket='lugia', Key=f'conversation_history/{conversation_file}')
            contents = response['Body'].read().decode('utf-8')
            messages = json.loads(contents)

            message_dict = asdict(message)
            messages.append(message_dict)

            json_string = json.dumps(messages, indent=2)
            self.s3_client.put_object(Bucket='lugia', Key=f'conversation_history/{conversation_file}', Body=json_string)
        except ClientError as e:
            logger.exception(f"Failed to save message to S3: {e}")

    async def create_new_conversation(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_conversation_file = f"conversation_{timestamp}.json"

        try:
            self.s3_client.put_object(Bucket='lugia', Key=f'conversation_history/{new_conversation_file}', Body='[]')
            return new_conversation_file
        except ClientError as e:
            logger.exception(f"Failed to create new conversation file on S3: {e}")
            return None
    
    async def delete_conversation(self, conversation_file: str):
        try:
            # Delete the conversation from S3
            self.s3_client.delete_object(Bucket='lugia', Key=f'conversation_history/{conversation_file}')
            
            # Delete the conversation from the cache and active conversation
            if self.active_conversation == conversation_file:
                self.active_conversation = None
            if conversation_file in self.conversation_cache:
                del self.conversation_cache[conversation_file]
            
            return True
        except ClientError as e:
            logger.exception(f"Failed to delete conversation from S3: {e}")
            return False

    async def switch_conversation(self, conversation_file: str):
        try:
            self.s3_client.head_object(Bucket='lugia', Key=f'conversation_history/{conversation_file}')
            self.conversation_cache.clear()
            return conversation_file
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Conversation file not found on S3: {conversation_file}")
            else:
                logger.exception(f"Failed to switch conversation on S3: {e}")
            return None

    async def add_message(self, role: str, content: str, model_name: str, token_limit: int, conversation_file: str):
        timestamp = datetime.utcnow().isoformat() + 'Z'
        message = Message(id=str(uuid.uuid4()), role=role, content=content, timestamp=timestamp)

        if conversation_file:
            await self.save_message(conversation_file, message)
            if conversation_file not in self.conversation_cache:
                self.conversation_cache[conversation_file] = await self.load_conversation_history(conversation_file)
            self.conversation_cache[conversation_file].append(message)
            return "Message added successfully."
        else:
            return "Message not added. Conversation file not provided."

    def truncate_conversation_history(self, model_name: str, token_limit: int, conversation_file: str) -> List[Message]:
        if conversation_file not in self.conversation_cache:
            return []

        cached_history = self.conversation_cache[conversation_file]

        truncated_history = []
        token_count = self.count_tokens(self.system_prompt)

        for message in reversed(cached_history):
            message_tokens = self.count_tokens(message.content)
            if token_count + message_tokens <= token_limit:
                truncated_history.insert(0, message)
                token_count += message_tokens
            else:
                break

        return truncated_history

    def _prepare_messages_for_model(self, model_name: str, token_limit: int, conversation_file: str) -> List[Message]:
        truncated_history = self.truncate_conversation_history(model_name, token_limit, conversation_file)

        system_message = Message(
            id=str(uuid.uuid4()),
            role="system",
            content=self.system_prompt,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

        user_message_content = "<conversation>\n"
        for msg in truncated_history:
            if msg.role == "user":
                user_message_content += f"<user>{msg.content}</user>\n"
            elif msg.role == "assistant":
                user_message_content += f"<engineer>{msg.content}</engineer>\n"
        user_message_content += "</conversation>\n"

        user_message_content += "\n<question>" + truncated_history[-1].content + "</question>\n"

        user_message = Message(
            id=str(uuid.uuid4()),
            role="user",
            content=user_message_content.strip(),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )

        return [system_message, user_message]

    def get_active_conversation(self):
        return self.active_conversation

    def set_active_conversation(self, conversation_file):
        self.active_conversation = conversation_file