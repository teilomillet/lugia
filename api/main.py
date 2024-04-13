# lugia/api/main.py
from fastapi import FastAPI, HTTPException
from core.model import ModelManager
from core.conversation import ConversationService
from fastapi.templating import Jinja2Templates
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger
from config import Config
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import asdict

logger.add(Config.LOG_FILE, rotation="10 MB", compression="zip")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

model_manager = ModelManager()
conversation_service = ConversationService()

templates = Jinja2Templates(directory="www")


class ChatRequest(BaseModel):
    model: str
    content: str

@app.get("/")
async def homepage(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering the homepage: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat/")
async def chat(request: ChatRequest):
    try:
        conversation_file = conversation_service.get_active_conversation()
        if not conversation_file:
            return {"response": "No active conversation found. Please create a new conversation or switch to an existing one."}

        result = await conversation_service.add_message("user", request.content, request.model, Config.TOKEN_LIMIT, conversation_file)
        if result.startswith("Message not added"):
            return {"response": result}

        formatted_messages = conversation_service._prepare_messages_for_model(request.model, Config.TOKEN_LIMIT, conversation_file)
        response = await model_manager.generate_response(request.model, [asdict(msg) for msg in formatted_messages])
        result = await conversation_service.add_message("assistant", response, request.model, Config.TOKEN_LIMIT, conversation_file)
        if result.startswith("Message not added"):
            return {"response": result}
        return {"response": response, "conversation_file": conversation_file}
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
    conversation_service.set_active_conversation(conversation_file)
    return {"message": "New conversation created.", "conversation_file": conversation_file}

@app.get("/conversations/history/")
async def get_conversation_history(conversation_file: str):
    messages = await conversation_service.load_conversation_history(conversation_file)
    return {"messages": [asdict(msg) for msg in messages]}

@app.post("/conversations/switch/")
async def switch_conversation(conversation_file: str):
    switched_conversation = await conversation_service.switch_conversation(conversation_file)
    if switched_conversation:
        conversation_service.set_active_conversation(conversation_file)
        return {"message": f"Switched to conversation: {conversation_file}"}
    else:
        raise HTTPException(status_code=404, detail="Conversation file not found on S3.")

@app.delete("/conversations/{conversation_file}")
async def delete_conversation(conversation_file: str):
    deleted = await conversation_service.delete_conversation(conversation_file)
    if deleted:
        return {"message": f"Conversation {conversation_file} deleted successfully."}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation {conversation_file}.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)