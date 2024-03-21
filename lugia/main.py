# main.py
from fastapi import FastAPI, HTTPException, Query
from model_manager import ModelManager
from dataclasses import asdict
from conversation_service import ConversationService
from pydantic import BaseModel
from loguru import logger
from config import Config
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

logger.add(Config.LOG_FILE, rotation="10 MB", compression="zip")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_manager = ModelManager()
conversation_service = ConversationService()

class ChatRequest(BaseModel):
    model: str
    content: str

@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        await conversation_service.add_message("user", request.content)
        formatted_messages = conversation_service._prepare_messages_for_model()
        response = await model_manager.generate_response(request.model, [asdict(msg) for msg in formatted_messages])
        await conversation_service.add_message("assistant", response)
        return {"response": response}
    except Exception:
        logger.exception("Failed to process chat request")
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")

@app.get("/conversations/")
async def list_conversations():
    conversations = await conversation_service.list_conversations()
    return {"conversations": [conv.name for conv in conversations]}

@app.post("/conversations/new/")
async def create_new_conversation():
    await conversation_service.create_new_conversation()
    return {"message": "New conversation created."}

@app.post("/conversations/switch/")
async def switch_conversation(conversation_file: str = Query(...)):
    conversation_path = Path(Config.HISTORY_DIR) / conversation_file
    await conversation_service.switch_conversation(conversation_path)
    return {"message": f"Switched to conversation: {conversation_file}"}

@app.get("/conversations/history/")
async def get_conversation_history():
    messages = await conversation_service.get_conversation_history()
    return {"messages": [asdict(msg) for msg in messages]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)