# config.py
from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    LUGIA_ACCESS_KEY = os.getenv('LUGIA_ACCESS_KEY_ID')
    LUGIA_SECRET_KEY = os.getenv('LUGIA_SECRET_KEY')
    HISTORY_DIR = "conversation_history"  # Directory to store conversation files
    LOG_FILE = "liteLLM_log.log"
    TOKEN_LIMIT = 8182
    CACHE_SIZE = 1000