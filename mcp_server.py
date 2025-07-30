from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn

from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_ollama import OllamaLLM

from chatbot import get_chat_response
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
from pathlib import Path

from datetime import datetime


SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok = True)

def load_memory_from_session(session_id: str) -> ConversationBufferMemory:
    
    memory = ConversationBufferMemory(
        memory_key = "chat_history",
        input_key = "input",
        return_messages=True
    )
    
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return memory
    
    history_data = json.loads(session_file.read_text(encoding = "utf-8"))
    for turn in history_data:
        if turn["role"] == "user":
            memory.chat_memory.add_user_message(turn["content"])
        elif turn["role"] == "ai":
            memory.chat_memory.add_ai_message(turn["content"])
    return memory            

app = FastAPI(title = "MCP Server")

class PromptRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

llm = OllamaLLM(model="mistral")

system_prompt = (
    "You are a concise, highly knowledgeable AI assistant."
    "Answer clearly, directly and to the point. "
    "Avoid repeating the user's input. Maintain a helpful and polite tone. "
)

wikipedia_tool = Tool(
    name = "Wikipedia",
    func = WikipediaQueryRun(api_wrapper = WikipediaAPIWrapper()).run,
    description = "Useful for answering general knowledge questions using Wikipedia."
)

python_repl = PythonREPLTool()

math_tool = Tool(
    name="Calculator",
    func=python_repl.run,
    description=(
        "Execute Python expressions, e.g. '2+2','sqrt(4)', or any valid python code. "
        "Returns the output as text."
    )
)

tools = [wikipedia_tool,math_tool]

def orchestrate_conversation(user_input: str, session_id: str) -> str:
    
    memory = load_memory_from_session(session_id)            

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        handle_parsing_errors = False,
        verbose = True
    )
    result = agent.run(user_input)
    return result 

@app.post("/mcp")
async def route_prompt(request: PromptRequest):
    session_id = request.session_id or "default"
    user_input = request.user_input

    result = orchestrate_conversation(user_input, session_id)

    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        session_file.write_text("[]",encoding = "utf-8")

    history_data = json.loads(session_file.read_text(encoding = "utf-8"))

    history_data.append({
        "role":"user",
        "content":user_input,
        "timestamp":datetime.now().isoformat()
    }) 

    history_data.append({
        "role":"ai",
        "content":result,
        "timestamp":datetime.now().isoformat()
    })

    session_file.write_text(
        json.dumps(history_data, ensure_ascii = False, indent = 2),
        encoding = "utf-8"
    )   

    return{
        "response": result,
        "session_id": session_id
    }    

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host = "127.0.0.1", port = 8001, reload = True)