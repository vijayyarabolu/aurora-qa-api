from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import re

app = FastAPI(title="Aurora Question Answering API")

MESSAGES_URL = "https://november7-730026606190.europe-west1.run.app/messages"


class Question(BaseModel):
    question: str


def fetch_messages():
    """Fetch messages from Aurora API."""
    resp = requests.get(MESSAGES_URL, timeout=10)
    data = resp.json()
    # Aurora API returns an object: {"total": int, "items": [ ...message dicts... ]}
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    return None


@app.post("/ask")
def ask(payload: Question):
    question = payload.question.strip()
    print(">>> Incoming question:", question)

    messages = fetch_messages()
    if messages is None:
        return {"answer": "Unable to read messages from Aurora API."}

    # Better name detection: find capitalized tokens from the question
    # and match them against real user names in the messages to avoid
    # picking sentence-start words like "When".
    user_names = list({m.get("user_name", "") for m in messages if m.get("user_name")})
    tokens = re.findall(r"\b[A-Z][a-z]+\b", question)

    best_user = None
    best_score = 0
    for u in user_names:
        score = sum(1 for t in tokens if t.lower() in u.lower())
        if score > best_score:
            best_score = score
            best_user = u

    name = best_user if best_score > 0 else None
    print(">>> Name detected:", name)

    user_msgs = (
        [m for m in messages if name and name.lower() in m.get("user_name", "").lower()]
        if name else messages
    )

    if not user_msgs:
        return {"answer": f"No messages found for {name or 'that person'}."}

    q_lower = question.lower()
    topics = [
        "trip","travel","flight","car","vehicle","restaurant","dinner","lunch",
        "reservation","booking","hotel","villa","concert","tickets",
        "payment","invoice","bill","plan","schedule"
    ]

    for topic in topics:
        if topic in q_lower:
            topic_msgs = [m for m in user_msgs if topic in m.get("message", "").lower()]
            if topic_msgs:
                return {"answer": topic_msgs[-1]["message"]}

    return {"answer": user_msgs[-1]["message"]}


@app.get("/")
def home():
    return {
        "message": "Aurora QA API is live 🚀",
        "usage": {
            "POST /ask": "Send JSON {'question': 'your question'}",
            "GET /ui": "Simple browser UI",
            "GET /test": "API connection test",
        },
    }


@app.get("/test")
def test():
    messages = fetch_messages()
    if not messages:
        return {"status": "error", "detail": "Bad messages format"}
    return {"status": "ok", "count": len(messages), "first_user": messages[0].get("user_name")}


@app.get("/ui", response_class=HTMLResponse)
def ui():
    html = """
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 40px auto;">
        <h2>Aurora Question Answering</h2>
        <form id='qa-form'>
            <input id='question' style='width:100%; padding:8px;' placeholder='Ask a question...'>
            <br><br>
            <button type='submit'>Ask</button>
        </form>
        <h3>Answer</h3>
        <pre id='answer' style='background:#111; color:#0f0; padding:10px;'></pre>
        <script>
            const form = document.getElementById('qa-form');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const q = document.getElementById('question').value;
                const res = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type':'application/json' },
                    body: JSON.stringify({ question: q })
                });
                const data = await res.json();
                document.getElementById('answer').innerText = data.answer || JSON.stringify(data);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
