import os
import json
from pathlib import Path
from langchain_ollama import OllamaLLM as Ollama
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

def list_sessions():
    """Return list of session IDs (filenames without .json)."""
    return [p.stem for p in SESSIONS_DIR.glob("*.json")]

def choose_session():
    existing = list_sessions()
    if existing:
        print("Existing Sessions:")
        for i, s in enumerate(existing, 1):
            print(f" {i}.{s}")
        print("Enter a number to resume, or type a new name to create:")
        choice = input("> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(existing):
            return existing[int(choice)-1]
        return choice
    else:
        print("No sessions yet. Enter a name to create one:")
        return input("> ").strip()
    
session_id = choose_session()
session_file = SESSIONS_DIR / f"{session_id}.json"
if not session_file.exists():

    session_file.write_text("[]", encoding="utf-8")
print(f"\nUsing Session: {session_id}\n")

memory = ConversationBufferMemory(return_messages = True)
history_data = json.loads(session_file.read_text(encoding="utf-8"))
for turn in history_data:
    role = turn["role"]
    content = turn["content"]
    if role == "user":
        memory.chat_memory.add_user_message(content)
    else:
        memory.chat_memory.add_ai_message(content)

model = Ollama(model="mistral")

system_prompt = (
    "You are a concise, highly knowledgeable AI assistant. "
    "Answer clearly, directly, and to the point"
    "Avoid repeating the user's input. Maintain a helpful tone."
)
prompt_tmpl = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    ("user","{user_input}")
])

print("Welcome! Type 'clear' to reset this session,'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit","quit"):
        print("Goodbye!")
        break

    if user_input.lower() == "clear":
        memory.clear()
        session_file.write_text("[]",encoding = "utf-8")
        print("\nSession memory CLEARED")
        continue

    memory.chat_memory.add_user_message(user_input)
    history_data.append({"role":"user","content":user_input})

    system_msg = SystemMessage(content=system_prompt)
    full_convo = [system_msg] + memory.chat_memory.messages[:-1] + [HumanMessage(content=user_input)]

    convo = [system_msg] + memory.chat_memory.messages[:-1] + [HumanMessage(content=user_input)]

    print("Bot:",end=" ",flush = True)
    response = ""
    for token in model.stream(convo):
        print(token, end = "",flush = True)
        response += token
    print("\n")

    memory.chat_memory.add_ai_message(response)
    history_data.append({"role":"ai","content":response})

    session_file.write_text(json.dumps(history_data, ensure_ascii=False,indent = 2),encoding = "utf-8")    

