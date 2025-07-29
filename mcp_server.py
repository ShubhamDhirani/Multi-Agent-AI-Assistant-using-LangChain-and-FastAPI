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

app = FastAPI(title = "MCP Server")

class PromptRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

llm = OllamaLLM(model="mistral")

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

def orchestrate_conversation(user_input: str) -> str:
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose = True
    )
    return agent.run(user_input)

@app.post("/mcp")
async def route_prompt(request: PromptRequest):
    result = orchestrate_conversation(request.user_input)
    return{
        "response": result,
        "session_id": request.session_id or "default"
    }    

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host = "127.0.0.1", port = 8001, reload = True)