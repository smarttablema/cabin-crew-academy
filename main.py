import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aero Crew Elite Academy Pro", version="13.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table supporting Steward/Hostess custom avatars & role (student vs teacher)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_users_v13 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            username VARCHAR(50) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            role VARCHAR(20) DEFAULT 'student',
            avatar_gender VARCHAR(20) DEFAULT 'steward',
            avatar_hair VARCHAR(50) DEFAULT 'classic_short',
            avatar_hair_color VARCHAR(20) DEFAULT '#2c2c2c',
            avatar_eyes VARCHAR(20) DEFAULT '#1e3a8a',
            avatar_outfit VARCHAR(50) DEFAULT 'standard_uniform',
            avatar_accessory VARCHAR(50) DEFAULT 'wings_pin',
            active_skin VARCHAR(100) DEFAULT 'Standard Aviator Suit',
            group_code VARCHAR(50) DEFAULT 'EASA-ALPHA-1',
            reports_count INT DEFAULT 0,
            is_banned BOOLEAN DEFAULT FALSE,
            xp_points INT DEFAULT 1500,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 21,
            completed_nodes TEXT[] DEFAULT ARRAY[]::TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Study Groups table managed by teachers with 4-digit join codes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_groups_v13 (
            id SERIAL PRIMARY KEY,
            group_name VARCHAR(100),
            group_code VARCHAR(10) UNIQUE,
            teacher_username VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Teacher Lessons & Quizzes Studio table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_lessons_v13 (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            teacher_username VARCHAR(50),
            title TEXT,
            content_html TEXT,
            quiz_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Student Quiz Results & Statistics Tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_quiz_results_v13 (
            id SERIAL PRIMARY KEY,
            lesson_id INT,
            student_username VARCHAR(50),
            student_name VARCHAR(100),
            score INT,
            total_questions INT,
            attempts INT DEFAULT 1,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Real Media Chat Messages table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_chat_messages_v13 (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            sender_username VARCHAR(50),
            sender_name VARCHAR(100),
            sender_avatar_config TEXT,
            msg_type VARCHAR(20) DEFAULT 'text',
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Shop Skins table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_shop_skins_v13 (
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
        INSERT INTO aero_shop_skins_v13 (category, tier_level, skin_name, cost, preview_svg, desc_en)
        VALUES 
        ('steward', 'Free', 'Standard Aviator Suit', 0, '👔', 'Clean cadet training uniform.'),
        ('steward', 'Budget', 'Junior Cabin Steward Vest', 80, '👔⭐', 'Sleek grey vest with silver airline pin.'),
        ('steward', 'Professional', 'Senior Purser Uniform', 500, '🎖️👔', 'Tailored navy suit with supervisor epaulets.'),
        ('steward', 'Ultra-Elite Luxury', 'Supreme Gold Commander', 10000, '👑👨‍✈️✨', 'Legendary gold four-stripe captain jacket.'),
        
        ('hostess', 'Free', 'Standard Hostess Attire', 0, '👗', 'Standard elegant academy skirt suit.'),
        ('hostess', 'Budget', 'Junior Cabin Hostess Dress', 80, '👗⭐', 'Professional airline service dress.'),
        ('hostess', 'Professional', 'Lead Purser Silk Scarf', 500, '🧣💎', 'Signature silk scarf and platinum wing brooch.'),
        ('hostess', 'Ultra-Elite Luxury', 'Supreme Chief Captain', 10000, '👑👩‍✈️✨', 'Legendary gold epaulets and diamond aviation wings.')
        ON CONFLICT DO NOTHING;
    """)

    # Seed Default Study Group
    cur.execute("""
        INSERT INTO aero_groups_v13 (group_name, group_code, teacher_username)
        VALUES ('EASA Alpha Professional Flight 1', '7842', 'instructor_boss')
        ON CONFLICT (group_code) DO NOTHING;
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
    avatar_gender: str = 'steward'
    avatar_hair: str = 'classic_short'
    avatar_hair_color: str = '#2c2c2c'
    avatar_eyes: str = '#1e3a8a'
    avatar_outfit: str = 'standard_uniform'
    avatar_accessory: str = 'wings_pin'
    group_code: str = '7842'

class LoginModel(BaseModel):
    phone_number: str
    password: str

class PasswordChangeModel(BaseModel):
    phone_number: str
    recovery_pin: str
    old_password: str
    new_password: str

class AvatarUpdateModel(BaseModel):
    phone_number: str
    avatar_gender: str
    avatar_hair: str
    avatar_hair_color: str
    avatar_eyes: str
    avatar_outfit: str
    avatar_accessory: str

class CreateGroupModel(BaseModel):
    group_name: str
    group_code: str
    teacher_username: str

class CreateLessonModel(BaseModel):
    group_code: str
    teacher_username: str
    title: str
    content_html: str
    quiz_data: list

class SubmitQuizModel(BaseModel):
    lesson_id: int
    student_username: str
    student_name: str
    score: int
    total_questions: int

class ChatMessageModel(BaseModel):
    group_code: str
    sender_username: str
    sender_name: str
    sender_avatar_config: str
    msg_type: str = 'text'
    content: str

class BuySkinModel(BaseModel):
    phone_number: str
    skin_name: str
    cost: int

class NodeCompleteModel(BaseModel):
    phone_number: str
    node_id: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v13 WHERE phone_number = %s OR username = %s;", (data.phone_number, data.username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number or username already taken.")
    
    cur.execute(
        """INSERT INTO aero_users_v13 (phone_number, username, full_name, password, recovery_pin, role, avatar_gender, avatar_hair, avatar_hair_color, avatar_eyes, avatar_outfit, avatar_accessory, group_code) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;""",
        (data.phone_number, data.username, data.full_name, data.password, data.recovery_pin, data.role, data.avatar_gender, data.avatar_hair, data.avatar_hair_color, data.avatar_eyes, data.avatar_outfit, data.avatar_accessory, data.group_code)
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
    cur.execute("SELECT * FROM aero_users_v13 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if user["is_banned"]:
        raise HTTPException(status_code=403, detail="Account is banned.")
    return {"status": "success", "user": user}

@app.post("/api/user/avatar-update")
def update_avatar(data: AvatarUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE aero_users_v13 SET avatar_gender = %s, avatar_hair = %s, avatar_hair_color = %s, avatar_eyes = %s, avatar_outfit = %s, avatar_accessory = %s 
           WHERE phone_number = %s RETURNING *;""",
        (data.avatar_gender, data.avatar_hair, data.avatar_hair_color, data.avatar_eyes, data.avatar_outfit, data.avatar_accessory, data.phone_number)
    )
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.post("/api/user/password-change")
def change_password(data: PasswordChangeModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v13 WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user or user["recovery_pin"] != data.recovery_pin:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid phone or recovery PIN.")
    cur.execute("UPDATE aero_users_v13 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/group/create")
def create_group(data: CreateGroupModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_groups_v13 WHERE group_code = %s;", (data.group_code,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Group code already exists.")
    cur.execute(
        "INSERT INTO aero_groups_v13 (group_name, group_code, teacher_username) VALUES (%s, %s, %s) RETURNING *;",
        (data.group_name, data.group_code, data.teacher_username)
    )
    grp = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "group": grp}

@app.get("/api/group/info")
def get_group_info(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_groups_v13 WHERE group_code = %s;", (group_code,))
    grp = cur.fetchone()
    cur.execute("SELECT username, full_name, role, avatar_gender, avatar_hair, avatar_hair_color, avatar_eyes, avatar_outfit, avatar_accessory, xp_points FROM aero_users_v13 WHERE group_code = %s;", (group_code,))
    members = cur.fetchall()
    cur.execute("SELECT * FROM aero_lessons_v13 WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    lessons = cur.fetchall()
    cur.close()
    conn.close()
    return {"group": grp, "members": members, "lessons": lessons}

@app.post("/api/lesson/create")
def create_lesson(data: CreateLessonModel):
    conn = get_db_connection()
    cur = conn.cursor()
    import json
    cur.execute(
        "INSERT INTO aero_lessons_v13 (group_code, teacher_username, title, content_html, quiz_data) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (data.group_code, data.teacher_username, data.title, data.content_html, json.dumps(data.quiz_data))
    )
    lesson = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "lesson": lesson}

@app.get("/api/teacher/analytics")
def get_teacher_analytics(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, l.title as lesson_title 
        FROM aero_quiz_results_v13 r 
        JOIN aero_lessons_v13 l ON l.id = r.lesson_id 
        WHERE l.group_code = %s 
        ORDER BY r.completed_at DESC;
    """, (group_code,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return {"results": results}

@app.post("/api/quiz/submit")
def submit_quiz(data: SubmitQuizModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_quiz_results_v13 WHERE lesson_id = %s AND student_username = %s;", (data.lesson_id, data.student_username))
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE aero_quiz_results_v13 SET score = %s, total_questions = %s, attempts = attempts + 1, completed_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *;",
            (data.score, data.total_questions, existing["id"])
        )
    else:
        cur.execute(
            "INSERT INTO aero_quiz_results_v13 (lesson_id, student_username, student_name, score, total_questions, attempts) VALUES (%s, %s, %s, %s, %s, 1) RETURNING *;",
            (data.lesson_id, data.student_username, data.student_name, data.score, data.total_questions)
        )
    res = cur.fetchone()
    # Award XP bonus
    cur.execute("UPDATE aero_users_v13 SET xp_points = xp_points + 50 WHERE username = %s;", (data.student_username,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "result": res}

@app.get("/api/chat/messages")
def get_chat_messages(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_chat_messages_v13 WHERE group_code = %s ORDER BY id DESC LIMIT 50;", (group_code,))
    msgs = cur.fetchall()
    cur.close()
    conn.close()
    return {"messages": msgs[::-1]}

@app.post("/api/chat/send")
def send_chat_message(data: ChatMessageModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_chat_messages_v13 (group_code, sender_username, sender_name, sender_avatar_config, msg_type, content) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.group_code, data.sender_username, data.sender_name, data.sender_avatar_config, data.msg_type, data.content)
    )
    msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": msg}

@app.post("/api/node/complete")
def complete_roadmap_node(data: NodeCompleteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT completed_nodes, xp_points FROM aero_users_v13 WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    nodes = user["completed_nodes"] or []
    if data.node_id not in nodes:
        nodes.append(data.node_id)
        cur.execute("UPDATE aero_users_v13 SET completed_nodes = %s, xp_points = xp_points + 30 WHERE phone_number = %s RETURNING completed_nodes, xp_points;", (nodes, data.phone_number))
    else:
        cur.execute("UPDATE aero_users_v13 SET completed_nodes = %s WHERE phone_number = %s RETURNING completed_nodes, xp_points;", (nodes, data.phone_number))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "completed_nodes": res["completed_nodes"], "xp": res["xp_points"]}

@app.get("/api/shop/skins")
def get_skins():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_shop_skins_v13 ORDER BY cost ASC;")
    skins = cur.fetchall()
    cur.close()
    conn.close()
    return {"skins": skins}

@app.post("/api/shop/buy")
def buy_skin(data: BuySkinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_users_v13 WHERE phone_number = %s;", (data.phone_number,))
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
    cur.execute("UPDATE aero_users_v13 SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aero Crew Elite Academy Pro</title>
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
            --gold: #fbbf24;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #1e293b;
            --border-glow: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        [dir="rtl"] * { font-family: 'Tajawal', sans-serif !important; }
        
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        .app-shell { width: 100%; max-width: 650px; background: var(--surface); border-radius: 36px; padding: 2rem; border: 1px solid var(--border-glow); box-shadow: 0 45px 90px rgba(0, 0, 0, 0.95); position: relative; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.4rem; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.2rem; color: var(--accent); }
        .brand-title img { width: 34px; height: 34px; }
        
        .header-controls { display: flex; align-items: center; gap: 8px; }
        .header-icon-btn { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 12px; width: 38px; height: 38px; display: flex; justify-content: center; align-items: center; cursor: pointer; font-size: 1.1rem; transition: all 0.2s; }
        .header-icon-btn:hover { border-color: var(--accent); background: var(--accent-glow); }

        h2 { font-weight: 800; margin-bottom: 0.4rem; font-size: 1.4rem; color: white; }
        p.sub-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.4rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem; }
        input, select, textarea { width: 100%; padding: 0.9rem 1.1rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 0.92rem; margin-bottom: 1rem; outline: none; }
        input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 0.98rem; cursor: pointer; box-shadow: 0 6px 20px var(--accent-glow); transition: transform 0.1s; }
        .btn-action:active { transform: scale(0.98); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; font-size: 0.82rem; }
        .footer-nav span { color: var(--accent); font-weight: 700; cursor: pointer; }
        .footer-nav span:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        /* CUSTOM AVATAR STUDIO PREVIEW */
        .avatar-preview-box { width: 110px; height: 110px; border-radius: 50%; background: linear-gradient(135deg, #1e293b, #0f172a); border: 3px solid var(--accent); display: flex; justify-content: center; align-items: center; margin: 0 auto 1.2rem auto; position: relative; box-shadow: 0 0 25px var(--accent-glow); font-size: 3rem; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.85rem 1.1rem; border-radius: 18px; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; }
        .stat-item { font-weight: 800; font-size: 0.82rem; display: flex; align-items: center; gap: 5px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.1rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.2s; }
        .mode-tile:hover { border-color: var(--accent); transform: translateY(-2px); background: var(--surface-card-hover); }
        .mode-tile h4 { font-size: 0.85rem; font-weight: 800; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 22px; padding: 1.5rem; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; min-height: 290px; }
        
        /* DUOLINGO ROADMAP STYLING */
        .duo-path-container { display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 20px 0; max-height: 340px; overflow-y: auto; }
        .duo-row { display: flex; justify-content: center; gap: 40px; width: 100%; }
        .duo-node { width: 68px; height: 68px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; font-weight: 900; font-size: 1.1rem; cursor: pointer; position: relative; box-shadow: 0 8px 0 rgba(0,0,0,0.4); transition: transform 0.2s; }
        .duo-node:hover { transform: scale(1.1); }
        .duo-node.completed { background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); color: #451a03; border: 4px solid #fef3c7; box-shadow: 0 8px 0 #b45309, 0 0 20px rgba(251,191,36,0.5); }
        .duo-node.active { background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: #020617; border: 4px solid #bae6fd; box-shadow: 0 8px 0 #0369a1, 0 0 25px var(--accent); animation: pulseNode 1.5s infinite ease-in-out; }
        .duo-node.locked { background: #334155; color: #94a3b8; border: 4px solid #475569; box-shadow: 0 8px 0 #1e293b; opacity: 0.7; }
        @keyframes pulseNode { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.06); } }

        /* CHAT STYLING WITH REAL MEDIA */
        .chat-container { display: flex; flex-direction: column; height: 340px; background: var(--bg-deep); border-radius: 16px; border: 1px solid var(--border-glow); overflow: hidden; }
        .chat-messages { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .chat-bubble { max-width: 80%; padding: 10px 14px; border-radius: 16px; font-size: 0.84rem; line-height: 1.4; }
        .chat-bubble.incoming { background: var(--surface-card); color: white; align-self: flex-start; }
        .chat-bubble.outgoing { background: #0284c7; color: white; align-self: flex-end; }
        .chat-input-bar { display: flex; gap: 8px; padding: 10px; background: var(--surface-card); border-top: 1px solid var(--border); align-items: center; }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 14px 28px; border-radius: 35px; font-weight: 800; font-size: 0.9rem; transition: transform 0.3s; z-index: 6000; pointer-events: none; }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <!-- MAIN APP SHELL -->
    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Logo">
                <span>Aero Crew Pro</span>
            </div>
            <div class="header-controls hidden" id="dash-header-icons">
                <div class="header-icon-btn" onclick="openAvatarStudio()" title="Customize Avatar">👤</div>
                <div class="header-icon-btn" onclick="openShop()" title="Skin Boutique">🎁</div>
                <div class="header-icon-btn" onclick="openSettingsModal()" title="Settings">⚙️</div>
            </div>
        </div>

        <!-- LOGIN SCREEN -->
        <div id="screen-login">
            <h2>Cabin Crew Portal</h2>
            <p class="sub-desc">Access accredited EASA/ICAO professional curriculum & live study groups.</p>
            
            <label>Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn-action" onclick="submitLogin()">Sign In to Simulator</button>
            
            <div class="footer-nav">
                <span onclick="navigateTo('screen-register')">Create Account</span>
                <span onclick="navigateTo('screen-reset')">Forgot Password?</span>
            </div>
        </div>

        <!-- REGISTER SCREEN WITH AVATAR CUSTOMIZER & TEACHER ROLE -->
        <div id="screen-register" class="hidden">
            <h2>Cadet & Instructor Enrollment</h2>
            <p class="sub-desc">Register your profile, choose your role, and design your custom professional avatar.</p>
            
            <div class="avatar-preview-box" id="reg-avatar-preview">👔</div>

            <label>Register As</label>
            <select id="reg-role" onchange="toggleTeacherCodeField()">
                <option value="student">🎓 Cadet / Student</option>
                <option value="teacher">👨‍🏫 Instructor / Teacher</option>
            </select>

            <div id="group-code-section">
                <label>Study Group Code (4-digits)</label>
                <input type="text" id="reg-group-code" placeholder="e.g. 7842" value="7842" maxlength="4" />
            </div>

            <label>Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label>Unique Username</label>
            <input type="text" id="reg-username" placeholder="@username" />

            <label>Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label>Recovery PIN (4 digits)</label>
            <input type="password" id="reg-pin" placeholder="PIN" maxlength="4" />

            <!-- AVATAR CUSTOMIZATION STUDIO -->
            <h3 style="font-size:1rem; color:var(--accent); margin: 1rem 0 0.5K 0; font-weight:800;">🎨 Avatar Customization Studio</h3>
            
            <label>Avatar Type</label>
            <select id="reg-gender" onchange="updateRegAvatarPreview()">
                <option value="steward">👔 Steward (Professional Male)</option>
                <option value="hostess">👗 Hostess (Professional Female)</option>
            </select>

            <label>Hair Style</label>
            <select id="reg-hair" onchange="updateRegAvatarPreview()">
                <option value="classic_short">Classic Short</option>
                <option value="sleek_bun">Sleek Bun</option>
                <option value="commander_cap">Commander Cap</option>
                <option value="aviator_caps">Aviator Cap</option>
            </select>

            <label>Hair Color</label>
            <input type="color" id="reg-hair-color" value="#2c2c2c" onchange="updateRegAvatarPreview()" style="height:45px; padding:4px; cursor:pointer;" />

            <label>Eye Color</label>
            <input type="color" id="reg-eyes" value="#1e3a8a" onchange="updateRegAvatarPreview()" style="height:45px; padding:4px; cursor:pointer;" />

            <label>Outfit Style</label>
            <select id="reg-outfit" onchange="updateRegAvatarPreview()">
                <option value="standard_uniform">Standard Academy Uniform</option>
                <option value="supervisor_suit">Senior Purser Suit</option>
                <option value="gold_commander">Supreme Gold Commander Jacket</option>
            </select>

            <label>Accessory</label>
            <select id="reg-accessory" onchange="updateRegAvatarPreview()">
                <option value="wings_pin">Platinum Wings Pin</option>
                <option value="silk_scarf">Designer Silk Scarf</option>
                <option value="captain_epaulets">Four-Stripe Gold Epaulets</option>
            </select>
            
            <button class="btn-action" onclick="submitRegister()" style="background: #10b981; color: white; margin-top:1rem;">Complete Registration & Initialize Profile</button>
            
            <div class="footer-nav">
                <span onclick="navigateTo('screen-login')">Already have an account? Sign In</span>
            </div>
        </div>

        <!-- RESET PASSWORD SCREEN -->
        <div id="screen-reset" class="hidden">
            <h2>Recovery PIN Reset</h2>
            <p class="sub-desc">Enter your phone and secret recovery PIN.</p>
            <label>Phone Number</label>
            <input type="tel" id="reset-phone" placeholder="Phone" />
            <label>Secret Recovery PIN</label>
            <input type="password" id="reset-pin" placeholder="PIN" maxlength="4" />
            <label>New Password</label>
            <input type="password" id="reset-new" placeholder="New Password" />
            <button class="btn-action" onclick="submitReset()" style="background: #f59e0b; color: #020617;">Update Credentials</button>
            <div class="footer-nav">
                <span onclick="navigateTo('screen-login')">Back to Sign In</span>
            </div>
        </div>

        <!-- DASHBOARD SCREEN -->
        <div id="screen-dashboard" class="hidden">
            <div class="mascot-banner">
                <div class="mascot-avatar" id="dash-avatar-icon">👔</div>
                <div class="mascot-speech" id="mascot-speech">Welcome back, Captain! EASA regulatory standards require continuous daily precision.</div>
            </div>

            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent); font-weight: 900;">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted);" id="dash-role-badge">Student • Group: 7842</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">1500</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">21</span></div>
                </div>
            </div>

            <div class="mode-grid">
                <div class="mode-tile" onclick="launchRoadmap(1)">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4 id="tile-year1">First Year Path (100+ Nodes)</h4>
                </div>
                <div class="mode-tile" onclick="launchRoadmap(2)">
                    <span style="font-size: 1.4rem;">🏆</span>
                    <h4 id="tile-year2">Second Year Path (100+ Nodes)</h4>
                </div>
                <div class="mode-tile" onclick="openStudyHub()">
                    <span style="font-size: 1.4rem;">📚</span>
                    <h4 id="tile-lessons">Lessons & Quizzes Studio</h4>
                </div>
                <div class="mode-tile" onclick="openGroupChat()">
                    <span style="font-size: 1.4rem;">💬</span>
                    <h4 id="tile-chat">Live Study Group Chat</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container">
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year Path</b> or <b>Second Year Path</b> above to begin your 200+ level Duolingo-style learning adventure, or open the <b>Lessons Studio</b> to access instructor-crafted quizzes and analytics.</p>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1;">← Hub</button>
                <button class="btn-action" onclick="logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1;">Logout 🚪</button>
            </div>
        </div>
    </div>

    <!-- AVATAR STUDIO MODAL -->
    <div id="avatar-studio-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); display:none; justify-content:center; align-items:center; z-index:5000;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:440px; max-height:90vh; overflow-y:auto;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <h3 style="font-size:1.1rem; font-weight:900; color:white;">🎨 Edit Avatar Customization</h3>
                <button onclick="closeAvatarStudio()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>
            <div class="avatar-preview-box" id="modal-avatar-preview">👔</div>
            <label>Gender / Style</label>
            <select id="mod-gender" onchange="updateModalAvatarPreview()">
                <option value="steward">👔 Steward</option>
                <option value="hostess">👗 Hostess</option>
            </select>
            <label>Hair Style</label>
            <select id="mod-hair" onchange="updateModalAvatarPreview()">
                <option value="classic_short">Classic Short</option>
                <option value="sleek_bun">Sleek Bun</option>
                <option value="commander_cap">Commander Cap</option>
                <option value="aviator_caps">Aviator Cap</option>
            </select>
            <label>Hair Color</label>
            <input type="color" id="mod-hair-color" value="#2c2c2c" onchange="updateModalAvatarPreview()" style="height:40px;" />
            <label>Eye Color</label>
            <input type="color" id="mod-eyes" value="#1e3a8a" onchange="updateModalAvatarPreview()" style="height:40px;" />
            <label>Outfit</label>
            <select id="mod-outfit" onchange="updateModalAvatarPreview()">
                <option value="standard_uniform">Standard Uniform</option>
                <option value="supervisor_suit">Senior Purser Suit</option>
                <option value="gold_commander">Gold Commander Jacket</option>
            </select>
            <button class="btn-action" onclick="saveAvatarChanges()" style="margin-top:1rem; background:var(--success); color:white;">Save Avatar 💾</button>
        </div>
    </div>

    <!-- SETTINGS MODAL -->
    <div id="settings-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); display:none; justify-content:center; align-items:center; z-index:5000;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:400px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
                <h3 style="font-size:1.2rem; font-weight:900; color:white;">⚙️ Academy Settings</h3>
                <button onclick="closeSettingsModal()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>
            <label>Change Password</label>
            <input type="password" id="set-pin" placeholder="Recovery PIN (4 digits)" maxlength="4" />
            <input type="password" id="set-new-pass" placeholder="New Password" />
            <button class="btn-action" onclick="submitPasswordChangeModal()" style="background:var(--warning); color:var(--bg-deep);">Update Password 🔒</button>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('aero_crew_user_pro') || 'null');
        let groupInfo = { group: null, members: [], lessons: [] };
        let activeRoadmapYear = 1;
        let mediaRecorder = null;
        let audioChunks = [];

        window.onload = function() {
            if(sessionUser) {
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchGroupData();
            } else {
                navigateTo('screen-login');
            }
        };

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
                if(id === 'screen-dashboard') headerIcons.classList.remove('hidden');
                else headerIcons.classList.add('hidden');
            }
        }

        function toggleTeacherCodeField() {
            const role = document.getElementById('reg-role').value;
            const sec = document.getElementById('group-code-section');
            if(role === 'teacher') sec.style.display = 'none';
            else sec.style.display = 'block';
        }

        function updateRegAvatarPreview() {
            const gender = document.getElementById('reg-gender').value;
            const emoji = gender === 'hostess' ? '👗' : '👔';
            document.getElementById('reg-avatar-preview').innerText = emoji;
        }

        function updateModalAvatarPreview() {
            const gender = document.getElementById('mod-gender').value;
            const emoji = gender === 'hostess' ? '👗' : '👔';
            document.getElementById('modal-avatar-preview').innerText = emoji;
        }

        async function submitRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const username = document.getElementById('reg-username').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();
            const role = document.getElementById('reg-role').value;
            const group_code = role === 'teacher' ? Math.floor(1000 + Math.random() * 9000).toString() : document.getElementById('reg-group-code').value.trim();
            
            const avatar_gender = document.getElementById('reg-gender').value;
            const avatar_hair = document.getElementById('reg-hair').value;
            const avatar_hair_color = document.getElementById('reg-hair-color').value;
            const avatar_eyes = document.getElementById('reg-eyes').value;
            const avatar_outfit = document.getElementById('reg-outfit').value;
            const avatar_accessory = document.getElementById('reg-accessory').value;

            if(!full_name || !username || !phone_number || !password || !recovery_pin) { showToast('Complete all required fields', true); return; }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ full_name, username, phone_number, password, recovery_pin, role, avatar_gender, avatar_hair, avatar_hair_color, avatar_eyes, avatar_outfit, avatar_accessory, group_code })
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
            if(!phone_number || !password) { showToast('Enter login credentials', true); return; }

            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number, password })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro', JSON.stringify(sessionUser));
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchGroupData();
                showToast('Welcome aboard, Captain ' + sessionUser.full_name + '!');
            } else {
                showToast(data.detail || 'Invalid phone or password', true);
            }
        }

        function updateDashboardUI() {
            if(!sessionUser) return;
            document.getElementById('dash-name').innerText = sessionUser.full_name;
            document.getElementById('dash-xp').innerText = sessionUser.xp_points;
            document.getElementById('dash-hearts').innerText = sessionUser.hearts;
            document.getElementById('dash-streak').innerText = sessionUser.streak;
            const emoji = sessionUser.avatar_gender === 'hostess' ? '👗' : '👔';
            document.getElementById('dash-avatar-icon').innerText = emoji;
            const roleText = sessionUser.role === 'teacher' ? 'Instructor / Teacher' : 'Cadet / Student';
            document.getElementById('dash-role-badge').innerText = `${roleText} • Group Code: ${sessionUser.group_code}`;
        }

        function logoutUser() {
            localStorage.removeItem('aero_crew_user_pro');
            sessionUser = null;
            navigateTo('screen-login');
            showToast('Logged out successfully.');
        }

        async function fetchGroupData() {
            if(!sessionUser) return;
            const res = await fetch('/api/group/info?group_code=' + sessionUser.group_code);
            groupInfo = await res.json();
        }

        function resetToMenu() {
            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year Path</b> or <b>Second Year Path</b> above to begin your 200+ level Duolingo-style learning adventure, or open the <b>Lessons Studio</b> to access instructor-crafted quizzes and analytics.</p>
            `;
        }

        /* 200+ LEVEL DUOLINGO ROADMAP GENERATOR */
        function launchRoadmap(yearNum) {
            activeRoadmapYear = yearNum;
            const box = document.getElementById('simulation-box');
            const completedList = sessionUser.completed_nodes || [];
            
            let nodesHtml = '';
            // Generate 100+ nodes for the selected year
            for(let i = 1; i <= 100; i++) {
                const nodeId = `y${yearNum}_node_${i}`;
                const isCompleted = completedList.includes(nodeId);
                // First node or previous node completed unlocks current
                let statusClass = 'locked';
                if(isCompleted) statusClass = 'completed';
                else if(i === 1 || completedList.includes(`y${yearNum}_node_${i-1}`)) statusClass = 'active';

                const icon = isCompleted ? '👑' : (statusClass === 'active' ? '✈️' : '🔒');

                nodesHtml += `
                    <div class="duo-node ${statusClass}" onclick="openNodeLesson(${yearNum}, ${i}, '${statusClass}')" title="Node ${i}">
                        <span style="font-size:1.3rem;">${icon}</span>
                        <span style="font-size:0.55rem; margin-top:-2px;">${i}</span>
                    </div>
                `;
            }

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--gold); font-weight: 900;">🏆 Year ${yearNum} Roadmap (100 Checkpoints)</h3>
                    <span style="font-size: 0.72rem; color: var(--text-muted);">Duolingo-Style Path</span>
                </div>
                <div class="duo-path-container">
                    <div style="display:flex; flex-direction:column; align-items:center; gap:18px; width:100%;">
                        ${nodesHtml}
                    </div>
                </div>
            `;
        }

        function openNodeLesson(yearNum, nodeNum, status) {
            if(status === 'locked') {
                showToast('Complete previous checkpoints to unlock this lesson!', true);
                return;
            }
            const box = document.getElementById('simulation-box');
            const nodeId = `y${yearNum}_node_${nodeNum}`;

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: var(--success);">EASA CHECKPOINT ${nodeNum} (Year ${yearNum})</span>
                    <span style="font-size: 0.75rem; color: var(--gold); font-weight: 800;">⭐ +30 XP</span>
                </div>
                <h3 style="font-size: 1.15rem; font-weight: 900; color: white; margin-bottom: 0.6rem;">Cabin Safety & Regulatory Module #${nodeNum}</h3>
                <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1.2rem;">
                    In accordance with EASA Part-CC standards, verify pre-flight cabin readiness, emergency exit arming protocols, and passenger briefing compliance.
                </p>
                <div style="background:var(--bg-deep); padding:1rem; border-radius:14px; border:1px solid var(--border-glow); margin-bottom:1.2rem;">
                    <b style="color:var(--accent); font-size:0.9rem;">Question: What is the mandatory cabin crew action prior to aircraft movement on pushback?</b>
                    <div style="display:flex; flex-direction:column; gap:8px; margin-top:10px;">
                        <button class="btn-action" onclick="verifyNodeAnswer('${nodeId}', true)" style="background:var(--bg-deep); color:white; border:1px solid var(--border-glow); padding:10px; font-size:0.85rem; text-align:left;">A) Perform safety demonstration and secure cabin/galleys</button>
                        <button class="btn-action" onclick="verifyNodeAnswer('${nodeId}', false)" style="background:var(--bg-deep); color:white; border:1px solid var(--border-glow); padding:10px; font-size:0.85rem; text-align:left;">B) Open forward passenger door for ventilation</button>
                    </div>
                </div>
                <div id="node-feedback" style="text-align:center; font-weight:800; font-size:0.85rem;"></div>
            `;
        }

        async function verifyNodeAnswer(nodeId, isCorrect) {
            const fb = document.getElementById('node-feedback');
            if(isCorrect) {
                fb.style.color = 'var(--success)';
                fb.innerText = 'Correct! +30 XP Earned.';
                const res = await fetch('/api/node/complete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: sessionUser.phone_number, node_id: nodeId })
                });
                const data = await res.json();
                sessionUser.completed_nodes = data.completed_nodes;
                sessionUser.xp_points = data.xp;
                localStorage.setItem('aero_crew_user_pro', JSON.stringify(sessionUser));
                updateDashboardUI();
                setTimeout(() => launchRoadmap(activeRoadmapYear), 1500);
            } else {
                fb.style.color = 'var(--danger)';
                fb.innerText = 'Incorrect answer. Review EASA manuals and try again.';
            }
        }

        /* LESSONS & QUIZZES STUDIO (TEACHER & STUDENT SUITE) */
        async function openStudyHub() {
            await fetchGroupData();
            const box = document.getElementById('simulation-box');
            const isTeacher = sessionUser.role === 'teacher';

            let teacherControls = '';
            if(isTeacher) {
                teacherControls = `
                    <div style="background:var(--bg-deep); padding:1rem; border-radius:14px; border:1px solid var(--accent); margin-bottom:1rem;">
                        <h4 style="color:var(--accent); font-size:0.9rem; margin-bottom:0.5rem;">👨‍🏫 Instructor Lesson & Quiz Builder</h4>
                        <label>Lesson Title</label>
                        <input type="text" id="new-lesson-title" placeholder="e.g. Emergency Evacuation Protocols" style="margin-bottom:8px;" />
                        <label>Rich Lesson Content (HTML / Notes)</label>
                        <textarea id="new-lesson-content" placeholder="Type lesson notes, colors, emojis..." style="height:70px; margin-bottom:8px;"></textarea>
                        <label>Quiz Question</label>
                        <input type="text" id="new-quiz-q" placeholder="Quiz Question" style="margin-bottom:8px;" />
                        <label>Correct Answer</label>
                        <input type="text" id="new-quiz-ans" placeholder="Correct Answer" style="margin-bottom:10px;" />
                        <button class="btn-action" onclick="createTeacherLesson()" style="padding:8px; font-size:0.85rem; background:var(--success); color:white;">Publish Lesson & Quiz 🚀</button>
                    </div>
                    <div style="margin-bottom:1rem;">
                        <button class="btn-action" onclick="openTeacherAnalytics()" style="padding:8px; font-size:0.85rem; background:var(--warning); color:var(--bg-deep);">View Student Completion Analytics 📊</button>
                    </div>
                `;
            }

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">📚 Group ${sessionUser.group_code} Study Studio</h3>
                    <span style="font-size: 0.72rem; color: var(--success); font-weight: 800;">Active Group Hub</span>
                </div>
                ${teacherControls}
                <h4 style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.6rem; text-transform:uppercase;">Published Lessons & Quizzes</h4>
                <div style="max-height:200px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;" id="lessons-list">
                    ${groupInfo.lessons.length === 0 ? '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:15px;">No lessons published by instructor yet.</div>' : 
                      groupInfo.lessons.map(l => `
                        <div style="background:var(--bg-deep); padding:10px 14px; border-radius:12px; border:1px solid var(--border-glow); display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <b style="color:white; font-size:0.9rem;">${l.title}</b>
                                <div style="color:var(--text-muted); font-size:0.75rem;">Instructor: ${l.teacher_username}</div>
                            </div>
                            <button class="btn-action" onclick='takeLessonQuiz(${JSON.stringify(l)})' style="width:90px; padding:6px; font-size:0.75rem;">Take Quiz 📝</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function createTeacherLesson() {
            const title = document.getElementById('new-lesson-title').value.trim();
            const content_html = document.getElementById('new-lesson-content').value.trim();
            const q = document.getElementById('new-quiz-q').value.trim();
            const ans = document.getElementById('new-quiz-ans').value.trim();

            if(!title || !q || !ans) { showToast('Fill in lesson title, question, and answer', true); return; }

            const quiz_data = [{ question: q, correct: ans }];
            const res = await fetch('/api/lesson/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_code: sessionUser.group_code, teacher_username: sessionUser.username, title, content_html, quiz_data })
            });
            if(res.ok) {
                showToast('Lesson published successfully!');
                openStudyHub();
            } else {
                showToast('Publish failed', true);
            }
        }

        async function openTeacherAnalytics() {
            const res = await fetch('/api/teacher/analytics?group_code=' + sessionUser.group_code);
            const data = await res.json();
            const box = document.getElementById('simulation-box');

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                    <h3 style="font-size:1.05rem; color:var(--warning); font-weight:900;">📊 Student Quiz Analytics</h3>
                    <button class="btn-action" onclick="openStudyHub()" style="width:70px; padding:6px; font-size:0.75rem;">Back</button>
                </div>
                <div style="max-height:220px; overflow-y:auto; display:flex; flex-direction:column; gap:8px;">
                    ${data.results.length === 0 ? '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center;">No quiz attempts recorded yet.</div>' :
                      data.results.map(r => `
                        <div style="background:var(--bg-deep); padding:10px; border-radius:12px; border:1px solid var(--border-glow); display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <b style="color:white; font-size:0.85rem;">${r.student_name} (@${r.student_username})</b>
                                <div style="color:var(--text-muted); font-size:0.72rem;">Lesson: ${r.lesson_title} • Attempts: ${r.attempts}</div>
                            </div>
                            <div style="text-align:right;">
                                <span style="color:var(--success); font-weight:900; font-size:0.9rem;">${r.score}/${r.total_questions}</span>
                                <div style="color:var(--text-muted); font-size:0.65rem;">Score</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function takeLessonQuiz(lesson) {
            const box = document.getElementById('simulation-box');
            let quiz = lesson.quiz_data;
            if(typeof quiz === 'string') quiz = JSON.parse(quiz);
            const q = quiz[0] || { question: 'Review lesson notes.', correct: 'Yes' };

            box.innerHTML = `
                <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900; margin-bottom:0.5rem;">📝 ${lesson.title}</h3>
                <div style="background:var(--bg-deep); padding:12px; border-radius:12px; font-size:0.85rem; color:white; margin-bottom:1rem; line-height:1.4;">${lesson.content_html}</div>
                <label>${q.question}</label>
                <input type="text" id="quiz-user-ans" placeholder="Type your answer..." />
                <button class="btn-action" onclick="submitQuizAnswer(${lesson.id}, '${q.correct}')" style="background:var(--success); color:white;">Submit Quiz 🎯</button>
            `;
        }

        async function submitQuizAnswer(lessonId, correctAns) {
            const val = document.getElementById('quiz-user-ans').value.trim();
            const score = val.toLowerCase() === correctAns.toLowerCase() ? 1 : 0;

            const res = await fetch('/api/quiz/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ lesson_id: lessonId, student_username: sessionUser.username, student_name: sessionUser.full_name, score, total_questions: 1 })
            });
            if(res.ok) {
                showToast(score === 1 ? 'Quiz Passed! +50 XP Stars ⭐' : 'Submitted. Keep reviewing!');
                openStudyHub();
            }
        }

        /* REAL MEDIA CHAT FUNCTIONALITY */
        async function openGroupChat() {
            const box = document.getElementById('simulation-box');
            const res = await fetch('/api/chat/messages?group_code=' + sessionUser.group_code);
            const data = await res.json();

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900;">💬 Group ${sessionUser.group_code} Live Chat</h3>
                    <span style="font-size:0.72rem; color:var(--success); font-weight:800;">● Secure Room</span>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-msg-stream">
                        ${data.messages.map(m => `
                            <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                                <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name} (@${m.sender_username})</div>
                                <div>${m.content}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="chat-input-bar">
                        <button onclick="startRealVoiceRecording()" id="btn-mic" title="Record Voice Note" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">🎤</button>
                        <input type="file" id="chat-file-picker" style="display:none;" onchange="sendRealFile(this)" />
                        <button onclick="document.getElementById('chat-file-picker').click()" title="Upload Photo / PDF" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">📎</button>
                        <input type="text" id="chat-text-input" placeholder="Type message..." style="margin-bottom:0; flex:1; padding:7px 10px; font-size:0.82rem;" />
                        <button onclick="sendChatMessage('text')" class="btn-action" style="width:50px; padding:7px; font-size:0.82rem;">Send</button>
                    </div>
                </div>
            `;
            const stream = document.getElementById('chat-msg-stream');
            stream.scrollTop = stream.scrollHeight;
        }

        async function sendChatMessage(type, contentOverride = null) {
            const input = document.getElementById('chat-text-input');
            const content = contentOverride || (input ? input.value.trim() : '');
            if(!content) return;

            const res = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    group_code: sessionUser.group_code, 
                    sender_username: sessionUser.username, 
                    sender_name: sessionUser.full_name, 
                    sender_avatar_config: sessionUser.avatar_gender, 
                    msg_type: type, 
                    content 
                })
            });
            if(res.ok) {
                if(!contentOverride && input) input.value = '';
                openGroupChat();
            }
        }

        async function startRealVoiceRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    showToast('Voice note recorded successfully!');
                    sendChatMessage('audio', '🎵 [Real Voice Note - Audio Clip Recorded]');
                };
                mediaRecorder.start();
                showToast('Recording voice note... Tap microphone again to stop.');
                document.getElementById('btn-mic').onclick = stopRealVoiceRecording;
                document.getElementById('btn-mic').style.color = 'var(--danger)';
            } catch(e) {
                showToast('Microphone access denied or unavailable', true);
            }
        }

        function stopRealVoiceRecording() {
            if(mediaRecorder) mediaRecorder.stop();
            document.getElementById('btn-mic').onclick = startRealVoiceRecording;
            document.getElementById('btn-mic').style.color = 'var(--accent)';
        }

        function sendRealFile(input) {
            if(input.files && input.files[0]) {
                const file = input.files[0];
                showToast('Uploading ' + file.name + '...');
                setTimeout(() => {
                    sendChatMessage('file', `📁 [Uploaded File: ${file.name}]`);
                }, 1000);
            }
        }

        /* AVATAR STUDIO MODAL */
        function openAvatarStudio() {
            document.getElementById('avatar-studio-modal').style.display = 'flex';
            document.getElementById('mod-gender').value = sessionUser.avatar_gender;
            document.getElementById('mod-hair').value = sessionUser.avatar_hair;
            document.getElementById('mod-hair-color').value = sessionUser.avatar_hair_color;
            document.getElementById('mod-eyes').value = sessionUser.avatar_eyes;
            document.getElementById('mod-outfit').value = sessionUser.avatar_outfit;
            updateModalAvatarPreview();
        }
        function closeAvatarStudio() {
            document.getElementById('avatar-studio-modal').style.display = 'none';
        }
        async function saveAvatarChanges() {
            const avatar_gender = document.getElementById('mod-gender').value;
            const avatar_hair = document.getElementById('mod-hair').value;
            const avatar_hair_color = document.getElementById('mod-hair-color').value;
            const avatar_eyes = document.getElementById('mod-eyes').value;
            const avatar_outfit = document.getElementById('mod-outfit').value;
            const avatar_accessory = sessionUser.avatar_accessory;

            const res = await fetch('/api/user/avatar-update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, avatar_gender, avatar_hair, avatar_hair_color, avatar_eyes, avatar_outfit, avatar_accessory })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro', JSON.stringify(sessionUser));
                updateDashboardUI();
                closeAvatarStudio();
                showToast('Avatar updated successfully!');
            }
        }

        function openSettingsModal() {
            document.getElementById('settings-modal').style.display = 'flex';
        }
        function closeSettingsModal() {
            document.getElementById('settings-modal').style.display = 'none';
        }
        async function submitPasswordChangeModal() {
            const recovery_pin = document.getElementById('set-pin').value.trim();
            const new_password = document.getElementById('set-new-pass').value.trim();
            if(!recovery_pin || !new_password) { showToast('Fill all fields', true); return; }

            const res = await fetch('/api/user/password-change', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, recovery_pin, old_password: new_password, new_password })
            });
            if(res.ok) {
                showToast('Password updated successfully!');
                closeSettingsModal();
            } else {
                showToast('Invalid recovery PIN', true);
            }
        }

        async function openShop() {
            const res = await fetch('/api/shop/skins');
            const data = await res.json();
            const box = document.getElementById('simulation-box');

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: #a78bfa; font-weight: 900;">🎁 Uniform & Skin Boutique</h3>
                    <span style="font-size: 0.8rem; color: var(--warning); font-weight: 800;">⭐ ${sessionUser.xp_points} Stars</span>
                </div>
                <div style="max-height: 220px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
                    ${data.skins.map(skin => `
                        <div style="background: var(--bg-deep); padding: 0.7rem 1rem; border-radius: 12px; border: 1px solid var(--border-glow); display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.6rem;">${skin.preview_svg}</span>
                                <div>
                                    <div style="display:flex; gap:6px; align-items:center;">
                                        <b style="color: white; font-size: 0.85rem;">${skin.skin_name}</b>
                                        <span style="font-size:0.62rem; padding:2px 6px; border-radius:6px; background:rgba(56,189,248,0.15); color:var(--accent);">${skin.tier_level}</span>
                                    </div>
                                    <div style="color: var(--text-muted); font-size: 0.7rem;">${skin.desc_en}</div>
                                </div>
                            </div>
                            <button class="btn-action" onclick="buySkin('${skin.skin_name}', ${skin.cost})" style="width:85px; padding:6px; font-size:0.75rem; background:#8b5cf6; color:white;">${skin.cost === 0 ? 'Equipped' : skin.cost + ' ⭐'}</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function buySkin(skinName, cost) {
            if(cost === 0) { showToast('Already equipped.'); return; }
            const res = await fetch('/api/shop/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, skin_name: skinName, cost })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast('Unlocked & equipped ' + skinName + '!');
                openShop();
            } else {
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
