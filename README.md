# QnA Chatbot

![WIP](https://img.shields.io/badge/status-WIP-orange)

A simple, session-based command-line chatbot powered by LangChain and Mistral LLM via Ollama. This project demonstrates how to build a conversational AI assistant that maintains chat history across sessions using JSON files.

## Features
- **Session Management:** Create, resume, delete, rename and clear chat sessions. Each session's history is stored in a separate JSON file.
- **Streaming Responses:** Real-time streaming of AI responses for a natural chat experience.
- **Memory Buffer:** Uses LangChain's `ConversationBufferMemory` to maintain context within each session.
- **Customizable System Prompt:** The assistant is concise, knowledgeable, and avoids repeating user input.

## Requirements
- Python 3.8+
- [LangChain](https://github.com/langchain-ai/langchain)
- [Ollama](https://ollama.com/)
- `langchain_ollama` Python package

## Usage
1. **Install dependencies:**
   ```bash
   pip install langchain langchain_ollama
   ```
2. **Run Ollama locally:**
   Make sure you have the Ollama server running and the `mistral` model available.
3. **Start the chatbot:**
   ```bash
   python app.py
   ```
4. **Interact:**
   - Type your message and press Enter.
   - Type `clear` to reset the current session.
   - Type `exit` or `quit` to end the chat.
   - Type `delete` to remove an existing session.
   - Type `/rename` during a chat session to rename it.

## File Structure
- `app.py` — Main chatbot application.

## Example
```
Welcome! Type 'clear' to reset this session,'exit' to quit.
You: What is the capital of France?
Bot: Paris is the capital of France.
```

## License
MIT
