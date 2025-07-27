# QnA Chatbot

![WIP](https://img.shields.io/badge/status-WIP-orange)

A simple, modular QnA chatbot powered by LangChain and Mistral LLM via Ollama. This project demonstrates how to build a conversational AI assistant with persistent session support and an API backend using FastAPI.

## Features
- **Session Management:** Create, resume, delete, rename and clear chat sessions. Each session's history is stored in a separate JSON file.
- **Streaming Responses:** Real-time streaming of AI responses for a natural chat experience.
- **Memory Buffer:** Uses LangChain's `ConversationBufferMemory` to maintain context within each session. Also records timestamps for each user and AI message in session history.
- **FastAPI Backend:** A RESTful / chat endpoint is availaible for integration with web frontends like React.
- **Customizable System Prompt:** The assistant is concise, knowledgeable, and avoids repeating user input.


## Requirements
- Python 3.8+
- [LangChain](https://github.com/langchain-ai/langchain)
- [Ollama](https://ollama.com/)
- `langchain_ollama` Python package
- [FastAPI](https:??fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/) (for running the FastAPI server)


## Usage

### 1. Install dependencies:
```bash
pip install langchain langchain_ollama fastapi uvicorn
```

### 2. Run Ollama locally:
Make sure you have the Ollama server running and the `mistral` model available.

### 3. Start the chatbot (CLI):
```bash
python app.py
```

### 4. Start the FastAPI backend:
```bash
uvicorn main:app --reload
```
- The API will be available at `http://127.0.0.1:8000/chat`.
> Note: `/chat` is a POST endpoint. Access it using a tool like `curl`, Postman, or your frontend code—not directly in the browser.

### 5. Interact (CLI):
- Type your message and press Enter.
- Type `clear` to reset the current session.
- Type `exit` or `quit` to end the chat.
- Type `delete` to remove an existing session.
- Type `/rename` during a chat session to rename it.

### 6. Interact (API):
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

## File Structure
- `app.py` — Main chatbot application (CLI).
- `main.py` — FastAPI backend exposing a `/chat` endpoint.
- `chatbot.py` — Chat logic used by both CLI and API.
- `sessions/` — Stores session history as JSON files.

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

## License
MIT