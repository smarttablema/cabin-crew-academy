import os
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import date, timedelta

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aero Crew Academy - Millennium Edition", version="31.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_users (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            username VARCHAR(50) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            role VARCHAR(20) DEFAULT 'student',
            avatar_gender VARCHAR(20) DEFAULT 'steward',
            active_skin VARCHAR(100) DEFAULT 'Cabin Fire Extinguisher',
            group_code VARCHAR(50) DEFAULT '7842',
            friends TEXT[] DEFAULT ARRAY[]::TEXT[],
            xp_points INT DEFAULT 1500,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 21,
            last_practice_date DATE,
            last_heart_loss_date DATE,
            last_heart_refill_timestamp BIGINT DEFAULT 0,
            last_spin_timestamp BIGINT DEFAULT 0,
            completed_nodes TEXT[] DEFAULT ARRAY[]::TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    try:
        cur.execute("ALTER TABLE aero_v22_users ADD COLUMN IF NOT EXISTS last_heart_refill_timestamp BIGINT DEFAULT 0;")
        cur.execute("ALTER TABLE aero_v22_users ADD COLUMN IF NOT EXISTS last_spin_timestamp BIGINT DEFAULT 0;")
    except Exception:
        conn.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_friend_requests (
            id SERIAL PRIMARY KEY,
            sender_username VARCHAR(50),
            receiver_username VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_direct_messages (
            id SERIAL PRIMARY KEY,
            sender_username VARCHAR(50),
            receiver_username VARCHAR(50),
            sender_name VARCHAR(100),
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_groups (
            id SERIAL PRIMARY KEY,
            group_name VARCHAR(100),
            group_code VARCHAR(10) UNIQUE,
            teacher_username VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_lessons (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            teacher_username VARCHAR(50),
            title TEXT,
            content_html TEXT,
            quiz_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_exams (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            teacher_username VARCHAR(50),
            title TEXT,
            exam_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_exam_submissions (
            id SERIAL PRIMARY KEY,
            exam_id INT,
            student_username VARCHAR(50),
            student_name VARCHAR(100),
            score INT,
            total_questions INT,
            time_spent_seconds INT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_battles (
            match_id VARCHAR(50) PRIMARY KEY,
            sender_username VARCHAR(50),
            sender_name VARCHAR(100),
            receiver_username VARCHAR(50),
            status VARCHAR(20) DEFAULT 'pending',
            questions JSONB,
            scores JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aero_v22_shop_skins (
            id SERIAL PRIMARY KEY,
            category VARCHAR(20),
            tier_level VARCHAR(30),
            skin_name_en VARCHAR(50),
            skin_name_fr VARCHAR(50),
            skin_name_ar VARCHAR(50),
            cost INT,
            preview_svg TEXT,
            desc_en TEXT,
            desc_fr TEXT,
            desc_ar TEXT
        );
    """)

    cur.execute("DELETE FROM aero_v22_shop_skins;")
    cur.execute("""
        INSERT INTO aero_v22_shop_skins (category, tier_level, skin_name_en, skin_name_fr, skin_name_ar, cost, preview_svg, desc_en, desc_fr, desc_ar)
        VALUES 
        ('safety', 'Essential', 'Cabin Fire Extinguisher', 'Extincteur de Cabine', 'طفاية حريق المقصورة', 0, '🧯', 'Halon/Dry powder extinguisher for onboard electrical and galley fires.', 'Extincteur pour feux de cabine.', 'طفاية حريق مخصصة لحرائق المقصورة والمطبخ.'),
        ('safety', 'Medical', 'Portable Oxygen Bottle', 'Bouteille d’Oxygène Portable', 'أسطوانة أكسجين محمولة', 150, '💨', 'First-aid medical oxygen supply unit with high-flow mask.', 'Unité d’oxygène médicale portable.', 'وحدة إمداد طبي بالأكسجين للحالات الطارئة.'),
        ('emergency', 'Evacuation', 'Emergency Megaphone', 'Mégaphone d’Urgence', 'مكبر صوت الطوارئ', 300, '📢', 'Battery-powered acoustic amplifier for crowd control and evacuation.', 'Amplificateur acoustique d’urgence.', 'مكبر صوت يعمل بالبطارية للتحكم في الحشود أثناء الإخلاء.'),
        ('safety', 'Equipment', 'Cabin Flashlight', 'Lampe de Poche de Sécurité', 'مصباح طوارئ الكابينة', 200, '🔦', 'Heavy-duty rechargeable emergency LED flashlight.', 'Lampe de poche de secours.', 'مصباح يدوي قوي قابل لإعادة الشحن للطوارئ.'),
        ('survival', 'Flotation', 'Inflatable Life Vest', 'Gilet de Sauvetage Gonflable', 'سترة نجاة قابلة للنفخ', 400, '🦺', 'Dual-chamber passenger and crew flotation vest with whistle and light.', 'Gilet de sauvetage double chambre.', 'سترة نجاة مزدوجة الغرفة مع صفارة ومصباح.'),
        ('emergency', 'Marine', 'Slide-Raft Unit', 'Toboggan-Radeau d’Évacuation', 'طوافة الانزلاق للإخلاء', 600, '🛟', 'Multi-person inflatable slide and emergency sea rescue raft.', 'Toboggan et radeau de sauvetage.', 'منزلق قابل للنفخ وطوافة إنقاذ بحري طارئة.')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO aero_v22_groups (group_name, group_code, teacher_username)
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
    group_code: str = '7842'
    teacher_code: str = None

class LoginModel(BaseModel):
    phone_number: str
    password: str

class PasswordChangeModel(BaseModel):
    phone_number: str
    recovery_pin: str
    new_password: str

class AvatarUpdateModel(BaseModel):
    phone_number: str
    avatar_gender: str

class CreateExamModel(BaseModel):
    group_code: str
    teacher_username: str
    title: str
    exam_data: list

class SubmitExamModel(BaseModel):
    exam_id: int
    student_username: str
    student_name: str
    score: int
    total_questions: int
    time_spent_seconds: int

class DirectMessageModel(BaseModel):
    sender_username: str
    receiver_username: str
    sender_name: str
    content: str

class BuySkinModel(BaseModel):
    phone_number: str
    skin_name: str
    cost: int

class NodeCompleteModel(BaseModel):
    phone_number: str
    node_id: str
    lost_heart: bool = False

class RefillHeartsModel(BaseModel):
    phone_number: str

class FriendRequestModel(BaseModel):
    sender_username: str
    receiver_username: str

class AcceptFriendModel(BaseModel):
    username: str
    friend_username: str

class BattleInviteModel(BaseModel):
    sender_username: str
    sender_name: str
    receiver_username: str

class BattleRespondModel(BaseModel):
    match_id: str
    accept: bool

class BattleSubmitModel(BaseModel):
    match_id: str
    username: str
    score: int

class BattleCancelModel(BaseModel):
    match_id: str

class GroupUpdateModel(BaseModel):
    phone_number: str
    group_code: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    
    assigned_role = "student"
    group_code = data.group_code
    
    if data.role == "teacher":
        if data.teacher_code != "112233":
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Invalid teacher access code.")
        assigned_role = "teacher"
        group_code = str(random.randint(1000, 9999))

    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s OR username = %s;", (data.phone_number, data.username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number or username already taken.")
    
    cur.execute(
        """INSERT INTO aero_v22_users (phone_number, username, full_name, password, recovery_pin, role, avatar_gender, group_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;""",
        (data.phone_number, data.username, data.full_name, data.password, data.recovery_pin, assigned_role, data.avatar_gender, group_code)
    )
    user = cur.fetchone()

    if assigned_role == "teacher":
        cur.execute(
            "INSERT INTO aero_v22_groups (group_name, group_code, teacher_username) VALUES (%s, %s, %s) ON CONFLICT (group_code) DO NOTHING;",
            (f"{data.full_name}'s Flight Academy Group", group_code, data.username)
        )

    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.post("/api/login")
def login(data: LoginModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    today = date.today()
    last_prac = user.get("last_practice_date")
    streak = user.get("streak", 21)

    if last_prac and last_prac < today - timedelta(days=1):
        streak = 0
    elif not last_prac:
        streak = 0

    cur.execute("UPDATE aero_v22_users SET streak = %s WHERE id = %s RETURNING *;", (streak, user["id"]))
    updated_user = cur.fetchone()

    cur.close()
    conn.close()
    return {"status": "success", "user": updated_user}

@app.get("/api/user/refresh")
def refresh_user(phone_number: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (phone_number,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "success", "user": user}

@app.post("/api/user/refill-hearts")
def refill_hearts(data: RefillHeartsModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    import time
    now_ms = int(time.time() * 1000)
    last_refill = user.get("last_heart_refill_timestamp") or 0
    twenty_four_hours = 24 * 60 * 60 * 1000

    if now_ms - last_refill < twenty_four_hours:
        remaining_ms = twenty_four_hours - (now_ms - last_refill)
        rem_hrs = int(remaining_ms // (3600 * 1000))
        rem_mins = int((remaining_ms % (3600 * 1000)) // (60 * 1000))
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"24-hour limit active! Next free 5 hearts refill in {rem_hrs}h {rem_mins}m.")

    cur.execute("UPDATE aero_v22_users SET hearts = 5, last_heart_refill_timestamp = %s WHERE phone_number = %s RETURNING *;", (now_ms, data.phone_number))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated}

@app.post("/api/user/avatar-update")
def update_avatar(data: AvatarUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_users SET avatar_gender = %s WHERE phone_number = %s RETURNING *;", (data.avatar_gender, data.phone_number))
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.post("/api/user/password-change")
def change_password(data: PasswordChangeModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user or user["recovery_pin"] != data.recovery_pin:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid recovery PIN.")
    cur.execute("UPDATE aero_v22_users SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/user/group-update")
def update_user_group(data: GroupUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_groups WHERE group_code = %s;", (data.group_code,))
    grp = cur.fetchone()
    if not grp:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid teacher/group code.")
        
    cur.execute("UPDATE aero_v22_users SET group_code = %s WHERE phone_number = %s RETURNING *;", (data.group_code, data.phone_number))
    updated_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated_user}

@app.post("/api/friends/request")
def send_friend_request(data: FriendRequestModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE username = %s;", (data.receiver_username,))
    target = cur.fetchone()
    if not target:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    cur.execute(
        "INSERT INTO aero_v22_friend_requests (sender_username, receiver_username) VALUES (%s, %s) RETURNING *;",
        (data.sender_username, data.receiver_username)
    )
    req = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "request": req}

@app.get("/api/friends/list")
def get_friends_list(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT friends, username, full_name, avatar_gender FROM aero_v22_users WHERE username = %s;", (username,))
    u = cur.fetchone()
    if not u:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    friend_usernames = u.get("friends") or []
    friends_data = []
    if friend_usernames:
        cur.execute("SELECT username, full_name, avatar_gender, xp_points FROM aero_v22_users WHERE username = ANY(%s);", (friend_usernames,))
        friends_data = cur.fetchall()
    
    cur.execute("SELECT * FROM aero_v22_friend_requests WHERE receiver_username = %s AND status = 'pending';", (username,))
    incoming_requests = cur.fetchall()

    cur.close()
    conn.close()
    return {"friends": friends_data, "incoming_requests": incoming_requests, "friend_groups": []}

@app.post("/api/friends/accept")
def accept_friend_request(data: AcceptFriendModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_friend_requests SET status = 'accepted' WHERE sender_username = %s AND receiver_username = %s;", (data.friend_username, data.username))
    
    cur.execute("SELECT friends FROM aero_v22_users WHERE username = %s;", (data.username,))
    u1 = cur.fetchone()
    f1 = u1.get("friends") or []
    if data.friend_username not in f1: f1.append(data.friend_username)
    cur.execute("UPDATE aero_v22_users SET friends = %s WHERE username = %s;", (f1, data.username))

    cur.execute("SELECT friends FROM aero_v22_users WHERE username = %s;", (data.friend_username,))
    u2 = cur.fetchone()
    if u2:
        f2 = u2.get("friends") or []
        if data.username not in f2: f2.append(data.username)
        cur.execute("UPDATE aero_v22_users SET friends = %s WHERE username = %s;", (f2, data.friend_username))

    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/direct-messages/list")
def get_direct_messages(user1: str, user2: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM aero_v22_direct_messages 
        WHERE (sender_username = %s AND receiver_username = %s) 
           OR (sender_username = %s AND receiver_username = %s)
        ORDER BY id DESC LIMIT 50;
    """, (user1, user2, user2, user1))
    msgs = cur.fetchall()
    cur.close()
    conn.close()
    return {"messages": msgs[::-1]}

@app.post("/api/direct-messages/send")
def send_direct_message(data: DirectMessageModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_v22_direct_messages (sender_username, receiver_username, sender_name, content) VALUES (%s, %s, %s, %s) RETURNING *;",
        (data.sender_username, data.receiver_username, data.sender_name, data.content)
    )
    msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": msg}

@app.get("/api/group/info")
def get_group_info(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_groups WHERE group_code = %s;", (group_code,))
    grp = cur.fetchone()
    cur.execute("SELECT username, full_name, role, avatar_gender, xp_points FROM aero_v22_users WHERE group_code = %s;", (group_code,))
    members = cur.fetchall()
    cur.execute("SELECT * FROM aero_v22_lessons WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    lessons = cur.fetchall()
    cur.execute("SELECT * FROM aero_v22_exams WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    exams = cur.fetchall()
    cur.close()
    conn.close()
    return {"group": grp, "members": members, "lessons": lessons, "exams": exams}

@app.post("/api/exam/create")
def create_exam(data: CreateExamModel):
    conn = get_db_connection()
    cur = conn.cursor()
    import json
    cur.execute(
        "INSERT INTO aero_v22_exams (group_code, teacher_username, title, exam_data) VALUES (%s, %s, %s, %s) RETURNING *;",
        (data.group_code, data.teacher_username, data.title, json.dumps(data.exam_data))
    )
    exam = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "exam": exam}

@app.post("/api/exam/submit")
def submit_exam(data: SubmitExamModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_v22_exam_submissions (exam_id, student_username, student_name, score, total_questions, time_spent_seconds) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.exam_id, data.student_username, data.student_name, data.score, data.total_questions, data.time_spent_seconds)
    )
    sub = cur.fetchone()
    cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 100 WHERE username = %s;", (data.student_username,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "submission": sub}

@app.post("/api/node/complete")
def complete_roadmap_node(data: NodeCompleteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT completed_nodes, xp_points, hearts, streak FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    nodes = user.get("completed_nodes") or []
    hearts = user.get("hearts", 5)
    xp = user.get("xp_points", 0)
    streak = user.get("streak", 0)

    if data.lost_heart:
        hearts = max(0, hearts - 1)
        cur.execute("UPDATE aero_v22_users SET hearts = %s, last_heart_loss_date = %s WHERE phone_number = %s;", (hearts, date.today(), data.phone_number))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "completed_nodes": nodes, "xp": xp, "hearts": hearts, "streak": streak}

    if hearts <= 0:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Out of hearts! Visit the Heart Recovery Lounge.")

    today = date.today()
    streak += 1

    if data.node_id not in nodes:
        nodes.append(data.node_id)
        cur.execute("UPDATE aero_v22_users SET completed_nodes = %s, xp_points = xp_points + 30, streak = %s, last_practice_date = %s WHERE phone_number = %s RETURNING completed_nodes, xp_points, hearts, streak;", (nodes, streak, today, data.phone_number))
    else:
        cur.execute("UPDATE aero_v22_users SET streak = %s, last_practice_date = %s WHERE phone_number = %s RETURNING completed_nodes, xp_points, hearts, streak;", (streak, today, data.phone_number))
    res = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "completed_nodes": res["completed_nodes"], "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}

@app.get("/api/shop/skins")
def get_skins():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_shop_skins ORDER BY cost ASC;")
    skins = cur.fetchall()
    cur.close()
    conn.close()
    return {"skins": skins}

@app.post("/api/shop/buy")
def buy_skin(data: BuySkinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
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
    cur.execute("UPDATE aero_v22_users SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated}

@app.post("/api/battle/invite")
def send_battle_invite(data: BattleInviteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    match_id = f"match_{int(random.randint(100000, 999999))}"
    
    raw_questions = [
        {"q": "How is letter 'A' pronounced in ICAO standard telephony?", "options": ["Alpha", "Apple", "Adam", "Anchor"], "correct": 0},
        {"q": "What is the correct ICAO pronunciation for number '9'?", "options": ["Nine", "Niner", "Nov", "Ninth"], "correct": 1},
        {"q": "Which phonetic word represents letter 'S'?", "options": ["Sugar", "Sam", "Sierra", "Sun"], "correct": 2},
        {"q": "What is the primary phrase for seatbelt compliance check?", "options": ["Please fasten belts", "Cabin crew, secure cabin for takeoff", "Fasten seatbelts please", "Check cabin belts"], "correct": 1},
        {"q": "During turbulence, what command is issued to cabin crew?", "options": ["Continue service", "Crew, be seated and secure", "Stand by galley", "Secure meal carts"], "correct": 1},
        {"q": "How do you announce emergency slide arming?", "options": ["Open all doors", "Disarm doors", "Cabin crew, arm slides and cross-check", "Check slides"], "correct": 2},
        {"q": "What command is shouted during rapid land evacuation?", "options": ["Please exit slowly", "EFP, LEAVE BAGS, DOWN THE SLIDE!", "Grab your luggage and jump", "Walk to exit"], "correct": 1},
        {"q": "What urgent prefix is used for non-immediate safety urgency?", "options": ["MAYDAY", "SECURITY", "PAN-PAN", "URGENT"], "correct": 2},
        {"q": "How many times is MAYDAY repeated in distress calls?", "options": ["Once", "Three times", "Two times", "Five times"], "correct": 1},
        {"q": "What term describes sudden severe vertical air movement?", "options": ["Wind shear / Turbulence", "Gentle breeze", "Thermal calm", "Air pocket"], "correct": 0}
    ]
    
    random.shuffle(raw_questions)
    selected_raw = raw_questions[:8]
    randomized_questions = []
    for item in selected_raw:
        opts = list(item["options"])
        correct_text = opts[item["correct"]]
        random.shuffle(opts)
        new_correct_idx = opts.index(correct_text)
        randomized_questions.append({
            "q": item["q"],
            "options": opts,
            "correct": new_correct_idx
        })
    
    import json
    cur.execute(
        "INSERT INTO aero_v22_battles (match_id, sender_username, sender_name, receiver_username, status, questions) VALUES (%s, %s, %s, %s, 'pending', %s) RETURNING *;",
        (match_id, data.sender_username, data.sender_name, data.receiver_username, json.dumps(randomized_questions))
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"match_id": match_id, "status": "sent"}

@app.get("/api/battle/incoming")
def get_incoming_battle(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_battles WHERE receiver_username = %s AND status = 'pending' ORDER BY created_at DESC LIMIT 1;", (username,))
    invite = cur.fetchone()
    cur.close()
    conn.close()
    return {"invite": invite}

@app.post("/api/battle/respond")
def respond_battle_invite(data: BattleRespondModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (data.match_id,))
    match = cur.fetchone()
    if not match:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
        
    new_status = "accepted" if data.accept else "rejected"
    cur.execute("UPDATE aero_v22_battles SET status = %s WHERE match_id = %s RETURNING *;", (new_status, data.match_id))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": new_status, "questions": updated["questions"]}

@app.get("/api/battle/status")
def get_battle_status(match_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (match_id,))
    match = cur.fetchone()
    cur.close()
    conn.close()
    if not match:
        return {"status": "not_found"}
    return {"status": match["status"], "questions": match.get("questions", [])}

@app.post("/api/battle/cancel")
def cancel_battle(data: BattleCancelModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_battles SET status = 'canceled' WHERE match_id = %s;", (data.match_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "canceled"}

@app.post("/api/battle/submit")
def submit_battle_score(data: BattleSubmitModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (data.match_id,))
    match = cur.fetchone()
    if not match:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
        
    scores = match.get("scores") or {}
    scores[data.username] = data.score
    
    import json
    cur.execute("UPDATE aero_v22_battles SET scores = %s WHERE match_id = %s;", (json.dumps(scores), data.match_id))
    conn.commit()
    
    opponent_score = random.randint(2, 6)
    result = "loss"
    if data.score > opponent_score:
        result = "win"
        cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 100 WHERE username = %s;", (data.username,))
    elif data.score == opponent_score:
        result = "draw"
        cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 50 WHERE username = %s;", (data.username,))
    
    conn.commit()
    cur.close()
    conn.close()
    return {
        "status": "completed",
        "your_score": data.score,
        "opponent_score": opponent_score,
        "result": result
    }

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
