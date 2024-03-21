# conversation_service.py
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json
from typing import List
from config import Config
from loguru import logger

logger.add(Config.LOG_FILE, rotation="10 MB", compression="zip")

@dataclass
class Message:
    id: str
    role: str
    content: str
    timestamp: str

class ConversationService:
    def __init__(self):
        self.conversation_history: List[Message] = self.load_conversation_history()

    def _prepare_messages_for_model(self) -> List[Message]:
        # Prepare conversation history for submission to the model
        formatted_content = "This is a friendly conversation:\n<conversation>\n"
        for msg in self.conversation_history:
            prefix = f"{msg.role}: "
            formatted_content += prefix + msg.content + "\n\n"
        formatted_content += "</conversation>\n"
        return [Message(id=str(uuid.uuid4()), role="user", content=formatted_content.strip(), timestamp=datetime.utcnow().isoformat() + 'Z')]
    
    def add_message(self, role: str, content: str):
        message = Message(id=str(uuid.uuid4()), role=role, content=content, timestamp=datetime.utcnow().isoformat() + 'Z')
        self.conversation_history.append(message)
        self.save_conversation_history()

    def load_conversation_history(self) -> List[Message]:
        try:
            with open(Config.HISTORY_FILE, 'r') as f:
                return [Message(**msg) for msg in json.load(f)]
        except FileNotFoundError:
            return []

    def save_conversation_history(self):
        with open(Config.HISTORY_FILE, 'w') as f:
            json.dump([asdict(msg) for msg in self.conversation_history], f, indent=4)