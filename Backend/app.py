"""
app.py — OnePulse Backend
Flask API + SQLite + Background Scheduler + Mock Publisher

Run:
    python app.py

Then open Frontend/index.html in your browser.
"""

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
CORS(app)   # allow requests from index.html (different origin)


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
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            platform       TEXT    NOT NULL,
            title          TEXT    NOT NULL,
            description    TEXT,
            hashtags       TEXT,
            caption        TEXT,
            image_url      TEXT,
            niche          TEXT    DEFAULT 'general',
            scheduled_time TEXT,
            status         TEXT    DEFAULT 'scheduled',
            created_at     TEXT    DEFAULT CURRENT_TIMESTAMP,
            posted_at      TEXT
        );
    ''')
    conn.commit()
    conn.close()
    print("✅ Database ready → onepulse.db")


# ─────────────────────────────────────────────
# ML MODEL
# ─────────────────────────────────────────────
class OnePulseModel:
    """
    Smart scheduling + content recommendation model.
    Rule-based heuristics — swap predict_best_time() with a real
    sklearn/TF model once you have engagement data to train on.
    """

    HASHTAG_BANK = {
        'youtube': {
            'general':   ['#YouTube', '#Viral', '#Trending', '#Subscribe', '#Creator', '#ContentCreator'],
            'tech':      ['#Tech', '#TechTips', '#Coding', '#Developer', '#AI', '#MachineLearning'],
            'lifestyle': ['#Lifestyle', '#Vlog', '#DayInMyLife', '#Aesthetic', '#MindfulLiving', '#Motivation'],
            'fitness':   ['#Fitness', '#WorkoutMotivation', '#GymLife', '#Health', '#FitFam', '#Cardio'],
            'food':      ['#FoodLovers', '#Cooking', '#Recipe', '#Foodie', '#HomeCook', '#EasyRecipes'],
            'art':       ['#Art', '#Creative', '#Handmade', '#DIY', '#Craft', '#Crochet'],
        },
        'instagram': {
            'general':   ['#Instagram', '#InstaGood', '#PhotoOfTheDay', '#Explore', '#Reels', '#Trending'],
            'tech':      ['#TechLife', '#Innovation', '#StartupLife', '#SoftwareEngineer', '#MacSetup', '#Coding'],
            'lifestyle': ['#LifestyleBlogger', '#GoodVibes', '#Mindfulness', '#SelfCare', '#DailyInspo', '#Wellness'],
            'fitness':   ['#FitnessMotivation', '#BodyTransformation', '#ActiveLife', '#Wellness', '#Sweat', '#Gym'],
            'food':      ['#FoodPhotography', '#EatWell', '#CleanEating', '#Brunch', '#FoodBlogger', '#Yummy'],
            'art':       ['#ArtOfInstagram', '#HandmadeWithLove', '#CrochetCommunity', '#Crafting', '#Maker', '#DIY'],
        }
    }

    CAPTION_TEMPLATES = {
        'youtube': [
            "🎬 {title}\n\n{description}\n\nDon't forget to like, comment & subscribe! 👇",
            "✨ {description}\n\nNew video is LIVE! Watch till the end 🔥\n\n{title}",
            "💡 {title}\n\n{description}\n\nHit the bell 🔔 so you never miss an upload!",
        ],
        'instagram': [
            "✨ {description}\n\nSave this post for later! 💾",
            "💫 {title}\n\n{description}\n\nDouble tap if you agree! ❤️",
            "🌟 {description}\n\nTag someone who needs to see this! 👇",
        ]
    }

    BEST_HOURS = {
        'youtube':   [14, 15, 16, 18, 19, 20],
        'instagram': [7, 8, 11, 12, 17, 18, 19, 21],
    }

    NICHE_WEIGHTS = {
        'tech':      {'youtube': 0.90, 'instagram': 0.80},
        'lifestyle': {'youtube': 0.85, 'instagram': 0.95},
        'fitness':   {'youtube': 0.88, 'instagram': 0.93},
        'food':      {'youtube': 0.82, 'instagram': 0.97},
        'art':       {'youtube': 0.80, 'instagram': 0.91},
        'general':   {'youtube': 0.75, 'instagram': 0.80},
    }

    def predict_best_time(self, platform, niche='general', days_ahead=1):
        base   = datetime.now() + timedelta(days=days_ahead)
        hour   = random.choice(self.BEST_HOURS.get(platform, [12, 18]))
        minute = random.choice([0, 15, 30])
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def generate_hashtags(self, platform, niche='general', count=10):
        bank       = self.HASHTAG_BANK.get(platform, {})
        niche_tags = bank.get(niche, bank.get('general', []))
        gen_tags   = bank.get('general', [])
        combined   = list(set(niche_tags + gen_tags))
        return random.sample(combined, min(count, len(combined)))

    def generate_caption(self, platform, title, description, niche='general'):
        templates = self.CAPTION_TEMPLATES.get(platform, self.CAPTION_TEMPLATES['instagram'])
        template  = random.choice(templates)
        caption   = template.format(title=title, description=description or title)
        hashtags  = self.generate_hashtags(platform, niche, count=6)
        return caption + '\n\n' + ' '.join(hashtags)

    def get_optimal_schedule(self, platform, niche='general', count=5):
        weight = self.NICHE_WEIGHTS.get(niche, {}).get(platform, 0.75)
        slots  = []
        for i in range(1, count + 1):
            t     = self.predict_best_time(platform, niche, days_ahead=i)
            score = round(weight * random.uniform(0.85, 1.0), 2)
            slots.append({
                'datetime': t.isoformat(),
                'label':    t.strftime('%A, %b %d at %I:%M %p'),
                'score':    min(score, 0.99),
            })
        slots.sort(key=lambda x: x['score'], reverse=True)
        return slots


def load_model():
    try:
        with open(MODEL_PATH, 'rb') as f:
            m = pickle.load(f)
        print("✅ ML model loaded from model.pkl")
        return m
    except Exception:
        m = OnePulseModel()
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(m, f)
        print("✅ ML model created & saved to model.pkl")
        return m


# ─────────────────────────────────────────────
# MOCK PUBLISHERS
# ─────────────────────────────────────────────
def mock_publish_instagram(post):
    time.sleep(0.4)
    success = random.random() > 0.10   # 90 % success rate
    return {
        'success':      success,
        'mock_post_id': f'IG_{random.randint(100000, 999999)}' if success else None,
        'error':        None if success else 'Rate limit exceeded (mock)',
    }


def mock_publish_youtube(post):
    time.sleep(0.4)
    success = random.random() > 0.05   # 95 % success rate
    return {
        'success':       success,
        'mock_video_id': f'YT_{random.randint(100000, 999999)}' if success else None,
        'error':         None if success else 'Upload failed (mock)',
    }


def publish_post(post_dict):
    if post_dict['platform'] == 'instagram':
        return mock_publish_instagram(post_dict)
    return mock_publish_youtube(post_dict)


# ─────────────────────────────────────────────
# BACKGROUND SCHEDULER
# ─────────────────────────────────────────────
def scheduler_loop():
    """Checks every 60 s — auto-publishes posts whose time has passed."""
    while True:
        try:
            conn = get_db()
            now  = datetime.now().isoformat()
            due  = conn.execute(
                "SELECT * FROM posts WHERE status='scheduled' AND scheduled_time <= ?",
                (now,)
            ).fetchall()

            for row in due:
                post       = dict(row)
                result     = publish_post(post)
                new_status = 'posted' if result['success'] else 'failed'
                conn.execute(
                    "UPDATE posts SET status=?, posted_at=? WHERE id=?",
                    (new_status, datetime.now().isoformat(), post['id'])
                )
                icon = '✅' if result['success'] else '❌'
                print(f"{icon} Auto-published [{post['platform']}] \"{post['title']}\" → {new_status}")

            if due:
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  Scheduler error: {e}")

        time.sleep(60)


# ─────────────────────────────────────────────
# OPTIONAL: Serve index.html directly from Flask
# ─────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory('../Frontend', 'index.html')


# ─────────────────────────────────────────────
# API ROUTES — POSTS
# ─────────────────────────────────────────────

@app.route('/api/posts', methods=['GET'])
def get_posts():
    platform = request.args.get('platform')
    status   = request.args.get('status')

    query, params = "SELECT * FROM posts WHERE 1=1", []
    if platform:
        query += " AND platform=?";  params.append(platform)
    if status:
        query += " AND status=?";    params.append(status)
    query += " ORDER BY scheduled_time ASC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json(silent=True) or {}

    platform = (data.get('platform') or '').strip()
    title    = (data.get('title')    or '').strip()

    if not platform: return jsonify({'error': 'platform is required'}), 400
    if not title:    return jsonify({'error': 'title is required'}),    400

    description    = data.get('description', '')
    niche          = data.get('niche', 'general')
    image_url      = data.get('image_url', '')
    scheduled_time = data.get('scheduled_time')

    # Auto-generate if not provided by the user
    caption  = data.get('caption')  or model.generate_caption(platform, title, description, niche)
    hashtags = data.get('hashtags') or ' '.join(model.generate_hashtags(platform, niche))

    if not scheduled_time:
        scheduled_time = model.predict_best_time(platform, niche).isoformat()

    conn   = get_db()
    cur    = conn.execute(
        '''INSERT INTO posts
           (platform, title, description, hashtags, caption, image_url, niche, scheduled_time, status)
           VALUES (?,?,?,?,?,?,?,?,'scheduled')''',
        (platform, title, description, hashtags, caption, image_url, niche, scheduled_time)
    )
    pid = cur.lastrowid
    conn.commit()
    post = dict(conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone())
    conn.close()
    return jsonify(post), 201


@app.route('/api/posts/<int:pid>', methods=['GET'])
def get_post(pid):
    conn = get_db()
    row  = conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row: return jsonify({'error': 'Post not found'}), 404
    return jsonify(dict(row))


@app.route('/api/posts/<int:pid>', methods=['PUT'])
def update_post(pid):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    conn.execute(
        '''UPDATE posts SET title=?, description=?, hashtags=?, caption=?,
           image_url=?, scheduled_time=?, status=?, niche=? WHERE id=?''',
        (data.get('title'), data.get('description'), data.get('hashtags'),
         data.get('caption'), data.get('image_url'), data.get('scheduled_time'),
         data.get('status', 'scheduled'), data.get('niche', 'general'), pid)
    )
    conn.commit()
    post = dict(conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone())
    conn.close()
    return jsonify(post)


@app.route('/api/posts/<int:pid>', methods=['DELETE'])
def delete_post(pid):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Post deleted'})


@app.route('/api/posts/<int:pid>/publish', methods=['POST'])
def publish_now(pid):
    conn = get_db()
    row  = conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404

    post   = dict(row)
    result = publish_post(post)
    status = 'posted' if result['success'] else 'failed'

    conn.execute(
        "UPDATE posts SET status=?, posted_at=? WHERE id=?",
        (status, datetime.now().isoformat(), pid)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': result['success'], 'status': status, 'result': result})


# ─────────────────────────────────────────────
# API ROUTES — STATS
# ─────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    platform = request.args.get('platform')
    conn     = get_db()

    where  = "WHERE platform=?" if platform else "WHERE 1=1"
    params = [platform] if platform else []

    total     = conn.execute(f"SELECT COUNT(*) FROM posts {where}",                     params).fetchone()[0]
    scheduled = conn.execute(f"SELECT COUNT(*) FROM posts {where} AND status='scheduled'", params).fetchone()[0]
    posted    = conn.execute(f"SELECT COUNT(*) FROM posts {where} AND status='posted'",    params).fetchone()[0]
    failed    = conn.execute(f"SELECT COUNT(*) FROM posts {where} AND status='failed'",    params).fetchone()[0]
    conn.close()

    return jsonify({'total': total, 'scheduled': scheduled, 'posted': posted, 'failed': failed})


# ─────────────────────────────────────────────
# API ROUTES — AI / ML
# ─────────────────────────────────────────────

@app.route('/api/ai/recommend', methods=['POST'])
def ai_recommend():
    """
    Frontend calls this when user clicks
    "✨ Generate AI Captions, Hashtags & Best Times".
    Returns caption, hashtags list, and best_times list.
    """
    data = request.get_json(silent=True) or {}

    platform    = data.get('platform',    'instagram')
    niche       = data.get('niche',       'general')
    title       = data.get('title',       'My Post')
    description = data.get('description', '')

    caption    = model.generate_caption(platform, title, description, niche)
    hashtags   = model.generate_hashtags(platform, niche, count=12)
    best_times = model.get_optimal_schedule(platform, niche, count=5)

    return jsonify({
        'caption':    caption,
        'hashtags':   hashtags,
        'best_times': best_times,
    })


@app.route('/api/ai/best-times', methods=['GET'])
def ai_best_times():
    platform = request.args.get('platform', 'instagram')
    niche    = request.args.get('niche',    'general')
    return jsonify(model.get_optimal_schedule(platform, niche, count=7))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    init_db()

    # Load (or create) the ML model
    model = load_model()

    # Start background auto-publisher
    scheduler = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler.start()

    print("\n" + "="*50)
    print("  ⚡ OnePulse backend is running!")
    print("  🌐 URL  → http://localhost:5000")
    print("  📁 Open Frontend/index.html in your browser")
    print("  🛑 Stop → Ctrl+C")
    print("="*50 + "\n")

    app.run(debug=True, use_reloader=False, port=5000)