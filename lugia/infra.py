import json
from dataclasses import dataclass, field, asdict  # Correctly import asdict here
from datetime import datetime
from dotenv import load_dotenv
import uuid
import os
from loguru import logger
import fire
import litellm
from typing import List

# Load environment variables
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

# Set the API key for litellm
litellm.openai_key = openai_key
litellm.anthropic_key = anthropic_key

history_file = "conversation_history.json"

model_shortcuts = {
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-2": 'claude-2.1',
    "gpt-4": "gpt-4-turbo-preview",
    "gpt-3.5": "gpt-3.5-turbo",
}

@dataclass
class Message:
    id: str
    role: str
    content: str
    timestamp: str

@dataclass
class LiteLLMConversation:
    model: str
    max_tokens: int = 4096
    conversation_history: List[Message] = field(default_factory=list)

    def __post_init__(self):
        self.model = model_shortcuts.get(self.model, self.model)
        self.conversation_history = self.load_conversation_history()

    def add_message(self, role: str, content: str):
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat() + 'Z',
        )
        self.conversation_history.append(message)
        with open(history_file, 'w') as f:
            json.dump([asdict(msg) for msg in self.conversation_history], f, indent=4)  # Corrected usage of asdict

    def _prepare_messages_for_model(self) -> List[Message]:
        formatted_content = ""
        for msg in self.conversation_history:
            prefix = f"{msg.role}: "
            formatted_content += prefix + msg.content + "\n\n"

        return [Message(id=str(uuid.uuid4()), role="user", content=formatted_content.strip(), timestamp=datetime.utcnow().isoformat() + 'Z')]

    def submit(self, user_message: str):
        self.add_message("user", user_message)
        messages_to_send = self._prepare_messages_for_model()
        
        try:
            response = litellm.completion(model=self.model, messages=[asdict(msg) for msg in messages_to_send])
            self.add_message("assistant", response.choices[0].message.content)
            print(response.choices[0].message.content)
            # print(response.usage.total_tokens)
            # print(response.model)
        except Exception as e:
            logger.exception("Error during LiteLLM completion")
            raise e

    def load_conversation_history(self) -> List[Message]:
        try:
            with open(history_file, 'r') as f:
                return [Message(**msg) for msg in json.load(f)]
        except FileNotFoundError:
            return []

def chat(model: str, content: str):
    conv = LiteLLMConversation(model=model)
    conv.submit(content)

if __name__ == "__main__":
    logger.add("liteLLM_log.log", rotation="10 MB", compression="zip")
    fire.Fire(chat)
