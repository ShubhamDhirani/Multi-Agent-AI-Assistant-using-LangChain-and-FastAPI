from fastapi import FastAPI, Request
from pydantic import BaseModel
from chatbot import get_chat_response

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    user_input: str

class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model = ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:

        response = get_chat_response(request.session_id, request.user_input)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
