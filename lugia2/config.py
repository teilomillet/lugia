# config.py
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    HISTORY_FILE = "conversation_history.json"
    LOG_FILE = "liteLLM_log.log"