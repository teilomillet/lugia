from dotenv import load_dotenv
import os
import litellm
from loguru import logger
import fire
from dataclasses import dataclass

# Configure loguru logger
logger.add("error_log.log", rotation="10 MB", compression="zip")

# Load .env variables
load_dotenv()

# Access the environment variables
openai_key = os.getenv('OPENAI_API_KEY')

# Add the api-key to litellm
litellm.openai_key = openai_key

@dataclass
class Message:
    model: str
    content: str
    stream: bool = True

def submit_message(model, content, stream=True):
    message = Message(model=model, content=content, stream=stream)
    try:
        response = litellm.completion(
            model=message.model,
            messages=[{"role": "user", "content": message.content}],
            stream=message.stream,
        )
        print(response)
    except Exception as e:  # Replace OpenAIError with a more general or specific exception if needed
        logger.exception("An error occurred during the completion request")
        # Optionally, re-raise the exception if you want the error to propagate
        # raise e

if __name__ == "__main__":
    fire.Fire(submit_message)
