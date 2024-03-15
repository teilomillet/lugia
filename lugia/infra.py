from dataclasses import dataclass
from dotenv import load_dotenv
import os
import litellm
from loguru import logger
import fire

# Load environment variables
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

# Set the API key for litellm
litellm.openai_key = openai_key
litellm.anthropic_key = anthropic_key


@dataclass
class Message:
    model: str
    content: str

def preprocess_message(message: Message) -> dict:
    """
    Process the Message object to fit the requirements of the litellm completion function.
    This is where you can modify the message content or structure.

    Args:
        message (Message): The message dataclass instance to be processed.

    Returns:
        dict: A processed message ready for submission.
    """
    # Example preprocessing, can be customized as needed
    processed_content = message.content #.strip()  # Simple processing for demonstration


    # Return the message in the format expected by litellm.completion
    return [{"role": "user", "content": processed_content}]



def submit_message(message: Message):
    """
    Submits a message to the LiteLLM completion API.

    Args:
        message (Message): The message dataclass instance to be submitted.
    """
    try:
        processed_messages = preprocess_message(message)
        response = litellm.completion(
            model=message.model, 
            messages=processed_messages, 
        )
        print(response.choices[0].message.content)
    except Exception as e:
        logger.exception("An error occurred during LiteLLM completion request")
        raise e



def cli(model, content, stream=True):
    """
    CLI interface for submitting messages.

    Args:
        model (str): The model to use for the completion.
        content (str): The content of the message.
        stream (bool, optional): Whether to stream the response. Defaults to True.
    """
    message = Message(model=model, content=content)
    submit_message(message)

if __name__ == "__main__":
    logger.add("error_log.log", rotation="10 MB", compression="zip")
    fire.Fire(cli)
