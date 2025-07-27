import os
import json
from pathlib import Path
from langchain_ollama import OllamaLLM as Ollama
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from datetime import datetime

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

def list_sessions():
    """Return list of session IDs (filenames without .json)."""
    return [p.stem for p in sorted(SESSIONS_DIR.glob("*.json"), key = lambda x: x.stat().st_ctime)]

def choose_session():
    while True:
        existing = list_sessions()
        if existing:
            print("Existing Sessions:")
            for i, s in enumerate(existing, 1):
                print(f" {i}.{s}")
            print("\nOptions")
            print(" - Type the number to resume a session")
            print(" - Type a new name to create one")
            print(" - Type 'delete' to remove a session.")
            print(" - Type 'exit' to quit the chatbot")
            choice = input("> ").strip()

            if choice.lower() in ("exit","quit"):
                print("Goodbye !")
                exit()

            if choice.lower() == "delete":
                print("\nWhich session would you like to delete?")
                del_choice = input("Enter number to delete or 'cancel':").strip()
                if del_choice.isdigit() and 1 <= int(del_choice) <= len(existing):
                    del_session = existing[int(del_choice) - 1]
                    os.remove(SESSIONS_DIR / f"{del_session}.json")
                    print(f"Deleted Session: {del_session}\n")
                elif del_choice.lower() == "cancel":
                    print("Cancelled Deletion.\n")
                else:
                    print("Invalid Input. Try again. \n")
                continue
            elif choice.isdigit() and 1 <= int(choice) <= len(existing):
                return existing[int(choice) - 1]
            
            if choice == "":
                print("Session name cannot be empty.\n")
                continue
            
            return choice
        
        else:
            print("No sessions yet. Enter a name to create one:")
            choice = input("> ").strip()
            if choice.lower() in ("exit","quit"):
                print("Goodbye !")
                exit()
            if choice == "":
                print("Session name cannot be empty. \n")
                continue
            return choice
              
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

    if user_input.lower().startswith("/rename"):
        new_name = input("Enter new name for this session: ").strip()
        new_file = SESSIONS_DIR / f"{new_name}.json"
        if new_file.exists():
            print("A session with that name already exists.\n")
        else:
            session_file.rename(new_file)
            session_id = new_name
            session_file = new_file    
            print(f"Session renamed to: {new_name}\n")
        continue    

    memory.chat_memory.add_user_message(user_input)
    history_data.append({"role":"user",
                         "content":user_input,
                         "timestamp": datetime.now().isoformat()
                        })

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
    history_data.append({"role":"ai",
                         "content":response,
                         "timestamp": datetime.now().isoformat()
                        })

    session_file.write_text(json.dumps(history_data, ensure_ascii=False,indent = 2),encoding = "utf-8")    

