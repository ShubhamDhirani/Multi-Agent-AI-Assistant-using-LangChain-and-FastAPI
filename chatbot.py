import os
import json
from pathlib import Path
from datetime import datetime
from langchain_ollama import OllamaLLM as Ollama
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok = True)

model = Ollama(model = "mistral")

system_prompt = (
    "You are a concise, highly knowledgeable AI assistant. "
    "Answer clearly, directly, and to the point. "
    "Avoid repeating the user's input. Mantain a helpful and polite tone. "
)
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    ("user", "{user_input}")
])

def get_session_file(session_id: str) -> Path:
    """Return the full path to the session file."""
    file = SESSIONS_DIR / f"{session_id}.json"
    if not file.exists():
        file.write_text("[]",encoding = "utf-8")
    return file

def get_chat_response(session_id: str, user_input: str) -> str:
    """Main function to handle chat and return response."""
    session_file = get_session_file(session_id)

    history_data = json.loads(session_file.read_text(encoding = "utf-8"))
    memory = ConversationBufferMemory(return_messages = True)

    for turn in history_data:
        role = turn["role"]
        content = turn["content"]
        if role == "user":
            memory.chat_memory.add_user_message(content)
        if role == "ai":    
            memory.chat_memory.add_ai_message(content)

    memory.chat_memory.add_user_message(user_input)
    history_data.append({
        "role":"user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })        

    system_msg = SystemMessage(content = system_prompt)
    convo = [system_msg] + memory.chat_memory.messages[:-1] + [HumanMessage(content = user_input)]

    response = ""
    for token in model.stream(convo):
        response += token

    memory.chat_memory.add_ai_message(response)
    history_data.append({
        "role":"ai",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })    

    session_file.write_text(json.dumps(history_data, ensure_ascii = False, indent = 2), encoding = "utf-8")

    return response