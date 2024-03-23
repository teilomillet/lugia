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

    def count_tokens(self, text: str) -> int:
        encoding = encoding_for_model("gpt-4")
        return len(encoding.encode(text))

    def get_latest_conversation_file(self) -> Optional[Path]:
        conversation_files = sorted(self.history_dir.glob("*.json"), reverse=True)
        return conversation_files[0] if conversation_files else None

    async def load_conversation_history(self, conversation_file: Path) -> List[Message]:
        try:
            async with aiofiles.open(conversation_file, 'r') as f:
                content = await f.read()
                return [Message(**msg) for msg in json.loads(content)]
        except FileNotFoundError:
            return []

    async def save_conversation_history(self, conversation_file: Path, conversation_history: List[Message]):
        async with aiofiles.open(conversation_file, 'w') as f:
            await f.write(json.dumps([asdict(msg) for msg in conversation_history], indent=4))

    async def list_conversations(self) -> List[Path]:
        return [file for file in self.history_dir.glob("*.json")]

    async def create_new_conversation(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_conversation_file = self.history_dir / f"conversation_{timestamp}.json"
        self.conversation_history = []
        await self.save_conversation_history(self.current_conversation_file, self.conversation_history)

    async def switch_conversation(self, conversation_file: Path):
        self.current_conversation_file = conversation_file
        self.conversation_history = await self.load_conversation_history(conversation_file)

    async def add_message(self, role: str, content: str, model_name: str, token_limit: int):
        if self.current_conversation_file is None:
            await self.create_new_conversation()

        message = Message(id=str(uuid.uuid4()), role=role, content=content, timestamp=datetime.utcnow().isoformat() + 'Z')

        self.conversation_history.append(message)
        truncated_history = self.truncate_conversation_history(model_name, token_limit)

        await self.save_conversation_history(self.current_conversation_file, truncated_history)
        return "Message added successfully."

    def truncate_conversation_history(self, model_name: str, token_limit: int) -> List[Message]:
        truncated_history = []
        token_count = 0

        for message in reversed(self.conversation_history):
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