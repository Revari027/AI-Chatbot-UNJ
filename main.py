from groq import Groq
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import timedelta
import uuid

app = Flask(__name__)
app.secret_key = "replace_with_a_strong_secret_key_revario"
app.permanent_session_lifetime = timedelta(days=7)

# Izinkan Next.js
CORS(app, supports_credentials=True)

AI_KEY = ""
client = Groq(api_key=AI_KEY)


# -------------------- SYSTEM RULE --------------------
SYSTEM_RULE = (
    "Kamu adalah AI chatbot khusus untuk mata kuliah PSTI dan Konsep Pemrograman.\n\n"
    "Kamu hanya boleh menjawab topik berikut:\n"
    "- PSTI\n"
    "- Konsep Pemrograman\n"
    "- Struktur Data Dasar\n"
    "- Algoritma Dasar\n"
    "- Dasar pemrograman (variabel, tipe data, loop)\n\n"
    "Jika di luar topik → jawab: "
    "\"Maaf, saya hanya bisa menjawab pertanyaan tentang mata kuliah PSTI dan Konsep Pemrograman.\"\n\n"
    "Jika user bertanya 'kamu dibuat oleh siapa' → jawab: 'Saya dibuat oleh Revario.'\n\n"
    "Jika ditanya 'siapa Revario' → jawab:\n"
    "\"Revario adalah seorang mahasiswa UNJ Prodi PTIK yang tergabung di dalam bocah bocahan The Baba's. "
    "Berikut list bocah bocahan the baba's:\n"
    "1.el bayi\n2.el makassar\n3.el kemayoran\n4.el alexander\n5.el cildeug\n6.el bintara\n"
    "7.el khudri\n8.el decul\n9.el kebon nanas\n10.el ketang\n11.el putsal\n12.el coki pardede\n"
    "13.el gontor\n14.el piala\n15.el belah tengah\n16.el pingpong\"\n\n"
    "Jika ada typo, perbaiki dan tetap jawab.\n"
    "Jawab singkat, padat, dan jelas."
)


# -------------------- CHAT SYSTEM --------------------
def save_chats():
    session.modified = True


def init_chats():
    if "chats" not in session:
        session["chats"] = {}
    if "current_chat_id" not in session:
        new_id = str(uuid.uuid4())
        session["chats"][new_id] = {"name": "Chat Baru", "history": []}
        session["current_chat_id"] = new_id
    save_chats()


def get_current_chat():
    init_chats()
    cid = session["current_chat_id"]
    return cid, session["chats"][cid]


# -------------------- ROUTES --------------------
@app.route("/chats", methods=["GET"])
def get_chats():
    init_chats()
    return jsonify(session["chats"])


@app.route("/chat/new", methods=["POST"])
def new_chat():
    init_chats()
    cid = str(uuid.uuid4())
    session["chats"][cid] = {"name": "Chat Baru", "history": []}
    session["current_chat_id"] = cid
    save_chats()
    return jsonify({"id": cid})


@app.route("/chat/rename", methods=["POST"])
def rename_chat():
    init_chats()
    cid = request.form.get("id")
    name = request.form.get("name")

    if cid in session["chats"]:
        session["chats"][cid]["name"] = name
        save_chats()
        return jsonify({"ok": True})

    return jsonify({"error": "Chat not found"}), 404


@app.route("/chat/delete", methods=["POST"])
def delete_chat():
    init_chats()
    cid = request.form.get("id")

    if cid in session["chats"]:
        session["chats"].pop(cid)

        # jika chat aktif terhapus
        if session["current_chat_id"] == cid:
            if session["chats"]:
                session["current_chat_id"] = next(iter(session["chats"]))
            else:
                session.pop("current_chat_id")

        save_chats()
        return jsonify({"ok": True})

    return jsonify({"error": "Chat not found"}), 404


@app.route("/chat/set", methods=["POST"])
def set_chat():
    init_chats()
    cid = request.form.get("id")

    if cid in session["chats"]:
        session["current_chat_id"] = cid
        save_chats()
        return jsonify({"ok": True})

    return jsonify({"error": "Chat not found"}), 404


@app.route("/history", methods=["GET"])
def history():
    init_chats()
    cid, chat = get_current_chat()
    return jsonify({"id": cid, "history": chat["history"]})


# -------------------- AI FUNCTION --------------------
def ask_ai(user_msg, chat):
    chat["history"].append({"role": "user", "content": user_msg})

    messages = [{"role": "system", "content": SYSTEM_RULE}] + chat["history"]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        ai_reply = response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        ai_reply = "AI bermasalah."

    chat["history"].append({"role": "assistant", "content": ai_reply})
    save_chats()
    return ai_reply


@app.route("/send", methods=["POST"])
def send_message():
    init_chats()
    user_text = request.form.get("message", "").strip()
    if not user_text:
        return jsonify({"error": "Pesan kosong"}), 400

    cid, chat = get_current_chat()
    reply = ask_ai(user_text, chat)
    return jsonify({"reply": reply})


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
