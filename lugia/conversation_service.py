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

    async def save_conversation_history(self, conversation_file: Path):
        async with aiofiles.open(conversation_file, 'w') as f:
            await f.write(json.dumps([asdict(msg) for msg in self.conversation_history], indent=4))

    async def list_conversations(self) -> List[Path]:
        return [file for file in self.history_dir.glob("*.json")]

    async def create_new_conversation(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_conversation_file = self.history_dir / f"conversation_{timestamp}.json"
        self.conversation_history = []

    async def switch_conversation(self, conversation_file: Path):
        self.current_conversation_file = conversation_file
        self.conversation_history = await self.load_conversation_history(conversation_file)

    async def add_message(self, role: str, content: str):
        if self.current_conversation_file is None:
            await self.create_new_conversation()

        message = Message(id=str(uuid.uuid4()), role=role, content=content, timestamp=datetime.utcnow().isoformat() + 'Z')
        self.conversation_history.append(message)
        await self.save_conversation_history(self.current_conversation_file)

    def _prepare_messages_for_model(self) -> List[Message]:
        # Prepare conversation history for submission to the model
        formatted_content = "This is a friendly conversation:\n<conversation>\n"
        for msg in self.conversation_history:
            prefix = f"{msg.role}: "
            formatted_content += prefix + msg.content + "\n\n"
        formatted_content += "</conversation>\n"
        return [Message(id=str(uuid.uuid4()), role="user", content=formatted_content.strip(), timestamp=datetime.utcnow().isoformat() + 'Z')]