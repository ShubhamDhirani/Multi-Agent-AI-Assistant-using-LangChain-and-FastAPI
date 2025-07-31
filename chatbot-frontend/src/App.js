import React, { useState } from "react";
import axios from "axios";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState("default");

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages([...messages, { role: "user", content: input }]);
    setInput("");
    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        session_id: sessionId,
        user_input: input,
      });
      setMessages((msgs) => [
        ...msgs,
        { role: "ai", content: res.data.response },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { role: "ai", content: "Error: Could not get response." },
      ]);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>Chatbot</h2>
      <div style={{ border: "1px solid #ccc", padding: 10, minHeight: 300 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ margin: "8px 0" }}>
            <b>{msg.role === "user" ? "You" : "Bot"}:</b> {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={{ width: "80%" }}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        placeholder="Type your message..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default App;