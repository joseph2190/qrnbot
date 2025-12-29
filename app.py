from flask import Flask, request
import requests
import sqlite3
import os

TOKEN = os.environ["BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

conn = sqlite3.connect("votes.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS votes (
    user_id INTEGER PRIMARY KEY,
    choice TEXT
)
""")
conn.commit()

def send_message(chat_id, text, reply_markup=None):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json

    if "callback_query" in update:
        cq = update["callback_query"]
        user_id = cq["from"]["id"]
        chat_id = cq["message"]["chat"]["id"]
        choice = cq["data"]

        cur.execute("SELECT choice FROM votes WHERE user_id=?", (user_id,))
        if cur.fetchone():
            send_message(chat_id, "You already voted.")
        else:
            cur.execute("INSERT INTO votes VALUES (?,?)", (user_id, choice))
            conn.commit()
            send_message(chat_id, f"Vote saved: {choice}")

        return "OK"

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        keyboard = {
            "inline_keyboard": [
                [{"text": "👍 YES", "callback_data": "YES"}],
                [{"text": "👎 NO", "callback_data": "NO"}]
            ]
        }
        send_message(chat_id, "Vote now:", keyboard)

    return "OK"

@app.route("/")
def index():
    return "Bot alive"
