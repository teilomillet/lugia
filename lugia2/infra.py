import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from dotenv import load_dotenv  # Load environment variables from a .env file
import uuid  # Generate unique identifiers
import os  # Access environment variables
from loguru import logger  # Enhanced logging
import fire  # CLI integration
import litellm  # LiteLLM library for model interactions
from typing import List  # Type hinting for lists

# Load environment variables
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')  # Fetch OpenAI API key
anthropic_key = os.getenv('ANTHROPIC_API_KEY')  # Fetch Anthropic API key

# Set the API key for litellm
litellm.openai_key = openai_key
litellm.anthropic_key = anthropic_key

history_file = "conversation_history.json"  # File to store conversation history

# Model shortcuts for easier referencing
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
    id: str  # Unique identifier for the message
    role: str  # Role of the message sender (e.g., user or assistant)
    content: str  # Message content
    timestamp: str  # Timestamp of the message

@dataclass
class LiteLLMConversation:
    model: str  # Model name
    max_tokens: int = 40962  # Maximum tokens for model responses
    conversation_history: List[Message] = field(default_factory=list)  # List to store conversation history

    def __post_init__(self):
        # Replace model name with shortcut if available
        self.model = model_shortcuts.get(self.model, self.model)
        # Load conversation history from file
        self.conversation_history = self.load_conversation_history()

    def add_message(self, role: str, content: str):
        # Create and add a new message to the conversation history
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat() + 'Z',
        )
        self.conversation_history.append(message)
        # Save updated conversation history to file
        with open(history_file, 'w') as f:
            json.dump([asdict(msg) for msg in self.conversation_history], f, indent=4)

    def _prepare_messages_for_model(self) -> List[Message]:
        # Prepare conversation history for submission to the model
        formatted_content = ""
        for msg in self.conversation_history:
            prefix = f"{msg.role}: "
            formatted_content += prefix + msg.content + "\n\n"
        return [Message(id=str(uuid.uuid4()), role="user", content=formatted_content.strip(), timestamp=datetime.utcnow().isoformat() + 'Z')]

    def submit(self, user_message: str):
        # Submit a message from the user to the model and handle the response
        self.add_message("user", user_message)
        messages_to_send = self._prepare_messages_for_model()
        try:
            response = litellm.completion(model=self.model, messages=[asdict(msg) for msg in messages_to_send])
            self.add_message("assistant", response.choices[0].message.content)
            print(response.choices[0].message.content)
        except Exception as e:
            logger.exception("Error during LiteLLM completion")
            raise e

    def load_conversation_history(self) -> List[Message]:
        # Load conversation history from file
        try:
            with open(history_file, 'r') as f:
                return [Message(**msg) for msg in json.load(f)]
        except FileNotFoundError:
            return []  # Return empty list if file does not exist

def chat(model: str, content: str):
    # Facilitate a chat session with a specified model
    conv = LiteLLMConversation(model=model)
    conv.submit(content)

if __name__ == "__main__":
    # Setup logging and CLI
    logger.add("liteLLM_log.log", rotation="10 MB", compression="zip")  # Configure logging
    fire.Fire(chat)  # Enable command-line interface
