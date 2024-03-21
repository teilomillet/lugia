# model_manager.py
from config import Config
import litellm
from loguru import logger

logger.add(Config.LOG_FILE, rotation="10 MB", compression="zip")

# Initialize API keys
litellm.openai_key = Config.OPENAI_API_KEY
litellm.anthropic_key = Config.ANTHROPIC_API_KEY

class ModelManager:
    def __init__(self):
        self.model_shortcuts = {
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-2": 'claude-2.1',
            "gpt-4": "gpt-4-turbo-preview",
            "gpt-3.5": "gpt-3.5-turbo",
        }

    def get_model_name(self, model_name: str) -> str:
        return self.model_shortcuts.get(model_name, model_name)

    async def generate_response(self, model: str, messages: list):
        model_name = self.get_model_name(model)
        try:
            formatted_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            response = await litellm.acompletion(model=model_name, messages=formatted_messages, max_tokens=4096)
            print("Response:", response)  # Print response for debugging
            return response.choices[0].message.content  # Assuming response structure
        except Exception as e:
            logger.exception("Error during model response generation")
            raise e