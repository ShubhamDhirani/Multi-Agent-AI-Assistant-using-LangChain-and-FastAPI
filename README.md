# QnA Chatbot

![WIP](https://img.shields.io/badge/status-WIP-orange)

A modular QnA chatbot powered by LangChain and Mistral LLM via Ollama. Features persistent session support, a FastAPI backend, and an advanced MCP server with a LangChain agent that orchestrates Wikipedia and calculator tools.

## Features
- **Session Management:** Create, resume, delete, rename, and clear chat sessions. Each session's history is stored in a separate JSON file.
- **Streaming Responses:** Real-time streaming of AI responses for a natural chat experience.
- **Memory Buffer:** Uses LangChain's `ConversationBufferMemory` to maintain context within each session. Also records timestamps for each user and AI message in session history.
- **FastAPI Backend:** RESTful `/chat` endpoint for integration with web frontends or other clients.
- **MCP Server with Agent:** Advanced FastAPI server (`mcp_server.py`) that uses a LangChain agent to orchestrate Wikipedia and Python calculator tools for enhanced Q&A. Supports session-based memory and persistent chat history.
- **Customizable System Prompt:** The assistant is concise, knowledgeable, and avoids repeating user input.

## Requirements
- Python 3.8+
- [LangChain](https://github.com/langchain-ai/langchain)
- [Ollama](https://ollama.com/)
- [langchain_ollama](https://pypi.org/project/langchain-ollama/)
- [langchain-community](https://pypi.org/project/langchain-community/)
- [langchain-experimental](https://pypi.org/project/langchain-experimental/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/) (for running the FastAPI server)
- [pydantic](https://docs.pydantic.dev/)

Or simply:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Ollama locally:
Make sure you have the Ollama server running and the `mistral` model available.

### 3. Start the chatbot (CLI):
```bash
python app.py
```

### 4. Start the FastAPI backend (QnA API):
```bash
uvicorn main:app --reload
```
- The API will be available at `http://127.0.0.1:8000/chat` (POST endpoint).
> Note: `/chat` is a POST endpoint. Use `curl`, Postman, or your frontend code—not directly in the browser.

### 5. Start the MCP server (with agent and tools):
```bash
uvicorn mcp_server:app --reload --port 8001
```
- The MCP API will be available at `http://127.0.0.1:8001/mcp` (POST endpoint).
- The MCP server uses a LangChain agent that can reason and decide when to use the Wikipedia or calculator tools to answer user queries.

### 6. Interact (CLI):
- Type your message and press Enter.
- Type `clear` to reset the current session.
- Type `exit` or `quit` to end the chat.
- Type `delete` to remove an existing session.
- Type `/rename` during a chat session to rename it.

### 7. Interact (API):
Send a POST request to `/chat` with JSON:
```json
{
  "session_id": "your_session_name",
  "user_input": "Your question here"
}
```
Response:
```json
{
  "response": "AI's answer here"
}
```

### 8. Interact (MCP API):
Send a POST request to `/mcp` with JSON:
```json
{
  "user_input": "What is the capital of France?",
  "session_id": "your_session_name"  // optional
}
```
Response:
```json
{
  "response": "Paris is the capital of France.",
  "session_id": "your_session_name"
}
```

## File Structure
- `app.py` — Main chatbot application (CLI).
- `main.py` — FastAPI backend exposing a `/chat` endpoint.
- `mcp_server.py` — Advanced FastAPI backend with a LangChain agent that orchestrates Wikipedia and calculator tools, session memory, and persistent history.
- `chatbot.py` — Chat logic used by both CLI and API.
- `sessions/` — Stores session history as JSON files.
- `requirements.txt` — Project dependencies.

## Example (CLI)
```
Welcome! Type 'clear' to reset this session,'exit' to quit.
You: What is the capital of France?
Bot: Paris is the capital of France.
```

## Example (API)
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test", "user_input": "What is the capital of France?"}'
```
Response:
```json
{"response": "Paris is the capital of France."}
```

## Example (MCP API)
```bash
curl -X POST "http://127.0.0.1:8001/mcp" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "2+2", "session_id": "test"}'
```
Response:
```json
{"response": "4", "session_id": "test"}
```

## License
MIT