from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import uvicorn
import spacy 
from langchain.agents import Tool, ConversationalAgent, AgentExecutor, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from chatbot import get_chat_response
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain.schema.runnable import RunnableLambda
import json
from pathlib import Path

from datetime import datetime
from typing import Dict, Any

nlp = spacy.load("en_core_web_sm")

def resolve_coreferences(history, user_input):
    # Enhanced: If user_input is a pronoun or ambiguous, prepend last user/AI message
    pronouns = ["he", "she", "it", "they", "him", "her", "them"]
    if user_input.strip().lower() in pronouns:
        for turn in reversed(history):
            if turn["role"] == "user":
                return f"{turn['content']} {user_input}"
    # Fallback to previous logic for named entities
    last_mention = None
    for turn in reversed(history):
        doc = nlp(turn["content"])
        for ent in doc.ents:
            if ent.label_ in ["PERSON","ORG","PRODUCT","GPE"]:
                last_mention = ent.text
                break
        if last_mention:
            break
    resolved_input = user_input
    if last_mention:
        resolved_input = user_input.replace("he",last_mention).replace("she", last_mention).replace("it",last_mention)
    return resolved_input
            
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok = True)

PDF_DIR = Path("pdfs")
PDF_DIR.mkdir(exist_ok=True)

VECTOR_DIR = Path("vectorstores")
VECTOR_DIR.mkdir(exist_ok=True)

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
    "When you need to use a tool, ONLY return an Action and Action Input, and wait for the result. "
    "When giving a final answer, ONLY return 'Final Answer: ...'. "
    "Never give both at once. Do not repeat the user's input. Maintain a helpful and polite tone. "
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

@app.post("/upload_pdf")
async def upload_pdf(session_id: str, file: UploadFile = File(...)):
    pdf_path = PDF_DIR / f"{session_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size = 1000, chunk_overlap=100)
    documents = text_splitter.split_documents(pages)

    embeddings = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
    vectorstore_path = VECTOR_DIR / session_id
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(vectorstore_path))

    return {"message" : f"PDF uploaded and processed for session '{session_id}'"}

def load_pdf_tool_if_exists(session_id: str):
    index_path = VECTOR_DIR / session_id
    if not index_path.exists():
        print(f"[DEBUG] No PDF vectorstore for session {session_id}")
        return None
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization = True
    )
    retriever = vectorstore.as_retriever()
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    def pdf_qa_tool_func(query: str) -> str:
        print(f"[DEBUG] PDF_QA tool called with query: {query}")
        return qa_chain.run(query)
    return Tool(
        name="PDF_QA",
        func=pdf_qa_tool_func,
        description="Answer questions using the uploaded PDF for this session. Use this tool for any question about the uploaded document, job description, or PDF content."
    )


def get_tools_for_session(session_id: str):
    tools = [wikipedia_tool, math_tool]
    pdf_tool = load_pdf_tool_if_exists(session_id)
    if pdf_tool:
        print(f"[DEBUG] PDF_QA tool loaded for session {session_id}")
        tools.append(pdf_tool)
    else:
        print(f"[DEBUG] No PDF_QA tool for session {session_id}")
    return tools
@app.get("/test_pdf_vectorstore/{session_id}")
def test_pdf_vectorstore(session_id: str, query: str):
    """Test endpoint to directly query the PDF vectorstore for debugging."""
    index_path = VECTOR_DIR / session_id
    if not index_path.exists():
        return {"error": "No vectorstore for this session."}
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever()
    docs = retriever.get_relevant_documents(query)
    return {"chunks": [d.page_content for d in docs]}

def orchestrate_conversation(user_input: str, session_id: str) -> str:
    # Load memory and tools for this session
    memory = load_memory_from_session(session_id)
    tools = get_tools_for_session(session_id)

    # Load session history for coreference
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        history_data = json.loads(session_file.read_text(encoding="utf-8"))
    else:
        history_data = []

    # Coreference resolution
    resolved_input = resolve_coreferences(history_data, user_input)
    print(f"[DEBUG] Resolved input: {resolved_input}")

    # Initialize agent with all tools and memory
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )

    # Run agent
    retries = 0
    while retries < 4:
        try:
            response = agent.run(resolved_input)
            print(f"[DEBUG] Agent response: {response}")
            break
        except Exception as e:
            retries += 1
            print(f"[Agent parsing error] Retry {retries}/4: {e}")
            response = "Sorry, I couldn't process your request due to an internal error. Please rephrase your question. "

    # Update memory and session file
    memory.chat_memory.add_user_message(user_input)
    memory.chat_memory.add_ai_message(response)

    history_data.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    history_data.append({
        "role": "ai",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })

    session_file.write_text(
        json.dumps(history_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return response

@app.post("/mcp")
async def route_prompt(request: PromptRequest):
    session_id = request.session_id or "default"
    user_input = request.user_input

    result = orchestrate_conversation(user_input, session_id)

    return{
        "response": result,
        "session_id": session_id
    }

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host = "127.0.0.1", port = 8001, reload = True)