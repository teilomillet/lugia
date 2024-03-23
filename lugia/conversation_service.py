# conversation_service.py
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json
from typing import List, Optional
from config import Config
from loguru import logger
import aiofiles
from pathlib import Path
from tiktoken import encoding_for_model
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
        self.history_dir = Path(Config.HISTORY_DIR)
        self.history_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
        self.current_conversation_file = self.get_latest_conversation_file()
        self.conversation_history: List[Message] = []  # Initialize conversation_history
        self.conversation_cache = LRUCache(maxsize=Config.CACHE_SIZE)

    def count_tokens(self, text: str) -> int:
        encoding = encoding_for_model("gpt-4")
        return len(encoding.encode(text))

    def get_latest_conversation_file(self) -> Optional[Path]:
        conversation_files = sorted(self.history_dir.glob("*.json"), reverse=True)
        return conversation_files[0] if conversation_files else None

    async def load_conversation_history(self, conversation_file: Path) -> List[Message]:
        try:
            async with aiofiles.open(conversation_file, 'r') as f:
                contents = await f.read()
                messages_dict = json.loads(contents)
                messages = [Message(**message_dict) for message_dict in messages_dict]
                return messages
        except FileNotFoundError:
            logger.warning(f"Conversation file not found: {conversation_file}")
            return []

    async def save_message(self, conversation_file: Path, message: Message):
        try:
            async with aiofiles.open(conversation_file, 'r+') as f:
                # Read the existing JSON array
                contents = await f.read()
                messages = json.loads(contents)

                # Append the new message to the array
                message_dict = asdict(message)
                messages.append(message_dict)

                # Write the updated JSON array back to the file
                await f.seek(0)
                await f.truncate()
                json_string = json.dumps(messages, indent=2)
                await f.write(json_string)
        except Exception as e:
            logger.exception(f"Failed to save message: {e}")

    async def create_new_conversation(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_conversation_file = self.history_dir / f"conversation_{timestamp}.json"

        # Save an empty JSON array to the new file
        async with aiofiles.open(new_conversation_file, 'w') as f:
            await f.write('[]')

        self.current_conversation_file = new_conversation_file
        self.conversation_history = []
        self.conversation_cache.clear()

    async def switch_conversation(self, conversation_file: Path):
        if not conversation_file.exists():
            raise FileNotFoundError(f"Conversation file not found: {conversation_file}")
        self.current_conversation_file = conversation_file
        self.conversation_history = await self.load_conversation_history(conversation_file)
        self.conversation_cache.clear()

    async def add_message(self, role: str, content: str, model_name: str, token_limit: int):
        if self.current_conversation_file is None:
            await self.create_new_conversation()

        message = Message(id=str(uuid.uuid4()), role=role, content=content, timestamp=datetime.utcnow().isoformat() + 'Z')

        self.conversation_history.append(message)
        await self.save_message(self.current_conversation_file, message)
        self.conversation_cache[self.current_conversation_file] = self.conversation_history

        return "Message added successfully."

    def truncate_conversation_history(self, model_name: str, token_limit: int) -> List[Message]:
        if self.current_conversation_file not in self.conversation_cache:
            self.conversation_cache[self.current_conversation_file] = self.conversation_history

        cached_history = self.conversation_cache[self.current_conversation_file]

        truncated_history = []
        token_count = 0

        for message in reversed(cached_history):
            message_tokens = self.count_tokens(message.content)
            if token_count + message_tokens <= token_limit:
                truncated_history.insert(0, message)
                token_count += message_tokens
            else:
                break

        return truncated_history

    def _prepare_messages_for_model(self, model_name: str, token_limit: int) -> List[Message]:
        truncated_history = self.truncate_conversation_history(model_name, token_limit)

        formatted_content = "Here's are the previous part of a friendly conversation:\n\n"
        for msg in truncated_history:
            prefix = f"{msg.role}: "
            formatted_content += prefix + msg.content + "\n\n"
        formatted_content += "\n"

        return [Message(id=str(uuid.uuid4()), role="user", content=formatted_content.strip(), timestamp=datetime.utcnow().isoformat() + 'Z')]