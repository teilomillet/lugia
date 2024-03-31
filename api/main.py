# lugia/api/main.py
from fastapi import FastAPI, HTTPException, Query
from core.model import ModelManager
from dataclasses import asdict
from core.conversation import ConversationService
from pydantic import BaseModel
from loguru import logger
from config import Config
from fastapi.middleware.cors import CORSMiddleware

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
        conversation_file = await conversation_service.create_new_conversation()
        result = await conversation_service.add_message("user", request.content, request.model, Config.TOKEN_LIMIT)
        if result.startswith("Message not added"):
            return {"response": result}

        formatted_messages = conversation_service._prepare_messages_for_model(request.model, Config.TOKEN_LIMIT, conversation_file)
        response = await model_manager.generate_response(request.model, [asdict(msg) for msg in formatted_messages])
        result = await conversation_service.add_message("assistant", response, request.model, Config.TOKEN_LIMIT)
        if result.startswith("Message not added"):
            return {"response": result}
        return {"response": response}
    except Exception:
        logger.exception("Failed to process chat request")
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")


@app.get("/conversations/")
async def list_conversations():
    conversations = await conversation_service.list_conversations()
    return {"conversations": conversations}


@app.post("/conversations/new/")
async def create_new_conversation():
    conversation_file = await conversation_service.create_new_conversation()
    return {"message": "New conversation created.", "conversation_file": conversation_file}


@app.get("/conversations/history/")
async def get_conversation_history(conversation_file: str = Query(...)):
    messages = await conversation_service.load_conversation_history(conversation_file)
    return {"messages": [asdict(msg) for msg in messages]}


@app.post("/conversations/switch/")
async def switch_conversation(conversation_file: str = Query(...)):
    switched_conversation = await conversation_service.switch_conversation(conversation_file)
    if switched_conversation:
        return {"message": f"Switched to conversation: {conversation_file}"}
    else:
        raise HTTPException(status_code=404, detail="Conversation file not found on S3.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)