from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import pickle
import random
import threading
import time
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, 'onepulse.db')
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')

app = Flask(__name__, static_folder='../Frontend', static_url_path='')
CORS(app)

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            hashtags TEXT,
            caption TEXT,
            image_url TEXT,
            niche TEXT DEFAULT 'general',
            scheduled_time TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            posted_at TEXT
        );
    ''')
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────
class OnePulseModel:
    HASHTAG_BANK = {
        'youtube': {'general': ['#YouTube','#Trending','#Subscribe']},
        'instagram': {'general': ['#Instagram','#Explore','#Reels']}
    }

    def predict_best_time(self, platform, niche='general', days_ahead=1):
        base = datetime.now() + timedelta(days=days_ahead)
        return base.replace(hour=12, minute=0, second=0)

    def generate_hashtags(self, platform, niche='general', count=5):
        return self.HASHTAG_BANK.get(platform, {}).get('general', [])

    def generate_caption(self, platform, title, description, niche='general'):
        return f"{title}\n\n{description}"

# ✅ IMPORTANT: LOAD MODEL GLOBALLY
def load_model():
    try:
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    except:
        m = OnePulseModel()
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(m, f)
        return m

model = load_model()

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route('/')
def home():
    return send_from_directory('../Frontend', 'index.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (platform,title,description) VALUES (?,?,?)",
        (data['platform'], data['title'], data.get('description'))
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    init_db()

    scheduler = threading.Thread(target=lambda: None, daemon=True)
    scheduler.start()

    app.run(host="0.0.0.0", port=10000)