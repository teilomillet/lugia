import json
from datetime import datetime
from dotenv import load_dotenv
import uuid
import os
from loguru import logger
import fire
import litellm

# Load environment variables
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

# Set the API key for litellm
litellm.openai_key = openai_key
litellm.anthropic_key = anthropic_key

# Set verbose (troubleshooting)
#litellm.set_verbose= True

history_file = "conversation_history.json"

model_shortcuts = {
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3-opus" : "claude-3-opus-20240229",
    "claude-3-sonnet" : "claude-3-sonnet-20240229",
    "claude-2" : 'claude-2.1',
    "gpt-4": "gpt-4-turbo-preview",
    "gpt-3.5" : "gpt-3.5-turbo",
    # Add more mappings as needed
}


class LiteLLMConversation:
    def __init__(self, model, max_tokens=4096):
        self.model = model_shortcuts.get(model, model)  # Translate shorthand to full model name
        self.max_tokens = max_tokens
        self.conversation_history = self.load_conversation_history()

    def add_message(self, role, content):
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
        }
        # Update in-memory history
        self.conversation_history.append(message)
        # Append to the persistent history file
        with open(history_file, 'w') as f:
            json.dump(self.conversation_history, f, indent=4)

    def submit(self, user_message):
        self.add_message("user", user_message)
        messages_to_send = self._prepare_messages_for_model()
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages_to_send,
            )
            # Assuming the response structure, adjust as needed
            self.add_message("assistant", response.choices[0].message.content)
            print(messages_to_send)
            print("---")
            print(response.choices[0].message.content)
            print(response.usage.total_tokens)
            print(response.model)
        except Exception as e:
            logger.exception("Error during LiteLLM completion")
            raise e

    def _prepare_messages_for_model(self):
        """
        Formats the conversation history into a single string that alternates between user and assistant messages.
        This makes the conversation more comprehensible and useful for future interactions.
        """
        formatted_content = ""
        for msg in self.conversation_history:
            # Add user or assistant prefix based on the role
            prefix = f"{msg['role']}: "
            formatted_content += prefix + msg["content"] + "\n\n"

        # Check if the formatted content exceeds max tokens, and trim if necessary
        tokens = formatted_content.split()
        if len(tokens) > self.max_tokens:
            # If exceeds, trim tokens from the start
            trimmed_content = " ".join(tokens[-self.max_tokens:])
            formatted_content = trimmed_content

        # Wrap the formatted content in a list to match expected input format
        messages_to_send = [{
            "id": str(uuid.uuid4()),
            "role": "user",  # Assuming the whole conversation is treated as 'user' input
            "content": formatted_content.strip(),
            "timestamp": datetime.utcnow().isoformat() + 'Z',
        }]

        return messages_to_send



    def load_conversation_history(self):
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

def chat(model, content):
    conv = LiteLLMConversation(model=model)
    conv.submit(content)

if __name__ == "__main__":
    logger.add("liteLLM_log.log", rotation="10 MB", compression="zip")
    fire.Fire(chat)