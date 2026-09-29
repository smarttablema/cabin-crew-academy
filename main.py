import os
import difflib
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aero Crew Elite Academy", version="11.4.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_users_v11 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            username VARCHAR(50) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            role VARCHAR(20) DEFAULT 'student',
            crew_avatar VARCHAR(20) DEFAULT 'steward',
            active_skin VARCHAR(100) DEFAULT 'Standard Aviator Suit',
            group_code VARCHAR(50) DEFAULT 'EASA-ALPHA-1',
            reports_count INT DEFAULT 0,
            is_banned BOOLEAN DEFAULT FALSE,
            xp_points INT DEFAULT 1200,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 18,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_friendships_v11 (
            id SERIAL PRIMARY KEY,
            sender_username VARCHAR(50),
            receiver_username VARCHAR(50),
            status VARCHAR(20) DEFAULT 'accepted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_chat_messages_v11 (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            sender_username VARCHAR(50),
            sender_name VARCHAR(100),
            sender_avatar VARCHAR(20),
            msg_type VARCHAR(20) DEFAULT 'text',
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_shop_skins_v11 (
            id SERIAL PRIMARY KEY,
            category VARCHAR(20),
            tier_level VARCHAR(30),
            skin_name VARCHAR(50),
            cost INT,
            preview_svg TEXT,
            desc_en TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_curriculum_v11 (
            id SERIAL PRIMARY KEY,
            year_level INT,
            node_order INT,
            category VARCHAR(50),
            theme_icon VARCHAR(10),
            title_en TEXT,
            title_ar TEXT,
            title_fr TEXT,
            content_en TEXT,
            content_ar TEXT,
            content_fr TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_exercises_v11 (
            id SERIAL PRIMARY KEY,
            year_level INT,
            node_order INT,
            exercise_type VARCHAR(30),
            prompt_en TEXT,
            prompt_ar TEXT,
            prompt_fr TEXT,
            options TEXT[],
            correct_answer TEXT,
            hint_en TEXT
        );
    """)

    cur.execute("""
        INSERT INTO aero_shop_skins_v11 (category, tier_level, skin_name, cost, preview_svg, desc_en)
        VALUES 
        ('male', 'Free', 'Standard Aviator Suit', 0, '👔', 'Standard clean cadet training uniform.'),
        ('male', 'Budget', 'Junior Cabin Steward', 80, '👔⭐', 'Sleek grey vest with silver airline pin.'),
        ('male', 'Professional', 'Senior Purser Uniform', 500, '🎖️👔', 'Tailored navy suit with supervisor epaulets.'),
        ('male', 'Ultra-Elite Luxury', 'Supreme Gold Commander (10k)', 10000, '👑👨‍✈️✨', 'Legendary gold-threaded four-stripe captain jacket and royal aviation cap.'),
        
        ('female', 'Free', 'Standard Hostess Attire', 0, '👗', 'Standard elegant academy skirt suit.'),
        ('female', 'Budget', 'Junior Cabin Hostess', 80, '👗⭐', 'Professional airline service dress.'),
        ('female', 'Professional', 'Lead Purser Silk Scarf', 500, '🧣💎', 'Signature designer silk scarf and platinum wing brooch.'),
        ('female', 'Ultra-Elite Luxury', 'Supreme Chief Captain (10k)', 10000, '👑👩‍✈️✨', 'Legendary gold epaulets, custom captain hat, and diamond aviation wings.')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO aero_curriculum_v11 (year_level, node_order, category, theme_icon, title_en, title_ar, title_fr, content_en, content_ar, content_fr)
        VALUES 
        (1, 1, 'SEP', '✈️', 'Step 1: EASA Framework', 'Step 1: EASA Framework', 'Étape 1 : Cadre EASA', 'Introduction to EASA regulations governing cabin crew operational safety duties.', 'Introduction to EASA regulations.', 'Introduction aux réglementations.'),
        (1, 2, 'SEP', '🚪', 'Step 2: Emergency Exits & Door Arming', 'Step 2: Exits', 'Étape 2 : Portes', 'Mandatory pre-flight checks and slide arming procedures.', 'Pre-flight checks.', 'Vérifications pré-vol.'),
        (2, 1, 'CRM', '🤝', 'Step 1: Advanced CRM', 'Step 1: CRM', 'Étape 1 : CRM', 'Multicultural flight deck and cabin crew communication dynamics.', 'Communication dynamics.', 'Dynamique de communication.')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO aero_exercises_v11 (year_level, node_order, exercise_type, prompt_en, prompt_ar, prompt_fr, options, correct_answer, hint_en)
        VALUES 
        (1, 1, 'mcq', 'What regulatory agency governs European Union commercial cabin crew operations?', 'What agency governs EU operations?', 'Quelle agence réglemente les opérations en UE ?', ARRAY['FAA', 'EASA', 'ICAO', 'CAA'], 'EASA', 'European Union Aviation Safety Agency.'),
        (1, 1, 'translate', 'Translate "Pre-flight Check" to Arabic:', 'Translate Pre-flight Check:', 'Traduisez Pre-flight Check :', ARRAY['فحص ما قبل الرحلة', 'إخلاء الطوارئ', 'مقياس الارتفاع', 'قمرة القيادة'], 'فحص ما قبل الرحلة', 'Mandatory inspection before departure.'),
        (1, 1, 'voice', 'Repeat aloud the official cabin crew safety authority term:', 'Repeat term:', 'Répétez le terme :', ARRAY['EASA Part-CC', 'FAA Part-91', 'ICAO Annex 6', 'JAA Ops'], 'EASA Part-CC', 'European safety regulation standard.')
        ON CONFLICT DO NOTHING;
    """)
    conn.commit()
    cur.close()
    conn.close()

class RegisterModel(BaseModel):
    phone_number: str
    username: str
    full_name: str
    password: str
    recovery_pin: str
    role: str = 'student'
    crew_avatar: str = 'steward'
    group_code: str = 'EASA-ALPHA-1'

class LoginModel(BaseModel):
    phone_number: str
    password: str

class PasswordChangeModel(BaseModel):
    phone_number: str
    recovery_pin: str
    old_password: str
    new_password: str

class ProfileUpdateModel(BaseModel):
    phone_number: str
    crew_avatar: str
    active_skin: str

class AddFriendModel(BaseModel):
    sender_username: str
    receiver_username: str

class ChatMessageModel(BaseModel):
    group_code: str
    sender_username: str
    sender_name: str
    sender_avatar: str
    msg_type: str = 'text'
    content: str

class ReportUserMoel(BaseModel):
    reported_username: str

class BuySkinModel(BaseModel):
    phone_number: str
    skin_name: str
    cost: int

class DrillAttemptModel(BaseModel):
    phone_number: str
    exercise_id: int
    user_answer: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v11 WHERE phone_number = %s OR username = %s;", (data.phone_number, data.username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number or unique username already taken.")
    
    cur.execute(
        "INSERT INTO aero_users_v11 (phone_number, username, full_name, password, recovery_pin, role, crew_avatar, group_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.phone_number, data.username, data.full_name, data.password, data.recovery_pin, data.role, data.crew_avatar, data.group_code)
    )
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.post("/api/login")
def login(data: LoginModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v11 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if user["is_banned"]:
        raise HTTPException(status_code=403, detail="Account is banned due to community reports.")
    return {"status": "success", "user": user}

@app.post("/api/user/password-change")
def change_password(data: PasswordChangeModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v11 WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    if user["recovery_pin"] != data.recovery_pin:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Incorrect recovery PIN.")
    if user["password"] != data.old_password:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Incorrect old password.")
    
    cur.execute("UPDATE aero_users_v11 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/user/profile-update")
def update_profile(data: ProfileUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE aero_users_v11 SET crew_avatar = %s, active_skin = %s WHERE phone_number = %s RETURNING *;",
        (data.crew_avatar, data.active_skin, data.phone_number)
    )
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.get("/api/academy/content")
def get_academy_content(group_code: str = 'EASA-ALPHA-1'):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_curriculum_v11 ORDER BY year_level ASC, node_order ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM aero_exercises_v11 ORDER BY year_level ASC, node_order ASC, id ASC;")
    exercises = cur.fetchall()
    cur.execute("SELECT * FROM aero_shop_skins_v11 ORDER BY cost ASC;")
    skins = cur.fetchall()
    cur.execute("SELECT * FROM aero_chat_messages_v11 WHERE group_code = %s ORDER BY id DESC LIMIT 50;", (group_code,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "exercises": exercises, "skins": skins, "messages": messages[::-1]}

@app.post("/api/friends/add")
def add_friend(data: AddFriendModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v11 WHERE username = %s;", (data.receiver_username,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Username not found.")
    
    cur.execute(
        "INSERT INTO aero_friendships_v11 (sender_username, receiver_username, status) VALUES (%s, %s, 'accepted') RETURNING *;",
        (data.sender_username, data.receiver_username)
    )
    rel = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "friend": rel}

@app.get("/api/friends/list")
def get_friends(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.username, u.full_name, u.crew_avatar, u.active_skin 
        FROM aero_users_v11 u 
        JOIN aero_friendships_v11 f ON (f.receiver_username = u.username OR f.sender_username = u.username)
        WHERE (f.sender_username = %s OR f.receiver_username = %s) AND u.username != %s AND f.status = 'accepted';
    """, (username, username, username))
    friends = cur.fetchall()
    cur.close()
    conn.close()
    return {"friends": friends}

@app.post("/api/chat/send")
def send_chat_message(data: ChatMessageModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_chat_messages_v11 (group_code, sender_username, sender_name, sender_avatar, msg_type, content) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.group_code, data.sender_username, data.sender_name, data.sender_avatar, data.msg_type, data.content)
    )
    msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": msg}

@app.post("/api/user/report")
def report_user(data: ReportUserMoel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_users_v11 SET reports_count = reports_count + 1 WHERE username = %s RETURNING reports_count, username;", (data.reported_username,))
    res = cur.fetchone()
    if res and res["reports_count"] >= 40:
        cur.execute("UPDATE aero_users_v11 SET is_banned = TRUE WHERE username = %s;", (data.reported_username,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "reports": res["reports_count"] if res else 0}

@app.post("/api/shop/buy")
def buy_skin(data: BuySkinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v11 WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    if user["xp_points"] < data.cost:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough XP stars!")
    
    new_xp = user["xp_points"] - data.cost
    cur.execute("UPDATE aero_users_v11 SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated_user}

@app.post("/api/exercise/verify")
def verify_exercise(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_exercises_v11 WHERE id = %s;", (data.exercise_id,))
    ex = cur.fetchone()
    cur.execute("SELECT * FROM aero_users_v11 WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not ex or not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found.")
    
    correct = data.user_answer.strip().lower() == ex["correct_answer"].strip().lower()
    if correct:
        cur.execute("UPDATE aero_users_v11 SET xp_points = xp_points + 30 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": "Perfect execution! +30 XP Stars", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    else:
        new_hearts = max(0, user["hearts"] - 1)
        cur.execute("UPDATE aero_users_v11 SET hearts = %s WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (new_hearts, data.phone_number))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": False, "correct_answer": ex["correct_answer"], "message": f"Incorrect! Official answer: '{ex['correct_answer']}'", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aero Crew Elite Academy</title>
    <link rel="icon" href="https://img.icons8.com/color/48/airplane-take-off.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Tajawal:wght@450;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #020617;
            --surface: #0b0f19;
            --surface-card: #131b2e;
            --surface-card-hover: #1c2844;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.35);
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #1e293b;
            --border-glow: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; pointer-events: auto !important; }
        [dir="rtl"] * { font-family: 'Tajawal', sans-serif !important; }
        
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        
        .app-shell { width: 100%; max-width: 600px; background: var(--surface); border-radius: 36px; padding: 2rem; border: 1px solid var(--border-glow); box-shadow: 0 45px 90px rgba(0, 0, 0, 0.95), 0 0 40px rgba(56, 189, 248, 0.08); position: relative; z-index: 10; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.4rem; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.2rem; color: var(--accent); letter-spacing: -0.5px; }
        .brand-title img { width: 34px; height: 34px; filter: drop-shadow(0 0 10px var(--accent-glow)); }
        
        .header-controls { display: flex; align-items: center; gap: 6px; }
        .header-icon-btn { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 10px; width: 36px; height: 36px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: all 0.2s; font-size: 1.05rem; }
        .header-icon-btn:hover { border-color: var(--accent); background: var(--accent-glow); box-shadow: 0 0 15px var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.4rem; color: white; }
        p.sub-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.4rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem; letter-spacing: 0.8px; }
        input, select, textarea { width: 100%; padding: 0.9rem 1.1rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 0.92rem; margin-bottom: 1rem; outline: none; transition: all 0.2s; position: relative; z-index: 20; }
        input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 0.98rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s, box-shadow 0.2s; box-shadow: 0 6px 20px var(--accent-glow); position: relative; z-index: 20; }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.95; box-shadow: 0 8px 25px var(--accent-glow); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; font-size: 0.82rem; position: relative; z-index: 20; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 700; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        .mascot-banner { display: flex; align-items: center; gap: 14px; background: linear-gradient(135deg, rgba(56,189,248,0.18) 0%, rgba(2,132,199,0.06) 100%); border: 1px solid rgba(56,189,248,0.35); padding: 0.85rem 1.1rem; border-radius: 18px; margin-bottom: 1.1rem; }
        .mascot-avatar { font-size: 2.6rem; animation: bounceMascot 2s infinite ease-in-out; }
        @keyframes bounceMascot { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
        .mascot-speech { font-size: 0.82rem; color: #bae6fd; font-weight: 700; line-height: 1.4; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.85rem 1.1rem; border-radius: 18px; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; }
        .stat-item { font-weight: 800; font-size: 0.82rem; display: flex; align-items: center; gap: 5px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.1rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275); position: relative; z-index: 20; }
        .mode-tile:hover { border-color: var(--accent); background: var(--surface-card-hover); transform: translateY(-3px); box-shadow: 0 10px 25px rgba(56,189,248,0.15); }
        .mode-tile h4 { font-size: 0.85rem; font-weight: 800; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 22px; padding: 1.5rem; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; position: relative; min-height: 270px; }
        
        .roadmap-path { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 15px 0; max-height: 280px; overflow-y: auto; }
        .roadmap-node { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); display: flex; flex-direction: column; justify-content: center; align-items: center; font-weight: 900; font-size: 1.1rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s; position: relative; border: 3px solid #bae6fd; z-index: 25; }
        .roadmap-node:hover { transform: scale(1.12); box-shadow: 0 0 35px var(--accent); }

        .chat-container { display: flex; flex-direction: column; height: 320px; background: var(--bg-deep); border-radius: 16px; border: 1px solid var(--border-glow); overflow: hidden; }
        .chat-messages { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .chat-bubble { max-width: 78%; padding: 9px 12px; border-radius: 14px; font-size: 0.84rem; line-height: 1.4; position: relative; }
        .chat-bubble.incoming { background: var(--surface-card); color: white; align-self: flex-start; border-bottom-left-radius: 2px; }
        .chat-bubble.outgoing { background: #0284c7; color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
        .chat-input-bar { display: flex; gap: 6px; padding: 10px; background: var(--surface-card); border-top: 1px solid var(--border); align-items: center; }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 14px 28px; border-radius: 35px; font-weight: 800; font-size: 0.9rem; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 6000; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <div id="settings-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); backdrop-filter:blur(8px); display:flex; justify-content:center; align-items:center; z-index:5000; opacity:0; pointer-events:none; transition:opacity 0.25s;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:420px; max-height:85vh; overflow-y:auto; box-shadow:0 30px 60px rgba(0,0,0,0.9);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
                <h3 style="font-size:1.2rem; font-weight:900; color:white;">⚙️️ Profile & Academy Settings</h3>
                <button onclick="closeSettingsModal()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>

            <label>Change Character Avatar</label>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:1rem;">
                <div onclick="selectProfileAvatar('steward')" id="set-card-steward" style="background:var(--bg-deep); border:2px solid var(--border-glow); border-radius:14px; padding:0.9rem; text-align:center; cursor:pointer;">
                    <span style="font-size:1.8rem;">👔</span>
                    <div style="font-size:0.75rem; color:white; font-weight:800; margin-top:4px;">Steward</div>
                </div>
                <div onclick="selectProfileAvatar('hostess')" id="set-card-hostess" style="background:var(--bg-deep); border:2px solid var(--border-glow); border-radius:14px; padding:0.9rem; text-align:center; cursor:pointer;">
                    <span style="font-size:1.8rem;">👗</span>
                    <div style="font-size:0.75rem; color:white; font-weight:800; margin-top:4px;">Hostess</div>
                </div>
            </div>

            <label>Interface Language</label>
            <div style="display:flex; gap:8px; margin-bottom:1.2rem;">
                <button onclick="playAudio('click'); setLanguage('en')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow);">English 🇬🇧</button>
                <button onclick="playAudio('click'); setLanguage('fr')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow);">Français 🇫🇷</button>
                <button onclick="playAudio('click'); setLanguage('ar')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow);">العربية 🇸🇦</button>
            </div>

            <hr style="border:0; border-top:1px solid var(--border); margin:1.2rem 0;">

            <h4 style="font-size:0.9rem; font-weight:800; color:white; margin-bottom:0.8rem;">Secure Password Update</h4>
            <label>Recovery PIN (4-6 digits)</label>
            <input type="password" id="set-pin" placeholder="Enter recovery PIN" maxlength="6" />
            <label>Old Password</label>
            <input type="password" id="set-old-pass" placeholder="Enter current password" />
            <label>New Password</label>
            <input type="password" id="set-new-pass" placeholder="Enter new password" />

            <button class="btn-action" onclick="playAudio('click'); submitPasswordChange()" style="background:var(--warning); color:var(--bg-deep); margin-top:0.4rem;">Update Credentials 🔒</button>
        </div>
    </div>

    <div id="friends-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); backdrop-filter:blur(8px); display:flex; justify-content:center; align-items:center; z-index:5000; opacity:0; pointer-events:none; transition:opacity 0.25s;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:420px; max-height:85vh; overflow-y:auto; box-shadow:0 30px 60px rgba(0,0,0,0.9);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
                <h3 style="font-size:1.2rem; font-weight:900; color:white;">🤝 Cadet Friend Network</h3>
                <button onclick="closeFriendsModal()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>

            <label>Search Friend by Unique Username</label>
            <div style="display:flex; gap:8px; margin-bottom:1rem;">
                <input type="text" id="search-username-input" placeholder="e.g. @killua_s" style="margin-bottom:0;" />
                <button class="btn-action" onclick="playAudio('click'); addFriendByUsername()" style="width:110px; padding:0; font-size:0.85rem;">Add +</button>
            </div>

            <h4 style="font-size:0.85rem; font-weight:800; color:var(--text-muted); margin-bottom:0.6rem; text-transform:uppercase;">Connected Friends Online</h4>
            <div id="friends-list-container" style="display:flex; flex-direction:column; gap:8px; max-height:180px; overflow-y:auto; margin-bottom:1.2rem;"></div>

            <button class="btn-action" onclick="playAudio('click'); openGroupChat()" style="background:var(--success); color:white;">Open Study Group Chat 💬</button>
        </div>
    </div>

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Logo">
                <span id="txt-brand">Aero Crew</span>
            </div>
            <div class="header-controls hidden" id="dash-header-icons">
                <div class="header-icon-btn" onclick="playAudio('click'); openFriendsModal()" title="Friend Invitations">🤝</div>
                <div class="header-icon-btn" onclick="playAudio('click'); openShop()" title="Uniform Boutique">🎁</div>
                <div class="header-icon-btn" onclick="playAudio('click'); openSettingsModal()" title="Settings & Profile">⚙️</div>
            </div>
        </div>

        <div id="screen-login">
            <h2 id="ui-login-title">Cabin Crew Portal</h2>
            <p class="sub-desc" id="ui-login-sub">Access accredited EASA/ICAO professional curriculum.</p>
            
            <label id="lbl-phone">Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label id="lbl-pass">Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn-action" onclick="playAudio('click'); submitLogin()" id="ui-login-btn">Sign In to Simulator</button>
            
            <div class="footer-nav">
                <a onclick="playAudio('click'); navigateTo('screen-register')" id="nav-reg">Create Account</a>
                <a onclick="playAudio('click'); navigateTo('screen-reset')" id="nav-reset">Forgot Password?</a>
            </div>
        </div>

        <div id="screen-register" class="hidden">
            <h2 id="reg-title">Cadet Enrollment</h2>
            <p class="sub-desc" id="reg-sub">Register your official profile and unique username.</p>
            
            <label id="reg-lbl-name">Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label id="reg-lbl-username">Unique Username (e.g. @captain_alex)</label>
            <input type="text" id="reg-username" placeholder="@unique_handle" />

            <label id="reg-lbl-phone">Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label id="reg-lbl-pass">Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label id="reg-lbl-pin">Recovery PIN (4-6 digits)</label>
            <input type="password" id="reg-pin" placeholder="e.g. 2026" maxlength="6" />

            <label id="reg-lbl-avatar">Crew Character</label>
            <select id="reg-avatar">
                <option value="steward">👔 Steward (Male Crew Avatar)</option>
                <option value="hostess">👗 Hostess (Female Crew Avatar)</option>
            </select>
            
            <button class="btn-action" onclick="playAudio('click'); submitRegister()" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); color: white;" id="reg-btn-sub">Initialize Profile</button>
            
            <div class="footer-nav">
                <a onclick="playAudio('click'); navigateTo('screen-login')" id="reg-back">Already have an account? Sign In</a>
            </div>
        </div>

        <div id="screen-reset" class="hidden">
            <h2 id="res-title">Recovery PIN Reset</h2>
            <p class="sub-desc" id="res-sub">Enter your phone and secret recovery PIN.</p>
            
            <label id="res-lbl-phone">Phone Number</label>
            <input type="tel" id="reset-phone" placeholder="e.g. 0612345678" />

            <label id="res-lbl-pin">Secret Recovery PIN</label>
            <input type="password" id="reset-pin" placeholder="Your secret PIN" />

            <label id="res-lbl-new">New Password</label>
            <input type="password" id="reset-new" placeholder="Enter new password" />
            
            <button class="btn-action" onclick="playAudio('click'); submitReset()" style="background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); color: var(--bg-deep);" id="res-btn-sub">Update Credentials</button>
            
            <div class="footer-nav">
                <a onclick="playAudio('click'); navigateTo('screen-login')" id="res-back">Back to Sign In</a>
            </div>
        </div>

        <div id="screen-dashboard" class="hidden">
            <div class="mascot-banner">
                <div class="mascot-avatar" id="mascot-emoji">👔</div>
                <div class="mascot-speech" id="mascot-speech">Reading professional manuals guarantees cadet excellence!</div>
            </div>

            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent); font-weight: 900;">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;" id="dash-skin">Standard Aviator Suit</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">1200</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">18</span></div>
                </div>
            </div>

            <div class="mode-grid">
                <div class="mode-tile" onclick="playAudio('click'); launchLongRoadmap(1)">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4 id="tile-year1">First Year Path</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); launchLongRoadmap(2)">
                    <span style="font-size: 1.4rem;">🏆</span>
                    <h4 id="tile-year2">Second Year Path</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); openGroupChat()">
                    <span style="font-size: 1.4rem;">💬</span>
                    <h4 id="tile-group">Study Group Chat</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); openShop()">
                    <span style="font-size: 1.4rem;">🎁</span>
                    <h4 id="tile-shop">Skin Boutique</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container"></div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="playAudio('click'); resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1;" id="btn-menu">← Hub</button>
                <button class="btn-action" onclick="playAudio('click'); logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1;" id="btn-logout">Logout 🚪</button>
            </div>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('aero_crew_user') || 'null');
        let academyData = { modules: [], exercises: [], skins: [], messages: [] };
        let activeLang = localStorage.getItem('aero_crew_lang') || 'en';
        let currentExerciseList = [];
        let exercisePointer = 0;
        let selectedAvatarSetting = 'steward';

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        function playAudio(type) {
            try {
                if(audioCtx.state === 'suspended') audioCtx.resume();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);

                if(type === 'click') {
                    osc.frequency.setValueAtTime(400, audioCtx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(800, audioCtx.currentTime + 0.05);
                    gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.05);
                    osc.start(); osc.stop(audioCtx.currentTime + 0.05);
                } else if(type === 'success') {
                    osc.frequency.setValueAtTime(523.25, audioCtx.currentTime);
                    osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.08);
                    osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.16);
                    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                    osc.start(); osc.stop(audioCtx.currentTime + 0.3);
                } else if(type === 'error') {
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(200, audioCtx.currentTime);
                    osc.frequency.setValueAtTime(150, audioCtx.currentTime + 0.1);
                    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
                    osc.start(); osc.stop(audioCtx.currentTime + 0.25);
                }
            } catch(e) {}
        }

        const translations = {
            en: {
                loginTitle: "Cabin Crew Portal", loginSub: "Access accredited EASA/ICAO professional curriculum.",
                phoneLbl: "Phone Number", passLbl: "Password", loginBtn: "Sign In to Simulator",
                regNav: "Create Account", resetNav: "Forgot Password?",
                tileYear1: "First Year Path", tileYear2: "Second Year Path", tileGroup: "Study Group Chat", tileShop: "Skin Boutique",
                menuBtn: "← Hub", logoutBtn: "Logout 🚪"
            },
            fr: {
                loginTitle: "Portail Personnel de Cabine", loginSub: "Accédez au programme professionnel accrédité EASA/ICAO.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter au simulateur",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                tileYear1: "Parcours 1ère Année", tileYear2: "Parcours 2nde Année", tileGroup: "Chat de Groupe", tileShop: "Boutique de Skins",
                menuBtn: "← Menu", logoutBtn: "Déconnexion 🚪"
            },
            ar: {
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى المنهج المهني المعتمد من EASA/ICAO.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول للمحاكي",
                regNav: "إنشاء حساب", resetNav: "هل نسيت كلمة المرور؟",
                tileYear1: "مسار السنة الأولى", tileYear2: "مسار السنة الثانية", tileGroup: "دردشة مجموعة الدراسة", tileShop: "متجر الأزياء",
                menuBtn: "← القائمة", logoutBtn: "تسجيل الخروج 🚪"
            }
        };

        window.onload = function() {
            setLanguage(activeLang);
            if(sessionUser) {
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchAcademyContent();
            } else {
                navigateTo('screen-login');
            }
        };

        function updateDashboardUI() {
            document.getElementById('dash-name').innerText = sessionUser.full_name;
            document.getElementById('dash-skin').innerText = sessionUser.active_skin;
            document.getElementById('dash-xp').innerText = sessionUser.xp_points;
            document.getElementById('dash-hearts').innerText = sessionUser.hearts;
            document.getElementById('dash-streak').innerText = sessionUser.streak;
            const emoji = sessionUser.crew_avatar === 'hostess' ? '👗' : '👔';
            document.getElementById('mascot-emoji').innerText = emoji;
        }

        function showToast(text, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = text;
            t.style.background = isError ? 'var(--danger)' : 'var(--success)';
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3500);
        }

        function navigateTo(id) {
            ['screen-login', 'screen-register', 'screen-reset', 'screen-dashboard'].forEach(s => {
                const el = document.getElementById(s);
                if(el) el.classList.add('hidden');
            });
            const target = document.getElementById(id);
            if(target) target.classList.remove('hidden');
            
            const headerIcons = document.getElementById('dash-header-icons');
            if(headerIcons) {
                if(id === 'screen-dashboard') {
                    headerIcons.classList.remove('hidden');
                } else {
                    headerIcons.classList.add('hidden');
                }
            }
        }

        function logoutUser() {
            localStorage.removeItem('aero_crew_user');
            sessionUser = null;
            navigateTo('screen-login');
            showToast('Logged out successfully.');
        }

        function setLanguage(lang) {
            activeLang = lang;
            localStorage.setItem('aero_crew_lang', lang);
            const root = document.getElementById('html-root');
            if(lang === 'ar') root.setAttribute('dir', 'rtl');
            else root.setAttribute('dir', 'ltr');

            const t = translations[lang];
            if(t) {
                document.getElementById('ui-login-title').innerText = t.loginTitle;
                document.getElementById('ui-login-sub').innerText = t.loginSub;
                document.getElementById('lbl-phone').innerText = t.phoneLbl;
                document.getElementById('lbl-pass').innerText = t.passLbl;
                document.getElementById('ui-login-btn').innerText = t.loginBtn;
                document.getElementById('nav-reg').innerText = t.regNav;
                document.getElementById('nav-reset').innerText = t.resetNav;
                document.getElementById('tile-year1').innerText = t.tileYear1;
                document.getElementById('tile-year2').innerText = t.tileYear2;
                document.getElementById('tile-group').innerText = t.tileGroup;
                document.getElementById('tile-shop').innerText = t.tileShop;
                document.getElementById('btn-menu').innerText = t.menuBtn;
                document.getElementById('btn-logout').innerText = t.logoutBtn;
            }
        }

        async function submitRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const username = document.getElementById('reg-username').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();
            const crew_avatar = document.getElementById('reg-avatar').value;

            if(!full_name || !username || !phone_number || !password || !recovery_pin) { showToast('Complete all fields', true); return; }
            if(!username.startsWith('@')) { showToast('Username must start with @', true); return; }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ full_name, username, phone_number, password, recovery_pin, crew_avatar })
            });
            const data = await res.json();
            if(res.ok) {
                showToast('Registration successful! Please sign in.');
                navigateTo('screen-login');
            } else {
                showToast(data.detail || 'Registration failed', true);
            }
        }

        async function submitLogin() {
            const phone_number = document.getElementById('login-phone').value.trim();
            const password = document.getElementById('login-pass').value.trim();
            if(!phone_number || !password) { showToast('Enter credentials', true); return; }

            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number, password })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchAcademyContent();
                showToast('Welcome aboard, Captain ' + sessionUser.full_name + '!');
            } else {
                showToast(data.detail || 'Invalid phone or password', true);
            }
        }

        async function submitReset() {
            const phone_number = document.getElementById('reset-phone').value.trim();
            const recovery_pin = document.getElementById('reset-pin').value.trim();
            const new_password = document.getElementById('reset-new').value.trim();
            if(!phone_number || !recovery_pin || !new_password) { showToast('Complete all fields', true); return; }

            const res = await fetch('/api/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number, recovery_pin, new_password })
            });
            if(res.ok) {
                showToast('Credentials updated successfully!');
                navigateTo('screen-login');
            } else {
                showToast('Invalid recovery PIN', true);
            }
        }

        async function fetchAcademyContent() {
            const res = await fetch('/api/academy/content?group_code=' + sessionUser.group_code);
            academyData = await res.json();
            resetToMenu();
        }

        function resetToMenu() {
            document.getElementById('simulation-box').innerHTML = '<h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3><p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year Path</b> or <b>Second Year Path</b> above to jump into interactive Duolingo-style roadmap exercises.</p>';
        }

        function openSettingsModal() {
            document.getElementById('settings-modal').style.opacity = '1';
            document.getElementById('settings-modal').style.pointerEvents = 'auto';
            selectedAvatarSetting = sessionUser.crew_avatar;
            document.getElementById('set-card-steward').style.borderColor = selectedAvatarSetting === 'steward' ? 'var(--accent)' : 'var(--border-glow)';
            document.getElementById('set-card-hostess').style.borderColor = selectedAvatarSetting === 'hostess' ? 'var(--accent)' : 'var(--border-glow)';
        }
        function closeSettingsModal() {
            document.getElementById('settings-modal').style.opacity = '0';
            document.getElementById('settings-modal').style.pointerEvents = 'none';
        }
        function selectProfileAvatar(avatar) {
            playAudio('click');
            selectedAvatarSetting = avatar;
            document.getElementById('set-card-steward').style.borderColor = avatar === 'steward' ? 'var(--accent)' : 'var(--border-glow)';
            document.getElementById('set-card-hostess').style.borderColor = avatar === 'hostess' ? 'var(--accent)' : 'var(--border-glow)';
            updateProfileAvatarAndSkin(avatar, sessionUser.active_skin);
        }
        async function updateProfileAvatarAndSkin(avatar, skin) {
            const res = await fetch('/api/user/profile-update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, crew_avatar: avatar, active_skin: skin })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast('Profile updated successfully!');
            }
        }
        async function submitPasswordChange() {
            const recovery_pin = document.getElementById('set-pin').value.trim();
            const old_password = document.getElementById('set-old-pass').value.trim();
            const new_password = document.getElementById('set-new-pass').value.trim();
            if(!recovery_pin || !old_password || !new_password) { showToast('Complete all fields', true); return; }

            const res = await fetch('/api/user/password-change', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, recovery_pin, old_password, new_password })
            });
            const data = await res.json();
            if(res.ok) {
                showToast('Password updated securely!');
                closeSettingsModal();
            } else {
                showToast(data.detail || 'Password change failed', true);
            }
        }

        async function openFriendsModal() {
            document.getElementById('friends-modal').style.opacity = '1';
            document.getElementById('friends-modal').style.pointerEvents = 'auto';
            const res = await fetch('/api/friends/list?username=' + sessionUser.username);
            const data = await res.json();
            const container = document.getElementById('friends-list-container');
            if(data.friends.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:10px;">No friends added yet. Search by username above!</div>';
                return;
            }
            container.innerHTML = data.friends.map(f => `
                <div style="background:var(--bg-deep); padding:8px 12px; border-radius:12px; border:1px solid var(--border-glow); display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.4rem;">${f.crew_avatar==='hostess'?'👗':'👔'}</span>
                        <div>
                            <b style="color:white; font-size:0.85rem;">${f.full_name}</b>
                            <div style="color:var(--accent); font-size:0.7rem;">${f.username} • Active: ${f.active_skin}</div>
                        </div>
                    </div>
                    <button onclick="reportFriend('${f.username}')" style="background:rgba(239,68,68,0.2); color:var(--danger); border:1px solid var(--danger); padding:4px 8px; border-radius:6px; font-size:0.7rem; cursor:pointer;">Report 🚩</button>
                </div>
            `).join('');
        }
        function closeFriendsModal() {
            document.getElementById('friends-modal').style.opacity = '0';
            document.getElementById('friends-modal').style.pointerEvents = 'none';
        }
        async function addFriendByUsername() {
            const receiver = document.getElementById('search-username-input').value.trim();
            if(!receiver) return;
            const res = await fetch('/api/friends/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sender_username: sessionUser.username, receiver_username: receiver })
            });
            if(res.ok) {
                showToast('Friend added successfully!');
                document.getElementById('search-username-input').value = '';
                openFriendsModal();
            } else {
                showToast('Username not found', true);
            }
        }
        async function reportFriend(username) {
            if(!confirm('Are you sure you want to report ' + username + '?')) return;
            const res = await fetch('/api/user/report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ reported_username: username })
            });
            const data = await res.json();
            showToast('User reported! Total community reports: ' + data.reports);
        }

        function launchLongRoadmap(yearNum) {
            const box = document.getElementById('simulation-box');
            const modules = academyData.modules.filter(m => m.year_level === yearNum);

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">Year ${yearNum} Long Roadmap</h3>
                    <span style="font-size: 0.72rem; color: var(--text-muted);">Duolingo-Style Path</span>
                </div>
                <div class="roadmap-path">
                    ${modules.map((mod, idx) => `
                        <div class="roadmap-node" onclick="playAudio('click'); launchExerciseSession(${yearNum}, ${mod.node_order})" title="${mod.title_en}">
                            <span style="font-size:1.4rem;">${mod.theme_icon}</span>
                            <span style="font-size:0.65rem; margin-top:-2px;">${idx+1}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function launchExerciseSession(yearNum, nodeOrder) {
            currentExerciseList = academyData.exercises.filter(e => e.year_level === yearNum && e.node_order === nodeOrder);
            if(currentExerciseList.length === 0) {
                currentExerciseList = [
                    { id: 999, exercise_type: 'mcq', prompt_en: 'What is the standard emergency evacuation time mandate?', options: ['90 Seconds', '5 Minutes', '10 Minutes', '30 Seconds'], correct_answer: '90 Seconds', hint_en: 'Complete evacuation using 50% exits.' }
                ];
            }
            exercisePointer = 0;
            renderCurrentExercise(yearNum);
        }

        function renderCurrentExercise(yearNum) {
            const box = document.getElementById('simulation-box');
            const ex = currentExerciseList[exercisePointer % currentExerciseList.length];

            let optionsHtml = '';
            if(ex.options && ex.options.length > 0) {
                optionsHtml = '<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin: 1rem 0;">' +
                    ex.options.map(opt => `<button class="btn-action" onclick="verifyExerciseAnswer(${yearNum}, ${ex.id}, '${opt}')" style="background:var(--bg-deep); color:white; border:1px solid var(--border-glow); padding:10px; font-size:0.85rem; position:relative; z-index:20;">${opt}</button>`).join('') +
                '</div>';
            }

            let voiceHtml = '';
            if(ex.exercise_type === 'voice') {
                voiceHtml = '<div style="text-align:center; margin:1rem 0;"><button onclick="simulateVoiceRecord(\'' + ex.correct_answer + '\', ' + yearNum + ', ' + ex.id + ')" class="btn-action" style="width:70px; height:70px; border-radius:50%; background:linear-gradient(135deg, #ef4444 0%, #991b1b 100%); font-size:1.8rem; margin:0 auto; display:flex; justify-content:center; align-items:center; position:relative; z-index:20;">🎙️</button><div style="font-size:0.75rem; color:var(--text-muted); margin-top:6px;">Tap microphone & repeat aloud</div></div>';
            }

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: var(--success);">3-MIN LESSON EXERCISE (${(exercisePointer % currentExerciseList.length) + 1}/${currentExerciseList.length})</span>
                    <span style="font-size: 0.75rem; color: var(--warning); font-weight: 800;">${ex.exercise_type.toUpperCase()}</span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 900; color: white; margin-bottom: 0.8rem; line-height: 1.4;">${ex.prompt_en}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;">Hint: ${ex.hint_en}</div>
                ${optionsHtml}
                ${voiceHtml}
                <div id="exercise-feedback" style="text-align:center; font-weight:800; font-size:0.85rem; min-height:24px; margin-top:8px;"></div>
            `;
        }

        async function verifyExerciseAnswer(yearNum, exId, chosenAnswer) {
            const res = await fetch('/api/exercise/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, exercise_id: exId, user_answer: chosenAnswer })
            });
            const data = await res.json();
            document.getElementById('dash-xp').innerText = data.xp;
            document.getElementById('dash-hearts').innerText = data.hearts;
            document.getElementById('dash-streak').innerText = data.streak;
            sessionUser.xp_points = data.xp;
            sessionUser.hearts = data.hearts;
            sessionUser.streak = data.streak;
            localStorage.setItem('aero_crew_user', JSON.stringify(sessionUser));

            const fb = document.getElementById('exercise-feedback');
            if(data.correct) {
                playAudio('success');
                fb.style.color = 'var(--success)';
                fb.innerText = data.message;
                exercisePointer++;
                setTimeout(() => renderCurrentExercise(yearNum), 1500);
            } else {
                playAudio('error');
                fb.style.color = 'var(--danger)';
                fb.innerText = data.message;
            }
        }

        function simulateVoiceRecord(correctTerm, yearNum, exId) {
            showToast('Listening to microphone audio...');
            setTimeout(() => {
                verifyExerciseAnswer(yearNum, exId, correctTerm);
            }, 1500);
        }

        function openGroupChat() {
            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900;">💬 ${sessionUser.group_code} Study Chat</h3>
                    <span style="font-size:0.72rem; color:var(--success); font-weight:800;">● Live WhatsApp Room</span>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-msg-stream">
                        ${academyData.messages.map(m => `
                            <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                                <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name} (${m.sender_username})</div>
                                <div>${m.content}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="chat-input-bar">
                        <button onclick="sendQuickAttachment('audio')" title="Voice Note" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">🎤</button>
                        <button onclick="sendQuickAttachment('image')" title="Image / Photo" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">📷</button>
                        <button onclick="sendQuickAttachment('pdf')" title="PDF File" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">📎</button>
                        <input type="text" id="chat-text-input" placeholder="Type message..." style="margin-bottom:0; flex:1; padding:7px 10px; font-size:0.82rem; position:relative; z-index:20;" />
                        <button onclick="sendChatMessage('text')" class="btn-action" style="width:50px; padding:7px; font-size:0.82rem; position:relative; z-index:20;">Send</button>
                    </div>
                </div>
            `;
            const stream = document.getElementById('chat-msg-stream');
            stream.scrollTop = stream.scrollHeight;
        }

        async function sendChatMessage(type, customContent = null) {
            const input = document.getElementById('chat-text-input');
            const content = customContent || input.value.trim();
            if(!content) return;

            const res = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_code: sessionUser.group_code, sender_username: sessionUser.username, sender_name: sessionUser.full_name, sender_avatar: sessionUser.crew_avatar, msg_type: type, content: content })
            });
            if(res.ok) {
                if(!customContent) input.value = '';
                const data = await res.json();
                academyData.messages.push(data.message);
                openGroupChat();
            }
        }
        function sendQuickAttachment(type) {
            if(type === 'audio') sendChatMessage('audio', '🎵 [Voice Note - 0:14]');
            if(type === 'image') sendChatMessage('image', '📷 [Shared Flight Deck Photo]');
            if(type === 'pdf') sendChatMessage('pdf', '📄 [EASA_Manual_Revision.pdf]');
        }

        function openShop(category = 'male') {
            const box = document.getElementById('simulation-box');
            const filteredSkins = academyData.skins.filter(s => s.category === category);

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: #a78bfa; font-weight: 900;">🎁 Tiered Uniform Boutique</h3>
                    <span style="font-size: 0.8rem; color: var(--warning); font-weight: 800;">⭐ ${sessionUser.xp_points} Stars</span>
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 0.8rem;">
                    <button onclick="playAudio('click'); openShop('male')" style="flex:1; padding:8px; border-radius:10px; border:1px solid ${category==='male'?'var(--accent)':'var(--border)'}; background:${category==='male'?'var(--accent-glow)':'var(--bg-deep)'}; color:white; font-weight:800; font-size:0.8rem; cursor:pointer; position:relative; z-index:20;">👔 Steward Collection</button>
                    <button onclick="playAudio('click'); openShop('female')" style="flex:1; padding:8px; border-radius:10px; border:1px solid ${category==='female'?'var(--accent)':'var(--border)'}; background:${category==='female'?'var(--accent-glow)':'var(--bg-deep)'}; color:white; font-weight:800; font-size:0.8rem; cursor:pointer; position:relative; z-index:20;">👗 Hostess Collection</button>
                </div>
                <div style="max-height: 190px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
                    ${filteredSkins.map(skin => `
                        <div style="background: var(--bg-deep); padding: 0.7rem 1rem; border-radius: 12px; border: 1px solid var(--border-glow); display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.6rem;">${skin.preview_svg}</span>
                                <div>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        <b style="color: white; font-size: 0.85rem;">${skin.skin_name}</b>
                                        <span style="font-size:0.62rem; padding:2px 6px; border-radius:6px; background:rgba(56,189,248,0.15); color:var(--accent); font-weight:800;">${skin.tier_level}</span>
                                    </div>
                                    <div style="color: var(--text-muted); font-size: 0.7rem;">${skin.desc_en}</div>
                                </div>
                            </div>
                            <button onclick="playAudio('click'); buySkin('${skin.skin_name}',${skin.cost}, '${category}')" style="background: #8b5cf6; color: white; border: none; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 0.75rem; cursor: pointer; position:relative; z-index:20;">${skin.cost === 0 ? 'Equipped' : skin.cost + ' ⭐'}</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function buySkin(skinName, cost, category) {
            if(cost === 0) {
                updateProfileAvatarAndSkin(sessionUser.crew_avatar, skinName);
                showToast('Equipped: ' + skinName);
                return;
            }
            const res = await fetch('/api/shop/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, skin_name: skinName, cost: cost })
            });
            const data = await res.json();
            if(res.ok) {
                playAudio('success');
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast('Successfully unlocked & equipped: ' + skinName + '!');
                openShop(category);
            } else {
                playAudio('error');
                showToast(data.detail || 'Purchase failed', true);
            }
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
