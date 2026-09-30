import os
import random
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aero Crew Academy - Millennium Edition", version="28.0.0")

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
            completed_nodes TEXT[] DEFAULT ARRAY[]::TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

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
        CREATE TABLE IF NOT EXISTS aero_v22_friend_groups (
            id SERIAL PRIMARY KEY,
            group_name VARCHAR(100),
            creator_username VARCHAR(50),
            members TEXT[] DEFAULT ARRAY[]::TEXT[],
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
        CREATE TABLE IF NOT EXISTS aero_v22_friend_group_messages (
            id SERIAL PRIMARY KEY,
            group_id INT,
            sender_username VARCHAR(50),
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
        CREATE TABLE IF NOT EXISTS aero_v22_quiz_results (
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
        ('emergency', 'Marine', 'Slide-Raft Unit', 'Toboggan-Radeau d’Évacuation', 'طوافة الانزلاق للإخلاء', 600, '🛟', 'Multi-person inflatable slide and emergency sea rescue raft.', 'Toboggan et radeau de sauvetage.', 'منزلق قابل للنفخ وطوافة إنقاذ بحري طارئة.'),
        ('safety', 'Protection', 'Smoke Hood PBE', 'Cagoule Anti-Fumée PBE', 'قناع الدخان واقي الحريق', 500, '🪖', 'Protective Breathing Equipment smoke hood for firefighting.', 'Équipement de protection respiratoire anti-fumée.', 'معدات الحماية التنفسية لمقاومة الدخان والحريق.'),
        ('medical', 'FirstAid', 'Emergency Medical Kit', 'Trousse de Secours Médicale', 'حقيبة الإسعافات الأولية الطارئة', 450, '🩺', 'Comprehensive onboard medical response kit for crew use.', 'Trousse médicale d’urgence à bord.', 'حقيبة استجابة طبية شاملة على متن الطائرة للطاقم.')
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

class SubmitQuizModel(BaseModel):
    lesson_id: int
    student_username: str
    student_name: str
    score: int
    total_questions: int

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

class CreateFriendGroupModel(BaseModel):
    group_name: str
    creator_username: str
    members: list

class FriendGroupMessageModel(BaseModel):
    group_id: int
    sender_username: str
    sender_name: str
    content: str

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
            raise HTTPException(status_code=403, detail="Invalid 6-digit teacher access code. Unauthorized registration.")
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

    from datetime import date, timedelta
    today = date.today()
    last_prac = user["last_practice_date"]
    streak = user["streak"]

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
    
    if user["xp_points"] < 50:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough XP stars to refill hearts (Cost: 50 ⭐).")

    new_xp = user["xp_points"] - 50
    cur.execute("UPDATE aero_v22_users SET hearts = 5, xp_points = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.phone_number))
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
    friend_usernames = u["friends"] or []
    friends_data = []
    if friend_usernames:
        cur.execute("SELECT username, full_name, avatar_gender, xp_points FROM aero_v22_users WHERE username = ANY(%s);", (friend_usernames,))
        friends_data = cur.fetchall()
    
    cur.execute("SELECT * FROM aero_v22_friend_requests WHERE receiver_username = %s AND status = 'pending';", (username,))
    incoming_requests = cur.fetchall()

    cur.execute("SELECT * FROM aero_v22_friend_groups WHERE %s = ANY(members) OR creator_username = %s;", (username, username))
    friend_groups = cur.fetchall()

    cur.close()
    conn.close()
    return {"friends": friends_data, "incoming_requests": incoming_requests, "friend_groups": friend_groups}

@app.post("/api/friends/accept")
def accept_friend_request(data: AcceptFriendModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_friend_requests SET status = 'accepted' WHERE sender_username = %s AND receiver_username = %s;", (data.friend_username, data.username))
    
    cur.execute("SELECT friends FROM aero_v22_users WHERE username = %s;", (data.username,))
    u1 = cur.fetchone()
    f1 = u1["friends"] or []
    if data.friend_username not in f1: f1.append(data.friend_username)
    cur.execute("UPDATE aero_v22_users SET friends = %s WHERE username = %s;", (f1, data.username))

    cur.execute("SELECT friends FROM aero_v22_users WHERE username = %s;", (data.friend_username,))
    u2 = cur.fetchone()
    if u2:
        f2 = u2["friends"] or []
        if data.username not in f2: f2.append(data.username)
        cur.execute("UPDATE aero_v22_users SET friends = %s WHERE username = %s;", (f2, data.friend_username))

    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/friend-groups/create")
def create_friend_group(data: CreateFriendGroupModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_v22_friend_groups (group_name, creator_username, members) VALUES (%s, %s, %s) RETURNING *;",
        (data.group_name, data.creator_username, data.members)
    )
    grp = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "group": grp}

@app.get("/api/friend-groups/messages")
def get_friend_group_messages(group_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_friend_group_messages WHERE group_id = %s ORDER BY id DESC LIMIT 50;", (group_id,))
    msgs = cur.fetchall()
    cur.close()
    conn.close()
    return {"messages": msgs[::-1]}

@app.post("/api/friend-groups/send")
def send_friend_group_message(data: FriendGroupMessageModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aero_v22_friend_group_messages (group_id, sender_username, sender_name, content) VALUES (%s, %s, %s, %s) RETURNING *;",
        (data.group_id, data.sender_username, data.sender_name, data.content)
    )
    msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": msg}

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

@app.post("/api/lesson/create")
def create_lesson(data: CreateLessonModel):
    conn = get_db_connection()
    cur = conn.cursor()
    import json
    cur.execute(
        "INSERT INTO aero_v22_lessons (group_code, teacher_username, title, content_html, quiz_data) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (data.group_code, data.teacher_username, data.title, data.content_html, json.dumps(data.quiz_data))
    )
    lesson = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "lesson": lesson}

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

@app.get("/api/teacher/analytics")
def get_teacher_analytics(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, l.title as lesson_title 
        FROM aero_v22_quiz_results r 
        JOIN aero_v22_lessons l ON l.id = r.lesson_id 
        WHERE l.group_code = %s 
        ORDER BY r.completed_at DESC;
    """, (group_code,))
    quiz_results = cur.fetchall()

    cur.execute("""
        SELECT s.*, e.title as exam_title 
        FROM aero_v22_exam_submissions s 
        JOIN aero_v22_exams e ON e.id = s.exam_id 
        WHERE e.group_code = %s 
        ORDER BY s.submitted_at DESC;
    """, (group_code,))
    exam_submissions = cur.fetchall()

    cur.close()
    conn.close()
    return {"quiz_results": quiz_results, "exam_submissions": exam_submissions}

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

@app.post("/api/quiz/submit")
def submit_quiz(data: SubmitQuizModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_quiz_results WHERE lesson_id = %s AND student_username = %s;", (data.lesson_id, data.student_username))
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE aero_v22_quiz_results SET score = %s, total_questions = %s, attempts = attempts + 1, completed_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *;",
            (data.score, data.total_questions, existing["id"])
        )
    else:
        cur.execute(
            "INSERT INTO aero_v22_quiz_results (lesson_id, student_username, student_name, score, total_questions, attempts) VALUES (%s, %s, %s, %s, %s, 1) RETURNING *;",
            (data.lesson_id, data.student_username, data.student_name, data.score, data.total_questions)
        )
    res = cur.fetchone()
    cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 50 WHERE username = %s;", (data.student_username,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "result": res}

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
    
    nodes = user["completed_nodes"] or []
    hearts = user["hearts"]
    xp = user["xp_points"]
    streak = user["streak"]
    from datetime import date

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

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aero Crew Academy - Millennium Edition</title>
    <link rel="icon" href="https://img.icons8.com/color/48/airplane-take-off.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Tajawal:wght@450;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #020617;
            --surface: #0b0f19;
            --surface-card: rgba(19, 27, 46, 0.88);
            --surface-card-hover: rgba(28, 40, 68, 0.95);
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.4);
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --gold: #fbbf24;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(30, 41, 59, 0.8);
            --border-glow: rgba(56, 189, 248, 0.3);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        [dir="rtl"] * { font-family: 'Tajawal', sans-serif !important; }
        
        body { 
            background-color: #020617 !important;
            background-image: linear-gradient(rgba(2, 6, 23, 0.75), rgba(2, 6, 23, 0.85)), url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1920&q=80') !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-attachment: fixed !important;
            background-size: cover !important;
            color: var(--text-main); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            padding: 1rem; 
            position: relative;
        }

        .app-shell { width: 100%; max-width: 680px; background: rgba(11, 15, 25, 0.92); backdrop-filter: blur(18px); border-radius: 36px; padding: 2rem; border: 1px solid var(--border-glow); box-shadow: 0 45px 90px rgba(0, 0, 0, 0.95); position: relative; z-index: 2; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.4rem; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.2rem; color: var(--accent); text-shadow: 0 0 15px var(--accent-glow); }
        .brand-title img { width: 34px; height: 34px; }
        
        .header-controls { display: flex; align-items: center; gap: 8px; }
        .header-icon-btn { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 12px; width: 38px; height: 38px; display: flex; justify-content: center; align-items: center; cursor: pointer; font-size: 1.1rem; transition: all 0.2s; }
        .header-icon-btn:hover { border-color: var(--accent); background: var(--accent-glow); transform: scale(1.05); }

        h2 { font-weight: 800; margin-bottom: 0.4rem; font-size: 1.4rem; color: white; }
        p.sub-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.4rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem; }
        input, select, textarea { width: 100%; padding: 0.9rem 1.1rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 0.92rem; margin-bottom: 1rem; outline: none; transition: all 0.2s; }
        input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 0.98rem; cursor: pointer; box-shadow: 0 6px 20px var(--accent-glow); transition: transform 0.1s; margin-top: 0.4rem; margin-bottom: 0.4rem; }
        .btn-action:active { transform: scale(0.98); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; font-size: 0.82rem; }
        .footer-nav span { color: var(--accent); font-weight: 700; cursor: pointer; }
        .footer-nav span:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        .avatar-preview-box { width: 110px; height: 110px; border-radius: 50%; background: linear-gradient(135deg, #1e293b, #0f172a); border: 3px solid var(--accent); display: flex; justify-content: center; align-items: center; margin: 0 auto 1.2rem auto; position: relative; box-shadow: 0 0 25px var(--accent-glow); font-size: 3rem; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.85rem 1.1rem; border-radius: 18px; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; cursor: pointer; }
        .stat-item { font-weight: 800; font-size: 0.82rem; display: flex; align-items: center; gap: 5px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 1.1rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.2s; }
        .mode-tile:hover { border-color: var(--accent); transform: translateY(-2px); background: var(--surface-card-hover); box-shadow: 0 0 20px var(--accent-glow); }
        .mode-tile h4 { font-size: 0.85rem; font-weight: 800; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 22px; padding: 1.5rem; border: 1px solid var(--border-glow); margin-bottom: 1.1rem; min-height: 290px; }
        
        .path-backdrop-y1 {
            background: linear-gradient(135deg, rgba(2, 6, 23, 0.85) 0%, rgba(15, 23, 42, 0.92) 100%), 
                        url('https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80') center/cover no-repeat !important;
        }
        .path-backdrop-y2 {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.92) 100%), 
                        url('https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80') center/cover no-repeat !important;
        }
        .path-backdrop-eng {
            background: linear-gradient(135deg, rgba(2, 6, 23, 0.85) 0%, rgba(3, 105, 161, 0.82) 100%), 
                        url('https://images.unsplash.com/photo-1519074069444-1ba4ea16d66c?auto=format&fit=crop&w=1200&q=80') center/cover no-repeat !important;
        }

        .duo-path-container { 
            display: flex; 
            flex-direction: column; 
            gap: 24px; 
            padding: 20px 10px; 
            max-height: 360px; 
            overflow-y: auto; 
            border-radius: 18px; 
            border: 1px solid var(--border-glow);
            scrollbar-width: none; 
            -ms-overflow-style: none;
        }
        .duo-path-container::-webkit-scrollbar { display: none; }

        .duo-node-wrapper { display: flex; width: 100%; position: relative; }
        
        .duo-node-wrapper:nth-child(odd) { justify-content: flex-start; padding-left: 18%; }
        .duo-node-wrapper:nth-child(even) { justify-content: flex-end; padding-right: 18%; }

        .duo-node { width: 68px; height: 68px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; font-weight: 900; font-size: 1.1rem; cursor: pointer; position: relative; box-shadow: 0 8px 0 rgba(0,0,0,0.4); transition: transform 0.2s; z-index: 2; }
        .duo-node:hover { transform: scale(1.1); }
        .duo-node.completed { background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); color: #451a03; border: 4px solid #fef3c7; box-shadow: 0 8px 0 #b45309, 0 0 20px rgba(251,191,36,0.5); }
        .duo-node.active { background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: #020617; border: 4px solid #bae6fd; box-shadow: 0 8px 0 #0369a1, 0 0 25px var(--accent); }
        .duo-node.locked { background: #334155; color: #94a3b8; border: 4px solid #475569; box-shadow: 0 8px 0 #1e293b; opacity: 0.7; }
        
        .companion-hopper { position: absolute; top: -34px; font-size: 2rem; animation: floatCompanion 1.5s infinite ease-in-out; z-index: 10; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.7)); }
        @keyframes floatCompanion { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }

        .chat-container { display: flex; flex-direction: column; height: 340px; background: var(--bg-deep); border-radius: 16px; border: 1px solid var(--border-glow); overflow: hidden; }
        .chat-messages { flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; scrollbar-width: none; }
        .chat-messages::-webkit-scrollbar { display: none; }
        .chat-bubble { max-width: 80%; padding: 10px 14px; border-radius: 16px; font-size: 0.84rem; line-height: 1.4; }
        .chat-bubble.incoming { background: var(--surface-card); color: white; align-self: flex-start; }
        .chat-bubble.outgoing { background: #0284c7; color: white; align-self: flex-end; }
        .chat-input-bar { display: flex; gap: 8px; padding: 10px; background: var(--surface-card); border-top: 1px solid var(--border); align-items: center; }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 14px 28px; border-radius: 35px; font-weight: 800; font-size: 0.9rem; transition: transform 0.3s; z-index: 6000; pointer-events: none; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4); }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Logo">
                <span id="brand-logo-text">Aero Crew Millennium</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div id="prelogin-lang-bar" style="display: flex; gap: 4px;">
                    <button onclick="setLanguage('en')" style="background:var(--surface-card); color:white; border:1px solid var(--border-glow); padding:4px 8px; border-radius:8px; font-size:0.75rem; cursor:pointer;">EN</button>
                    <button onclick="setLanguage('fr')" style="background:var(--surface-card); color:white; border:1px solid var(--border-glow); padding:4px 8px; border-radius:8px; font-size:0.75rem; cursor:pointer;">FR</button>
                    <button onclick="setLanguage('ar')" style="background:var(--surface-card); color:white; border:1px solid var(--border-glow); padding:4px 8px; border-radius:8px; font-size:0.75rem; cursor:pointer;">AR</button>
                </div>
                <div class="header-controls hidden" id="dash-header-icons">
                    <div class="header-icon-btn" onclick="openAvatarStudio()" title="Avatar">👤</div>
                    <div class="header-icon-btn" onclick="openShop()" title="Boutique">🎁</div>
                    <div class="header-icon-btn" onclick="openSettingsModal()" title="Settings">⚙</div>
                </div>
            </div>
        </div>

        <!-- LOGIN SCREEN -->
        <div id="screen-login">
            <h2 id="tr-login-title">Cabin Crew Portal</h2>
            <p class="sub-desc" id="tr-login-sub">Access accredited EASA/ICAO curriculum & live groups.</p>
            
            <label id="tr-lbl-phone">Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label id="tr-lbl-pass">Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn-action" onclick="submitLogin()" id="tr-login-btn">Sign In to Simulator</button>
            
            <div class="footer-nav">
                <span onclick="navigateTo('screen-register')" id="tr-nav-reg">Create Account</span>
                <span onclick="navigateTo('screen-reset')" id="tr-nav-reset">Forgot Password?</span>
            </div>
        </div>

        <!-- REGISTER SCREEN -->
        <div id="screen-register" class="hidden">
            <h2 id="tr-reg-title">Cadet & Instructor Enrollment</h2>
            <p class="sub-desc" id="tr-reg-sub">Register your profile, choose your role, and design your avatar.</p>
            
            <div class="avatar-preview-box" id="reg-avatar-preview">🧯</div>

            <label id="tr-reg-role-lbl">Register As</label>
            <select id="reg-role" onchange="toggleTeacherCodeContainer()">
                <option value="student" id="tr-opt-cadet">🎓 Cadet / Student</option>
                <option value="teacher" id="tr-opt-teacher">👨‍🏫 Instructor / Teacher</option>
            </select>

            <div id="teacher-code-box" class="hidden" style="background: rgba(56, 189, 248, 0.08); padding: 12px; border-radius: 14px; border: 1px dashed var(--accent); margin-bottom: 1rem;">
                <label style="color: var(--accent);">🔒 6-Digit Teacher Verification Code</label>
                <input type="password" id="reg-teacher-code" placeholder="Enter 6-digit teacher code" maxlength="6" style="letter-spacing: 3px; text-align: center; margin-bottom:0;" />
            </div>

            <label id="tr-reg-name-lbl">Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label id="tr-reg-user-lbl">Unique Username</label>
            <input type="text" id="reg-username" placeholder="@username" />

            <label id="tr-reg-phone-lbl">Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label id="tr-reg-pass-lbl">Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label id="tr-reg-pin-lbl">Recovery PIN (4 digits)</label>
            <input type="password" id="reg-pin" placeholder="PIN" maxlength="4" />

            <h3 style="font-size:1rem; color:var(--accent); margin: 1rem 0 0.5rem 0; font-weight:800;" id="tr-avatar-studio-title">🎨 Avatar Customization</h3>
            
            <label id="tr-avatar-type-lbl">Avatar Type</label>
            <select id="reg-gender" onchange="updateRegAvatarPreview()">
                <option value="steward">👔 Steward</option>
                <option value="hostess">👗 Hostess</option>
            </select>
            
            <button class="btn-action" onclick="submitRegister()" style="background: #10b981; color: white;" id="tr-complete-reg-btn">Complete Registration</button>
            
            <div class="footer-nav">
                <span onclick="navigateTo('screen-login')" id="tr-back-login">Already have an account? Sign In</span>
            </div>
        </div>

        <!-- RESET SCREEN -->
        <div id="screen-reset" class="hidden">
            <h2 id="tr-reset-title">Recovery PIN Reset</h2>
            <p class="sub-desc" id="tr-reset-sub">Enter your phone and secret recovery PIN.</p>
            <label id="tr-reset-phone-lbl">Phone Number</label>
            <input type="tel" id="reset-phone" placeholder="Phone" />
            <label id="tr-reset-pin-lbl">Secret Recovery PIN</label>
            <input type="password" id="reset-pin" placeholder="PIN" maxlength="4" />
            <label id="tr-reset-new-lbl">New Password</label>
            <input type="password" id="reset-new" placeholder="New Password" />
            <button class="btn-action" onclick="submitReset()" style="background: #f59e0b; color: #020617;" id="tr-update-cred-btn">Update Credentials</button>
            <div class="footer-nav">
                <span onclick="navigateTo('screen-login')" id="tr-back-login2">Back to Sign In</span>
            </div>
        </div>

        <!-- DASHBOARD SCREEN -->
        <div id="screen-dashboard" class="hidden">
            <div class="stats-dashboard" onclick="openHeartRecoveryLounge()" title="Heart Recovery Lounge">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent); font-weight: 900;">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted);" id="dash-role-badge">Student</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">1500</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);" id="dash-streak-badge">🔥 <span id="dash-streak">21</span></div>
                </div>
            </div>

            <div class="mode-grid">
                <div class="mode-tile" onclick="launchRoadmap('year1')">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4 id="tr-tile-y1">First Year Path (100 Nodes)</h4>
                </div>
                <div class="mode-tile" onclick="launchRoadmap('year2')">
                    <span style="font-size: 1.4rem;">🏆</span>
                    <h4 id="tr-tile-y2">Second Year Path (100 Nodes)</h4>
                </div>
                <div class="mode-tile" onclick="launchAviationEnglishRoadmap()">
                    <span style="font-size: 1.4rem;">🌐</span>
                    <h4 id="tr-tile-eng">Aviation English & ICAO Mastery</h4>
                </div>
                <div class="mode-tile" onclick="openStudyHub()">
                    <span style="font-size: 1.4rem;">📚</span>
                    <h4 id="tr-tile-study">Lessons, Quizzes & Exams Studio</h4>
                </div>
                <div class="mode-tile" onclick="openSocialHub()" style="grid-column: span 2;">
                    <span style="font-size: 1.4rem;">💬</span>
                    <h4 id="tr-tile-social">Friends, Private Chat & Groups</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container">
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;" id="tr-center-title">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;" id="tr-center-desc">Select <b>First Year Path</b>, <b>Second Year Path</b>, or <b>Aviation English</b> above to begin your randomized anti-cheat learning adventure with your equipped equipment companion.</p>
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1; margin-top:0;" id="tr-hub-btn">← Hub</button>
                <button class="btn-action" onclick="logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1; margin-top:0;" id="tr-logout-btn">Logout 🚪</button>
            </div>
        </div>
    </div>

    <!-- AVATAR STUDIO MODAL -->
    <div id="avatar-studio-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); display:none; justify-content:center; align-items:center; z-index:5000;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:440px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <h3 style="font-size:1.1rem; font-weight:900; color:white;" id="tr-modal-avatar-title">🎨 Edit Avatar</h3>
                <button onclick="closeAvatarStudio()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>
            <div class="avatar-preview-box" id="modal-avatar-preview">👔</div>
            <label id="tr-modal-gender-lbl">Gender / Style</label>
            <select id="mod-gender" onchange="updateModalAvatarPreview()">
                <option value="steward">👔 Steward</option>
                <option value="hostess">👗 Hostess</option>
            </select>
            <button class="btn-action" onclick="saveAvatarChanges()" style="background:var(--success); color:white;" id="tr-save-avatar-btn">Save Avatar 💾</button>
        </div>
    </div>

    <!-- SETTINGS MODAL -->
    <div id="settings-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.9); display:none; justify-content:center; align-items:center; z-index:5000;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:28px; padding:2rem; width:90%; max-width:400px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
                <h3 style="font-size:1.2rem; font-weight:900; color:white;" id="tr-settings-title">⚙️ Academy Settings</h3>
                <button onclick="closeSettingsModal()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
            </div>

            <div style="background:var(--bg-deep); padding:10px 14px; border-radius:12px; margin-bottom:1rem; border:1px solid var(--border-glow);">
                <label id="tr-my-username-lbl" style="color:var(--accent);">My Username</label>
                <div id="settings-my-username" style="font-weight:800; font-size:0.95rem; color:white;">@username</div>
            </div>
            
            <label id="tr-lang-lbl">Interface Language</label>
            <div style="display:flex; gap:8px; margin-bottom:1.2rem;">
                <button onclick="setLanguage('en')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow); margin-top:0; margin-bottom:0;">English 🇬🇧</button>
                <button onclick="setLanguage('fr')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow); margin-top:0; margin-bottom:0;">Français 🇫🇷</button>
                <button onclick="setLanguage('ar')" class="btn-action" style="padding:8px; font-size:0.8rem; background:var(--bg-deep); color:white; border:1px solid var(--border-glow); margin-top:0; margin-bottom:0;">العربية 🇸🇦</button>
            </div>

            <label id="tr-pass-change-lbl">Change Password</label>
            <input type="password" id="set-pin" placeholder="Recovery PIN (4 digits)" maxlength="4" />
            <input type="password" id="set-new-pass" placeholder="New Password" />
            <button class="btn-action" onclick="submitPasswordChangeModal()" style="background:var(--warning); color:var(--bg-deep);" id="tr-update-pass-btn">Update Password 🔒</button>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('aero_crew_user_pro22') || 'null');
        let groupInfo = { group: null, members: [], lessons: [], exams: [] };
        let socialData = { friends: [], incoming_requests: [], friend_groups: [] };
        let mediaRecorder = null;
        let audioChunks = [];
        let activeLang = localStorage.getItem('aero_lang') || 'en';
        let dmPollingInterval = null;
        let groupMsgPollingInterval = null;
        let questionTimerInterval = null;

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        function playSound(type) {
            if(!audioCtx) return;
            if(audioCtx.state === 'suspended') audioCtx.resume();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            
            if(type === 'click') {
                osc.frequency.setValueAtTime(600, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(400, audioCtx.currentTime + 0.05);
                gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.05);
                osc.start(); osc.stop(audioCtx.currentTime + 0.05);
            } else if(type === 'success') {
                osc.frequency.setValueAtTime(523.25, audioCtx.currentTime);
                osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.08);
                osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.16);
                gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                osc.start(); osc.stop(audioCtx.currentTime + 0.3);
            } else if(type === 'error') {
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(220, audioCtx.currentTime);
                osc.frequency.setValueAtTime(150, audioCtx.currentTime + 0.1);
                gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
                osc.start(); osc.stop(audioCtx.currentTime + 0.25);
            }
        }

        const dict = {
            en: {
                brand: "Aero Crew Millennium",
                loginTitle: "Cabin Crew Portal", loginSub: "Access accredited EASA/ICAO curriculum & live groups.",
                phoneLbl: "Phone Number", passLbl: "Password", loginBtn: "Sign In to Simulator",
                regNav: "Create Account", resetNav: "Forgot Password?",
                regTitle: "Cadet & Instructor Enrollment", regSub: "Register your profile, choose your role, and design your avatar.",
                regRoleLbl: "Register As", optCadet: "🎓 Cadet / Student", optTeacher: "👨‍🏫 Instructor / Teacher",
                regNameLbl: "Full Name", regUserLbl: "Unique Username", regPassLbl: "Password", regPinLbl: "Recovery PIN (4 digits)",
                avatarStudioTitle: "🎨 Avatar Customization", avatarTypeLbl: "Avatar Type", optSteward: "👔 Steward", optHostess: "👗 Hostess",
                completeRegBtn: "Complete Registration", backLogin: "Already have an account? Sign In",
                resetTitle: "Recovery PIN Reset", resetSub: "Enter your phone and secret recovery PIN.", resetNewLbl: "New Password",
                updateCredBtn: "Update Credentials", backLogin2: "Back to Sign In",
                tileY1: "First Year Path (100 Nodes)", tileY2: "Second Year Path (100 Nodes)", tileEng: "Aviation English & ICAO Mastery",
                tileStudy: "Lessons, Quizzes & Exams Studio", tileSocial: "Friends, Private Chat & Groups",
                centerTitle: "EASA Professional Training Center", centerDesc: "Select <b>First Year Path</b>, <b>Second Year Path</b>, or <b>Aviation English</b> above to begin your randomized anti-cheat learning adventure.",
                hubBtn: "← Hub", logoutBtn: "Logout 🚪",
                modalAvatarTitle: "🎨 Edit Avatar", modalGenderLbl: "Gender / Style", saveAvatarBtn: "Save Avatar 💾",
                settingsTitle: "⚙️ Academy Settings", langLbl: "Interface Language", passChangeLbl: "Change Password", updatePassBtn: "Update Password 🔒",
                myUsernameLbl: "My Username"
            },
            fr: {
                brand: "Aero Crew Millennium",
                loginTitle: "Portail du Personnel de Cabine", loginSub: "Accédez au programme EASA/ICAO et aux groupes.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                regTitle: "Inscription Cadet & Instructeur", regSub: "Enregistrez votre profil, choisissez votre rôle et votre avatar.",
                regRoleLbl: "S'inscrire en tant que", optCadet: "🎓 Cadet / Étudiant", optTeacher: "👨‍🏫 Instructeur / Professeur",
                regNameLbl: "Nom complet", regUserLbl: "Nom d'utilisateur unique", regPassLbl: "Mot de passe", regPinLbl: "PIN de récupération (4 chiffres)",
                avatarStudioTitle: "🎨 Personnalisation d'Avatar", avatarTypeLbl: "Type d'avatar", optSteward: "👔 Steward", optHostess: "👗 Hôtesse",
                completeRegBtn: "Terminer l'inscription", backLogin: "Déjà un compte ? Se connecter",
                resetTitle: "Réinitialisation du PIN", resetSub: "Entrez votre téléphone et votre PIN de récupération secret.", resetNewLbl: "Nouveau mot de passe",
                updateCredBtn: "Mettre à jour", backLogin2: "Retour à la connexion",
                tileY1: "Parcours 1ère Année (100 Nœuds)", tileY2: "Parcours 2ème Année (100 Nœuds)", tileEng: "Anglais Aéronautique & ICAO",
                tileStudy: "Studio Leçons, Quiz & Examens", tileSocial: "Amis, Chat Privé & Groupes",
                centerTitle: "Centre de Formation Professionnelle EASA", centerDesc: "Sélectionnez <b>Parcours 1ère Année</b>, <b>2ème Année</b> ou <b>Anglais Aéronautique</b> pour débuter votre parcours aléatoire anti-triche.",
                hubBtn: "← Accueil", logoutBtn: "Déconnexion 🚪",
                modalAvatarTitle: "🎨 Modifier l'Avatar", modalGenderLbl: "Genre / Style", saveAvatarBtn: "Enregistrer 💾",
                settingsTitle: "⚙ Paramètres", langLbl: "Langue de l'interface", passChangeLbl: "Changer le mot de passe", updatePassBtn: "Mettre à jour 🔒",
                myUsernameLbl: "Mon Nom d'utilisateur"
            },
            ar: {
                brand: "Aero Crew Millennium",
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى مناهج EASA والمجموعات الحية المعتمدة.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول",
                regNav: "إنشاء حساب", resetNav: "نسيت كلمة المرور؟",
                regTitle: "تسجيل المتدربين والمدربين", regSub: "سجل ملفك الشخصي واجتاز التدريب وصمم صورتك الرمزية.",
                regRoleLbl: "التسجيل كـ", optCadet: "🎓 متدرب / طالب", optTeacher: "👨‍‍🏫 مدرب / معلم",
                regNameLbl: "الاسم الكامل", regUserLbl: "اسم المستخدم الفريد", regPassLbl: "كلمة المرور", regPinLbl: "رقم الاسترداد السري (4 أرقام)",
                avatarStudioTitle: "🎨 تخصيص الصورة الرمزية", avatarTypeLbl: "نوع الصورة", optSteward: "👔 مضيف جوي", optHostess: "👗 مضيفة جوية",
                completeRegBtn: "إتمام التسجيل", backLogin: "لديك حساب بالفعل؟ سجل دخولك",
                resetTitle: "إعادة تعيين رقم الاسترداد", resetSub: "أدخل هاتفك ورقم الاسترداد السري الخاص بك.", resetNewLbl: "كلمة المرور الجديدة",
                updateCredBtn: "تحديث بيانات الاعتماد", backLogin2: "العودة لتسجيل الدخول",
                tileY1: "مسار السنة الأولى (100 نقطة)", tileY2: "مسار السنة الثانية (100 نقطة)", tileEng: "اللغة الإنجليزية للطيران وإيكاو",
                tileStudy: "استوديو الدروس والاختبارات", tileSocial: "الأصدقاء والمحادثة الخاصة والمجموعات",
                centerTitle: "مركز تدريب الطيران الاحترافي EASA", centerDesc: "اختر مسار التعلم لعرض الخريطة المتعرجة مع أسئلة عشوائية مضادة للغش.",
                hubBtn: "← الرئيسية", logoutBtn: "تسجيل الخروج 🚪",
                modalAvatarTitle: "🎨 تعديل الرمزية", modalGenderLbl: "الجنس / النمط", saveAvatarBtn: "حفظ 💾",
                settingsTitle: "⚙️ إعدادات الأكاديمية", langLbl: "لغة الواجهة", passChangeLbl: "تغيير كلمة المرور", updatePassBtn: "تحديث كلمة المرور 🔒",
                myUsernameLbl: "اسم المستخدم الخاص بي"
            }
        };

        window.onload = async function() {
            setLanguage(activeLang);
            toggleTeacherCodeContainer();
            if(sessionUser && sessionUser.phone_number) {
                try {
                    const res = await fetch('/api/user/refresh?phone_number=' + encodeURIComponent(sessionUser.phone_number));
                    const data = await res.json();
                    if(res.ok && data.user) {
                        sessionUser = data.user;
                        localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                    }
                } catch(e) {}
            }

            if(sessionUser) {
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchGroupData();
            } else {
                navigateTo('screen-login');
            }
        };

        function setLanguage(lang) {
            playSound('click');
            activeLang = lang;
            localStorage.setItem('aero_lang', lang);
            const root = document.getElementById('html-root');
            if(lang === 'ar') root.setAttribute('dir', 'rtl');
            else root.setAttribute('dir', 'ltr');
            
            const t = dict[lang];
            if(t) {
                document.getElementById('brand-logo-text').innerText = t.brand;
                document.getElementById('tr-login-title').innerText = t.loginTitle;
                document.getElementById('tr-login-sub').innerText = t.loginSub;
                document.getElementById('tr-lbl-phone').innerText = t.phoneLbl;
                document.getElementById('tr-lbl-pass').innerText = t.passLbl;
                document.getElementById('tr-login-btn').innerText = t.loginBtn;
                document.getElementById('tr-nav-reg').innerText = t.regNav;
                document.getElementById('tr-nav-reset').innerText = t.resetNav;

                document.getElementById('tr-reg-title').innerText = t.regTitle;
                document.getElementById('tr-reg-sub').innerText = t.regSub;
                document.getElementById('tr-reg-role-lbl').innerText = t.regRoleLbl;
                document.getElementById('tr-opt-cadet').innerText = t.optCadet;
                document.getElementById('tr-opt-teacher').innerText = t.optTeacher;
                document.getElementById('tr-reg-name-lbl').innerText = t.regNameLbl;
                document.getElementById('tr-reg-user-lbl').innerText = t.regUserLbl;
                document.getElementById('tr-reg-phone-lbl').innerText = t.phoneLbl;
                document.getElementById('tr-reg-pass-lbl').innerText = t.passLbl;
                document.getElementById('tr-reg-pin-lbl').innerText = t.regPinLbl;
                document.getElementById('tr-avatar-studio-title').innerText = t.avatarStudioTitle;
                document.getElementById('tr-avatar-type-lbl').innerText = t.avatarTypeLbl;
                document.getElementById('tr-opt-steward').innerText = t.optSteward;
                document.getElementById('tr-opt-hostess').innerText = t.optHostess;
                document.getElementById('tr-complete-reg-btn').innerText = t.completeRegBtn;
                document.getElementById('tr-back-login').innerText = t.backLogin;

                document.getElementById('tr-reset-title').innerText = t.resetTitle;
                document.getElementById('tr-reset-sub').innerText = t.resetSub;
                document.getElementById('tr-reset-phone-lbl').innerText = t.phoneLbl;
                document.getElementById('tr-reset-pin-lbl').innerText = t.regPinLbl;
                document.getElementById('tr-reset-new-lbl').innerText = t.resetNewLbl;
                document.getElementById('tr-update-cred-btn').innerText = t.updateCredBtn;
                document.getElementById('tr-back-login2').innerText = t.backLogin2;

                document.getElementById('tr-tile-y1').innerText = t.tileY1;
                document.getElementById('tr-tile-y2').innerText = t.tileY2;
                document.getElementById('tr-tile-eng').innerText = t.tileEng;
                document.getElementById('tr-tile-study').innerText = t.tileStudy;
                document.getElementById('tr-tile-social').innerText = t.tileSocial;
                document.getElementById('tr-center-title').innerText = t.centerTitle;
                document.getElementById('tr-center-desc').innerHTML = t.centerDesc;
                document.getElementById('tr-hub-btn').innerText = t.hubBtn;
                document.getElementById('tr-logout-btn').innerText = t.logoutBtn;

                document.getElementById('tr-modal-avatar-title').innerText = t.modalAvatarTitle;
                document.getElementById('tr-modal-gender-lbl').innerText = t.modalGenderLbl;
                document.getElementById('tr-save-avatar-btn').innerText = t.saveAvatarBtn;

                document.getElementById('tr-settings-title').innerText = t.settingsTitle;
                document.getElementById('tr-lang-lbl').innerText = t.langLbl;
                document.getElementById('tr-pass-change-lbl').innerText = t.passChangeLbl;
                document.getElementById('tr-update-pass-btn').innerText = t.updatePassBtn;
                document.getElementById('tr-my-username-lbl').innerText = t.myUsernameLbl;
                if(sessionUser) document.getElementById('settings-my-username').innerText = '@' + sessionUser.username;
            }
        }

        function showToast(text, isError = false) {
            playSound(isError ? 'error' : 'success');
            const t = document.getElementById('toast');
            t.innerText = text;
            t.style.background = isError ? 'var(--danger)' : 'var(--success)';
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3500);
        }

        function navigateTo(id) {
            playSound('click');
            if(dmPollingInterval) clearInterval(dmPollingInterval);
            if(groupMsgPollingInterval) clearInterval(groupMsgPollingInterval);
            if(questionTimerInterval) clearInterval(questionTimerInterval);
            ['screen-login', 'screen-register', 'screen-reset', 'screen-dashboard'].forEach(s => {
                const el = document.getElementById(s);
                if(el) el.classList.add('hidden');
            });
            const target = document.getElementById(id);
            if(target) target.classList.remove('hidden');
            const headerIcons = document.getElementById('dash-header-icons');
            const langBar = document.getElementById('prelogin-lang-bar');
            if(headerIcons && langBar) {
                if(id === 'screen-dashboard') {
                    headerIcons.classList.remove('hidden');
                    langBar.classList.add('hidden');
                } else {
                    headerIcons.classList.add('hidden');
                    langBar.classList.remove('hidden');
                }
            }
        }

        function toggleTeacherCodeContainer() {
            const roleEl = document.getElementById('reg-role');
            const box = document.getElementById('teacher-code-box');
            if(!roleEl || !box) return;
            if(roleEl.value === 'teacher') {
                box.classList.remove('hidden');
            } else {
                box.classList.add('hidden');
                document.getElementById('reg-teacher-code').value = '';
            }
        }

        function updateRegAvatarPreview() {
            playSound('click');
            const gender = document.getElementById('reg-gender').value;
            document.getElementById('reg-avatar-preview').innerText = gender === 'hostess' ? '👗' : '🧯';
        }
        function updateModalAvatarPreview() {
            playSound('click');
            const gender = document.getElementById('mod-gender').value;
            document.getElementById('modal-avatar-preview').innerText = gender === 'hostess' ? '👗' : '🧯';
        }

        async function submitRegister() {
            playSound('click');
            const full_name = document.getElementById('reg-name').value.trim();
            const username = document.getElementById('reg-username').value.trim().replace('@','');
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();
            const role = document.getElementById('reg-role').value;
            const teacher_code = document.getElementById('reg-teacher-code').value.trim();
            const avatar_gender = document.getElementById('reg-gender').value;
            const group_code = '7842';

            if(!full_name || !username || !phone_number || !password || !recovery_pin) { showToast('Complete all fields', true); return; }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ full_name, username, phone_number, password, recovery_pin, role, teacher_code, avatar_gender, group_code })
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
            playSound('click');
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
                localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
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
            
            const streakVal = sessionUser.streak || 0;
            const streakBadge = document.getElementById('dash-streak-badge');
            const streakNumEl = document.getElementById('dash-streak');
            
            const todayStr = new Date().toISOString().split('T')[0];
            const lastPrac = sessionUser.last_practice_date;
            
            if(lastPrac && lastPrac < todayStr && streakVal > 0) {
                streakBadge.style.color = 'var(--accent)';
                streakNumEl.innerText = `${streakVal} 🧊`;
            } else {
                streakBadge.style.color = 'var(--success)';
                streakNumEl.innerText = `${streakVal} 🔥`;
            }

            const roleText = sessionUser.role === 'teacher' ? 'Instructor / Teacher (Code: ' + sessionUser.group_code + ')' : 'Cadet / Student';
            document.getElementById('dash-role-badge').innerText = roleText;
            document.getElementById('settings-my-username').innerText = '@' + sessionUser.username;
        }

        function logoutUser() {
            playSound('click');
            localStorage.removeItem('aero_crew_user_pro22');
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
            playSound('click');
            if(questionTimerInterval) clearInterval(questionTimerInterval);
            const t = dict[activeLang];
            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">${t.centerTitle}</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">${t.centerDesc}</p>
            `;
        }

        /* HEART RECOVERY LOUNGE */
        function openHeartRecoveryLounge() {
            playSound('click');
            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                    <h3 style="font-size:1.1rem; color:var(--danger); font-weight:900;">❤ Heart Recovery Lounge</h3>
                    <button class="btn-action" onclick="resetToMenu()" style="width:70px; padding:4px; font-size:0.75rem; margin-top:0;">Back</button>
                </div>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.2rem;">You currently have <b>${sessionUser.hearts}/5 hearts</b>. Refill your hearts instantly using XP stars so you can continue your flight training.</p>
                
                <div style="background:var(--bg-deep); padding:1.2rem; border-radius:16px; border:1px solid var(--border-glow); text-align:center; margin-bottom:1rem;">
                    <div style="font-size:2.2rem; margin-bottom:6px;">⭐</div>
                    <h4 style="color:var(--warning); font-size:1rem; margin-bottom:4px;">Refill 5 Hearts (Cost: 50 XP Stars)</h4>
                    <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:1rem;">Your Balance: ${sessionUser.xp_points} XP Stars</p>
                    <button class="btn-action" onclick="refillHeartsWithXP()" style="background:var(--success); color:white;">Refill Hearts Now ⚡</button>
                </div>
            `;
        }

        async function refillHeartsWithXP() {
            playSound('click');
            const res = await fetch('/api/user/refill-hearts', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast('Hearts fully restored to 5! ❤️');
                resetToMenu();
            } else {
                showToast(data.detail || 'Refill failed', true);
            }
        }

        /* MASTER RANDOMIZED QUESTION POOLS (TRUE ANTI-CHEAT SHUFFLE) */
        const masterQuestionPools = {
            english: [
                { q: "How is letter 'A' pronounced in ICAO standard telephony?", options: ["Alpha", "Apple", "Adam"], correct: 0 },
                { q: "What is the correct ICAO pronunciation for number '9'?", options: ["Niner", "Nine", "Nov"], correct: 0 },
                { q: "Which phonetic word represents letter 'S'?", options: ["Sierra", "Sugar", "Sam"], correct: 0 },
                { q: "What is the primary phrase for seatbelt compliance check?", options: ["Cabin crew, secure cabin for takeoff", "Please fasten belts", "Fasten seatbelts please"], correct: 0 },
                { q: "During turbulence, what command is issued to cabin crew?", options: ["Crew, be seated and secure", "Continue service", "Stand by galley"], correct: 0 },
                { q: "How do you announce emergency slide arming?", options: ["Cabin crew, arm slides and cross-check", "Open all doors", "Disarm doors"], correct: 0 },
                { q: "What command is shouted during rapid land evacuation?", options: ["EFP, LEAVE BAGS, DOWN THE SLIDE!", "Please exit slowly", "Grab your luggage and jump"], correct: 0 },
                { q: "What urgent prefix is used for non-immediate safety urgency?", options: ["PAN-PAN", "MAYDAY", "SECURITY"], correct: 0 },
                { q: "How many times is MAYDAY repeated in distress calls?", options: ["Three times", "Once", "Five times"], correct: 0 },
                { q: "What term describes sudden severe vertical air movement?", options: ["Wind shear / Turbulence", "Gentle breeze", "Thermal calm"], correct: 0 },
                { q: "What is the weather report acronym provided to pilots?", options: ["METAR", "RADAR", "SONAR"], correct: 0 },
                { q: "What condition requires anti-icing fluid application?", options: ["Freezing fog and frost", "Sunny skies", "High humidity"], correct: 0 }
            ],
            year1: [
                { q: "What is the mandatory crew action prior to door arming?", options: ["Arm cross-check and report", "Open emergency exit", "Deplane passengers"], correct: 0 },
                { q: "In case of cabin depressurization, what is your immediate action?", options: ["Secure oxygen mask and be seated", "Serve beverages", "Call flight deck"], correct: 0 },
                { q: "Who gives the final authorization for aircraft pushback?", options: ["Captain / Flight Deck", "Passenger", "Baggage loader"], correct: 0 },
                { q: "What safety equipment is required during firefighting in cabin?", options: ["Smoke goggles & PBE (Smoke Hood)", "Sunglasses", "Surgical mask"], correct: 0 },
                { q: "What is the pre-flight briefing acronym for crew coordination?", options: ["SEP / Briefing", "GPS", "FMS"], correct: 0 },
                { q: "Where are life vests typically stowed for passengers?", options: ["Underneath or beside passenger seats", "In overhead bins", "In the cockpit"], correct: 0 },
                { q: "What color is the emergency evacuation slide inflation cylinder pressure gauge indicator?", options: ["Green / Operating range", "Red only", "Black"], correct: 0 },
                { q: "Which department oversees airline crew regulatory compliance in Europe?", options: ["EASA", "NASA", "FIFA"], correct: 0 }
            ],
            year2: [
                { q: "What is CRM in aviation crew training?", options: ["Crew Resource Management", "Cabin Routine Maintenance", "Cockpit Radio Monitoring"], correct: 0 },
                { q: "What is the minimum crew rest requirement during long-haul duty rotations?", options: ["Mandatory scheduled rest period", "No rest required", "Optional coffee break"], correct: 0 },
                { q: "What does emergency transponder squawk code 7700 signify?", options: ["Emergency / Distress", "Hijacking", "Radio failure"], correct: 0 },
                { q: "How should dangerous goods (DG) spills in cabin be handled?", options: ["Isolate area, use spill kit, notify captain", "Wash down galley drain", "Ignore until landing"], correct: 0 },
                { q: "What is the procedure for suspected bomb threat inflight?", options: ["Search LRT (Least Risk Bomb Location), notify flight deck", "Open emergency door", "Announce publicly to passengers"], correct: 0 }
            ]
        };

        function getRandomQuizQuestions(poolKey, count = 3) {
            const pool = [...(masterQuestionPools[poolKey] || masterQuestionPools['year1'])];
            for (let i = pool.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [pool[i], pool[j]] = [pool[j], pool[i]];
            }
            const selected = pool.slice(0, Math.min(count, pool.length));
            return selected.map(item => {
                let opts = [...item.options];
                let correctText = opts[item.correct];
                for (let i = opts.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [opts[i], opts[j]] = [opts[j], opts[i]];
                }
                const newCorrectIdx = opts.indexOf(correctText);
                return { q: item.q, options: opts, correct: newCorrectIdx };
            });
        }

        /* AVIATION ENGLISH ROADMAP */
        function launchAviationEnglishRoadmap() {
            playSound('click');
            const box = document.getElementById('simulation-box');
            const completedList = sessionUser.completed_nodes || [];

            let activeIndex = 1;
            for(let i = 1; i <= 100; i++) {
                if(completedList.includes(`eng_node_${i}`)) activeIndex = i + 1;
            }
            if(activeIndex > 100) activeIndex = 100;

            let nodesHtml = '';
            for(let i = 1; i <= 100; i++) {
                const nodeId = `eng_node_${i}`;
                const isCompleted = completedList.includes(nodeId);
                let statusClass = 'locked';
                if(isCompleted) statusClass = 'completed';
                else if(i === 1 || completedList.includes(`eng_node_${i-1}`)) statusClass = 'active';

                const icon = isCompleted ? '👑' : (statusClass === 'active' ? '🌐' : '🔒');
                const isCurrentActive = (i === activeIndex);
                
                let companionEmoji = '🧯';
                if(sessionUser.active_skin === 'Portable Oxygen Bottle') companionEmoji = '💨';
                else if(sessionUser.active_skin === 'Emergency Megaphone') companionEmoji = '📢';
                else if(sessionUser.active_skin === 'Cabin Flashlight') companionEmoji = '🔦';
                else if(sessionUser.active_skin === 'Inflatable Life Vest') companionEmoji = '🦺';
                else if(sessionUser.active_skin === 'Slide-Raft Unit') companionEmoji = '🛟';
                else if(sessionUser.active_skin === 'Smoke Hood PBE') companionEmoji = '🪖';
                else if(sessionUser.active_skin === 'Emergency Medical Kit') companionEmoji = '🩺';
                else if(sessionUser.avatar_gender === 'hostess') companionEmoji = '👗';

                nodesHtml += `
                    <div class="duo-node-wrapper">
                        ${isCurrentActive ? `<div class="companion-hopper">${companionEmoji}</div>` : ''}
                        <div class="duo-node ${statusClass}" onclick="startDynamicNodeSession('english', ${i}, '${statusClass}')">
                            <span style="font-size:1.3rem;">${icon}</span>
                            <span style="font-size:0.55rem; margin-top:-2px;">${i}</span>
                        </div>
                    </div>
                `;
            }

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">🌐 Aviation English & ICAO Mastery Path</h3>
                    <span style="font-size: 0.72rem; color: var(--success); font-weight: 800;">Equipment: ${sessionUser.active_skin}</span>
                </div>
                <div class="duo-path-container path-backdrop-eng">
                    <div style="display:flex; flex-direction:column; gap:24px; width:100%;">
                        ${nodesHtml}
                    </div>
                </div>
            `;
        }

        function startDynamicNodeSession(poolKey, nodeNum, status) {
            playSound('click');
            if(status === 'locked') { showToast('Complete previous checkpoints first!', true); return; }
            if(sessionUser.hearts <= 0) {
                openHeartRecoveryLounge();
                return;
            }
            const randomizedQuestions = getRandomQuizQuestions(poolKey, 3);
            renderDynamicStep(poolKey, nodeNum, randomizedQuestions, 0);
        }

        function renderDynamicStep(poolKey, nodeNum, questions, stepIdx) {
            if(questionTimerInterval) clearInterval(questionTimerInterval);
            if(stepIdx >= questions.length) {
                completeDynamicNode(poolKey, nodeNum);
                return;
            }
            const qObj = questions[stepIdx];
            const box = document.getElementById('simulation-box');
            let timeLeft = 35;

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <span style="font-size: 0.75rem; color: var(--gold); font-weight: 900;">NODE ${nodeNum} • QUESTION ${stepIdx+1} OF ${questions.length}</span>
                    <span id="dyn-timer" style="font-size:0.8rem; color:var(--danger); font-weight:800;">⏱️ 35s</span>
                </div>
                <div style="background:var(--bg-deep); padding:1.2rem; border-radius:16px; border:1px solid var(--border-glow); margin-bottom:1rem;">
                    <b style="color:white; font-size:0.95rem; display:block; margin-bottom:12px;">${qObj.q}</b>
                    <div style="display:flex; flex-direction:column; gap:8px;">
                        ${qObj.options.map((opt, idx) => `
                            <button class="btn-action" onclick="verifyDynamicAnswer('${poolKey}', ${nodeNum}, ${idx === qObj.correct}, ${stepIdx}, ${JSON.stringify(questions).replace(/"/g, '&quot;')})" style="background:var(--bg-deep); color:white; border:1px solid var(--border-glow); padding:11px; font-size:0.85rem; text-align:left; margin-top:0;">${String.fromCharCode(65+idx)}) ${opt}</button>
                        `).join('')}
                    </div>
                </div>
                <div id="dyn-feedback" style="text-align:center; font-weight:800; font-size:0.85rem;"></div>
            `;

            questionTimerInterval = setInterval(async () => {
                timeLeft--;
                const timerEl = document.getElementById('dyn-timer');
                if(timerEl) timerEl.innerText = `⏱️ ${timeLeft}s`;
                if(timeLeft <= 0) {
                    clearInterval(questionTimerInterval);
                    showToast('Time expired! Heart lost ❤️-1', true);
                    const nodeId = poolKey === 'english' ? `eng_node_${nodeNum}` : `${poolKey}_node_${nodeNum}`;
                    const res = await fetch('/api/node/complete', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ phone_number: sessionUser.phone_number, node_id: nodeId, lost_heart: true })
                    });
                    const data = await res.json();
                    sessionUser.hearts = data.hearts;
                    localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                    updateDashboardUI();
                    if(sessionUser.hearts <= 0) openHeartRecoveryLounge();
                    else renderDynamicStep(poolKey, nodeNum, questions, stepIdx);
                }
            }, 1000);
        }

        async function verifyDynamicAnswer(poolKey, nodeNum, isCorrect, stepIdx, questionsJson) {
            if(questionTimerInterval) clearInterval(questionTimerInterval);
            const fb = document.getElementById('dyn-feedback');
            const questions = typeof questionsJson === 'string' ? JSON.parse(questionsJson.replace(/&quot;/g, '"')) : questionsJson;
            const nodeId = poolKey === 'english' ? `eng_node_${nodeNum}` : `${poolKey}_node_${nodeNum}`;

            if(isCorrect) {
                fb.style.color = 'var(--success)';
                fb.innerText = 'Correct procedure!';
                setTimeout(() => {
                    renderDynamicStep(poolKey, nodeNum, questions, stepIdx + 1);
                }, 900);
            } else {
                fb.style.color = 'var(--danger)';
                fb.innerText = 'Incorrect! Heart lost ❤️-1';
                const res = await fetch('/api/node/complete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: sessionUser.phone_number, node_id: nodeId, lost_heart: true })
                });
                const data = await res.json();
                sessionUser.hearts = data.hearts;
                localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                updateDashboardUI();
                if(sessionUser.hearts <= 0) openHeartRecoveryLounge();
            }
        }

        async function completeDynamicNode(poolKey, nodeNum) {
            const nodeId = poolKey === 'english' ? `eng_node_${nodeNum}` : `${poolKey}_node_${nodeNum}`;
            const res = await fetch('/api/node/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, node_id: nodeId, lost_heart: false })
            });
            const data = await res.json();
            sessionUser.completed_nodes = data.completed_nodes;
            sessionUser.xp_points = data.xp;
            sessionUser.hearts = data.hearts;
            sessionUser.streak = data.streak;
            localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
            updateDashboardUI();

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="text-align:center; padding: 2rem 0;">
                    <div style="font-size: 3.5rem; margin-bottom: 1rem;">👑</div>
                    <h3 style="font-size: 1.3rem; color: var(--gold); font-weight: 900; margin-bottom: 0.5rem;">Node Completed!</h3>
                    <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1.5rem;">You earned <b>+30 XP Stars</b> ⭐ and kept your streak alive!</p>
                    <button class="btn-action" onclick="${poolKey === 'english' ? 'launchAviationEnglishRoadmap()' : 'launchRoadmap(\'' + poolKey + '\')'}" style="background:var(--success); color:white;">Continue Journey ✈</button>
                </div>
            `;
        }

        /* ROADMAPS FOR YEAR 1 & YEAR 2 (RANDOMIZED ANTI-CHEAT) */
        function launchRoadmap(yearKey) {
            playSound('click');
            const box = document.getElementById('simulation-box');
            const completedList = sessionUser.completed_nodes || [];
            
            let activeNodeIndex = 1;
            for(let i = 1; i <= 100; i++) {
                if(completedList.includes(`${yearKey}_node_${i}`)) {
                    activeNodeIndex = i + 1;
                }
            }
            if(activeNodeIndex > 100) activeNodeIndex = 100;

            let nodesHtml = '';
            for(let i = 1; i <= 100; i++) {
                const nodeId = `${yearKey}_node_${i}`;
                const isCompleted = completedList.includes(nodeId);
                let statusClass = 'locked';
                if(isCompleted) statusClass = 'completed';
                else if(i === 1 || completedList.includes(`${yearKey}_node_${i-1}`)) statusClass = 'active';

                const icon = isCompleted ? '👑' : (statusClass === 'active' ? '✈' : '🔒');
                const isCurrentActive = (i === activeNodeIndex);
                
                let companionEmoji = '🧯';
                if(sessionUser.active_skin === 'Portable Oxygen Bottle') companionEmoji = '💨';
                else if(sessionUser.active_skin === 'Emergency Megaphone') companionEmoji = '📢';
                else if(sessionUser.active_skin === 'Cabin Flashlight') companionEmoji = '🔦';
                else if(sessionUser.active_skin === 'Inflatable Life Vest') companionEmoji = '🦺';
                else if(sessionUser.active_skin === 'Slide-Raft Unit') companionEmoji = '🛟';
                else if(sessionUser.active_skin === 'Smoke Hood PBE') companionEmoji = '🪖';
                else if(sessionUser.active_skin === 'Emergency Medical Kit') companionEmoji = '🩺';
                else if(sessionUser.avatar_gender === 'hostess') companionEmoji = '👗';

                nodesHtml += `
                    <div class="duo-node-wrapper">
                        ${isCurrentActive ? `<div class="companion-hopper">${companionEmoji}</div>` : ''}
                        <div class="duo-node ${statusClass}" onclick="startDynamicNodeSession('${yearKey}', ${i}, '${statusClass}')">
                            <span style="font-size:1.3rem;">${icon}</span>
                            <span style="font-size:0.55rem; margin-top:-2px;">${i}</span>
                        </div>
                    </div>
                `;
            }

            const backdropClass = yearKey === 'year1' ? 'path-backdrop-y1' : 'path-backdrop-y2';
            const yearDisplayNum = yearKey === 'year1' ? '1' : '2';

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--gold); font-weight: 900;">🏆 Year ${yearDisplayNum} Roadmap (Zig-Zag Path)</h3>
                    <span style="font-size: 0.72rem; color: var(--accent);">Equipment: ${sessionUser.active_skin}</span>
                </div>
                <div class="duo-path-container ${backdropClass}">
                    <div style="display:flex; flex-direction:column; gap:24px; width:100%;">
                        ${nodesHtml}
                    </div>
                </div>
            `;
        }

        /* STUDY & EXAMS STUDIO */
        async function openStudyHub() {
            playSound('click');
            const codeInput = document.getElementById('student-join-code-input');
            const codeToFetch = sessionUser.role === 'teacher' ? sessionUser.group_code : (codeInput ? codeInput.value.trim() : sessionUser.group_code);
            
            const res = await fetch('/api/group/info?group_code=' + codeToFetch);
            groupInfo = await res.json();
            const box = document.getElementById('simulation-box');
            const isTeacher = sessionUser.role === 'teacher';

            let teacherControls = '';
            if(isTeacher) {
                teacherControls = `
                    <div style="background:var(--bg-deep); padding:1rem; border-radius:14px; border:1px solid var(--accent); margin-bottom:1rem;">
                        <h4 style="color:var(--accent); font-size:0.9rem; margin-bottom:0.5rem;">👨‍‍🏫 Instructor Studio (My Code: ${sessionUser.group_code})</h4>
                        
                        <div style="margin-bottom:14px; border-bottom:1px solid var(--border); padding-bottom:10px;">
                            <label><b>Create Quiz</b></label>
                            <input type="text" id="les-title" placeholder="Quiz Title" style="margin-bottom:6px;" />
                            <textarea id="les-notes" placeholder="Instructions" style="height:40px; margin-bottom:6px;"></textarea>
                            <div id="quiz-questions-container" style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
                                <div class="quiz-q-row" style="display:flex; gap:6px;">
                                    <input type="text" placeholder="Question 1" class="qq-text" style="margin-bottom:0; flex:2;" />
                                    <input type="text" placeholder="Correct Answer" class="qq-ans" style="margin-bottom:0; flex:1;" />
                                </div>
                            </div>
                            <button class="btn-action" onclick="addQuizQuestionRow()" style="padding:4px; font-size:0.75rem; background:var(--surface-card); color:var(--accent); margin-top:0; margin-bottom:6px;">+ Add Question</button>
                            <button class="btn-action" onclick="publishLesson()" style="padding:6px; font-size:0.8rem; background:var(--success); color:white; margin-top:0;">Publish Quiz 🚀</button>
                        </div>

                        <div>
                            <label><b>Create Official Exam</b></label>
                            <input type="text" id="ex-title" placeholder="Exam Title" style="margin-bottom:6px;" />
                            <div id="exam-questions-container" style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
                                <div class="exam-q-row" style="display:flex; gap:6px;">
                                    <input type="text" placeholder="Question 1" class="eq-text" style="margin-bottom:0; flex:2;" />
                                    <input type="text" placeholder="Correct Answer" class="eq-ans" style="margin-bottom:0; flex:1;" />
                                </div>
                            </div>
                            <button class="btn-action" onclick="addExamQuestionRow()" style="padding:4px; font-size:0.75rem; background:var(--surface-card); color:var(--accent); margin-top:0; margin-bottom:6px;">+ Add Question</button>
                            <button class="btn-action" onclick="publishExam()" style="padding:6px; font-size:0.8rem; background:var(--warning); color:var(--bg-deep); margin-top:0;">Publish Exam 🏆</button>
                        </div>
                    </div>
                    <div style="margin-bottom:1rem;">
                        <button class="btn-action" onclick="openTeacherAnalytics()" style="padding:8px; font-size:0.85rem; background:var(--gold); color:var(--bg-deep); margin-top:0;">View Student Analytics & Timestamps 📊</button>
                    </div>
                `;
            }

            let studentJoinSection = '';
            if(!isTeacher) {
                studentJoinSection = `
                    <div style="background:var(--bg-deep); padding:0.9rem; border-radius:14px; border:1px solid var(--border-glow); margin-bottom:1rem;">
                        <label><b>Enter Teacher Code (Auto-Loads Quizzes & Exams)</b></label>
                        <input type="text" id="student-join-code-input" placeholder="Enter 4-digit code..." value="${codeToFetch}" maxlength="4" oninput="onStudentCodeInput(this.value)" style="margin-bottom:0;" />
                    </div>
                `;
            }

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">📚 Study & Exams Studio</h3>
                    <span style="font-size: 0.72rem; color: var(--success); font-weight: 800;">Code: ${codeToFetch}</span>
                </div>
                ${studentJoinSection}
                ${teacherControls}
                
                <h4 style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.5rem; text-transform:uppercase;">Official Exams (${groupInfo.exams.length})</h4>
                <div style="max-height:120px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; margin-bottom:1rem; scrollbar-width:none;" id="exams-list">
                    ${groupInfo.exams.length === 0 ? '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center;">No exams found for this code.</div>' :
                      groupInfo.exams.map(e => `
                        <div style="background:var(--bg-deep); padding:10px; border-radius:12px; border:1px solid var(--border-glow); display:flex; justify-content:space-between; align-items:center;">
                            <div><b style="color:white; font-size:0.85rem;">🏆 ${e.title}</b><div style="color:var(--text-muted); font-size:0.7rem;">Teacher: ${e.teacher_username}</div></div>
                            <button class="btn-action" onclick='takeExam(${JSON.stringify(e)})' style="width:90px; padding:6px; font-size:0.75rem; background:var(--warning); color:var(--bg-deep); margin-top:0;">Start ⏱</button>
                        </div>
                    `).join('')}
                </div>

                <h4 style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.5rem; text-transform:uppercase;">Quizzes (${groupInfo.lessons.length})</h4>
                <div style="max-height:120px; overflow-y:auto; display:flex; flex-direction:column; gap:8px; scrollbar-width:none;" id="lessons-list">
                    ${groupInfo.lessons.length === 0 ? '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center;">No quizzes found for this code.</div>' :
                      groupInfo.lessons.map(l => `
                        <div style="background:var(--bg-deep); padding:10px; border-radius:12px; border:1px solid var(--border-glow); display:flex; justify-content:space-between; align-items:center;">
                            <div><b style="color:white; font-size:0.85rem;">📝 ${l.title}</b></div>
                            <button class="btn-action" onclick='takeLessonQuiz(${JSON.stringify(l)})' style="width:90px; padding:6px; font-size:0.75rem; margin-top:0;">Take 📝</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        let codeInputTimer = null;
        function onStudentCodeInput(val) {
            if(codeInputTimer) clearTimeout(codeInputTimer);
            if(val.length === 4) {
                codeInputTimer = setTimeout(() => { openStudyHub(); }, 400);
            }
        }

        function addQuizQuestionRow() {
            playSound('click');
            const container = document.getElementById('quiz-questions-container');
            const row = document.createElement('div');
            row.className = 'quiz-q-row';
            row.style.cssText = 'display:flex; gap:6px; margin-top:4px;';
            row.innerHTML = `<input type="text" placeholder="Another Question" class="qq-text" style="margin-bottom:0; flex:2;" /><input type="text" placeholder="Correct Answer" class="qq-ans" style="margin-bottom:0; flex:1;" />`;
            container.appendChild(row);
        }

        function addExamQuestionRow() {
            playSound('click');
            const container = document.getElementById('exam-questions-container');
            const row = document.createElement('div');
            row.className = 'exam-q-row';
            row.style.cssText = 'display:flex; gap:6px; margin-top:4px;';
            row.innerHTML = `<input type="text" placeholder="Another Question" class="eq-text" style="margin-bottom:0; flex:2;" /><input type="text" placeholder="Correct Answer" class="eq-ans" style="margin-bottom:0; flex:1;" />`;
            container.appendChild(row);
        }

        async function publishLesson() {
            playSound('click');
            const title = document.getElementById('les-title').value.trim();
            const content_html = document.getElementById('les-notes').value.trim();
            if(!title) { showToast('Enter quiz title', true); return; }
            const rows = document.querySelectorAll('.quiz-q-row');
            let quiz_data = [];
            rows.forEach(r => {
                const q = r.querySelector('.qq-text').value.trim();
                const a = r.querySelector('.qq-ans').value.trim();
                if(q && a) quiz_data.push({ question: q, correct: a });
            });
            if(quiz_data.length === 0) { showToast('Add at least one question', true); return; }
            const res = await fetch('/api/lesson/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_code: sessionUser.group_code, teacher_username: sessionUser.username, title, content_html, quiz_data })
            });
            if(res.ok) { showToast('Quiz published!'); openStudyHub(); }
        }

        async function publishExam() {
            playSound('click');
            const title = document.getElementById('ex-title').value.trim();
            if(!title) { showToast('Enter exam title', true); return; }
            const rows = document.querySelectorAll('.exam-q-row');
            let exam_data = [];
            rows.forEach(r => {
                const q = r.querySelector('.eq-text').value.trim();
                const a = r.querySelector('.eq-ans').value.trim();
                if(q && a) exam_data.push({ question: q, correct: a });
            });
            if(exam_data.length === 0) { showToast('Add at least one question', true); return; }
            const res = await fetch('/api/exam/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_code: sessionUser.group_code, teacher_username: sessionUser.username, title, exam_data })
            });
            if(res.ok) { showToast('Exam published!'); openStudyHub(); }
        }

        async function openTeacherAnalytics() {
            playSound('click');
            const res = await fetch('/api/teacher/analytics?group_code=' + sessionUser.group_code);
            const data = await res.json();
            const box = document.getElementById('simulation-box');

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                    <h3 style="font-size:1.05rem; color:var(--gold); font-weight:900;">📊 Student Submissions & Timestamps</h3>
                    <button class="btn-action" onclick="openStudyHub()" style="width:70px; padding:6px; font-size:0.75rem; margin-top:0;">Back</button>
                </div>
                <h4 style="font-size:0.8rem; color:var(--accent); margin-bottom:0.4rem;">Official Exam Submissions</h4>
                <div style="max-height:110px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; margin-bottom:10px; scrollbar-width:none;">
                    ${data.exam_submissions.length === 0 ? '<div style="color:var(--text-muted); font-size:0.75rem;">No exam attempts yet.</div>' :
                      data.exam_submissions.map(s => `
                        <div style="background:var(--bg-deep); padding:8px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; font-size:0.8rem;">
                            <div><b>${s.student_name} (@${s.student_username})</b><div style="color:var(--text-muted); font-size:0.68rem;">Exam: ${s.exam_title} • Duration: ${s.time_spent_seconds}s • Finished: ${new Date(s.submitted_at).toLocaleString()}</div></div>
                            <div style="color:var(--success); font-weight:800;">${s.score}/${s.total_questions}</div>
                        </div>
                    `).join('')}
                </div>
                <h4 style="font-size:0.8rem; color:var(--accent); margin-bottom:0.4rem;">Quiz Submissions</h4>
                <div style="max-height:110px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; scrollbar-width:none;">
                    ${data.quiz_results.length === 0 ? '<div style="color:var(--text-muted); font-size:0.75rem;">No quiz attempts yet.</div>' :
                      data.quiz_results.map(r => `
                        <div style="background:var(--bg-deep); padding:8px; border-radius:10px; display:flex; justify-content:space-between; align-items:center; font-size:0.8rem;">
                            <div><b>${r.student_name}</b><div style="color:var(--text-muted); font-size:0.68rem;">Quiz: ${r.lesson_title} • Completed: ${new Date(r.completed_at).toLocaleString()}</div></div>
                            <div style="color:var(--success); font-weight:800;">${r.score}/${r.total_questions}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        let currentExamTimer = null;
        let examStartTime = 0;

        function takeExam(exam) {
            playSound('click');
            let questions = exam.exam_data;
            if(typeof questions === 'string') questions = JSON.parse(questions);
            examStartTime = Date.now();

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <h3 style="font-size:1.05rem; color:var(--warning); font-weight:900;">⏱️ ${exam.title}</h3>
                    <span id="exam-timer" style="color:var(--danger); font-weight:800; font-size:0.85rem;">Time: 0s</span>
                </div>
                <div style="max-height:220px; overflow-y:auto; display:flex; flex-direction:column; gap:12px; margin-bottom:1rem; scrollbar-width:none;">
                    ${questions.map((q, idx) => `
                        <div style="background:var(--bg-deep); padding:10px; border-radius:12px;">
                            <label style="color:white; font-size:0.85rem;">Q${idx+1}: ${q.question}</label>
                            <input type="text" class="exam-answer-input" data-correct="${q.correct}" placeholder="Your answer..." style="margin-bottom:0;" />
                        </div>
                    `).join('')}
                </div>
                <button class="btn-action" onclick="submitActiveExam(${exam.id}, ${questions.length})" style="background:var(--success); color:white;">Submit Official Exam 🏆</button>
            `;

            currentExamTimer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - examStartTime) / 1000);
                const timerEl = document.getElementById('exam-timer');
                if(timerEl) timerEl.innerText = `Time: ${elapsed}s`;
            }, 1000);
        }

        async function submitActiveExam(examId, totalQ) {
            if(currentExamTimer) clearInterval(currentExamTimer);
            const timeSpent = Math.floor((Date.now() - examStartTime) / 1000);
            const inputs = document.querySelectorAll('.exam-answer-input');
            let score = 0;
            inputs.forEach(inp => {
                if(inp.value.trim().toLowerCase() === inp.getAttribute('data-correct').trim().toLowerCase()) score++;
            });

            const res = await fetch('/api/exam/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ exam_id: examId, student_username: sessionUser.username, student_name: sessionUser.full_name, score, total_questions: totalQ, time_spent_seconds: timeSpent })
            });
            if(res.ok) {
                showToast(`Exam submitted! Score: ${score}/${totalQ} in ${timeSpent}s. +100 XP ⭐`);
                openStudyHub();
            }
        }

        function takeLessonQuiz(lesson) {
            playSound('click');
            let questions = lesson.quiz_data;
            if(typeof questions === 'string') questions = JSON.parse(questions);

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900; margin-bottom:0.5rem;">📝 ${lesson.title}</h3>
                <div style="background:var(--bg-deep); padding:10px; border-radius:10px; font-size:0.8rem; color:var(--text-muted); margin-bottom:1rem;">${lesson.content_html}</div>
                <div style="max-height:200px; overflow-y:auto; display:flex; flex-direction:column; gap:10px; margin-bottom:1rem; scrollbar-width:none;" id="quiz-questions-form">
                    ${questions.map((q, idx) => `
                        <div style="background:var(--bg-deep); padding:10px; border-radius:12px;">
                            <label style="color:white; font-size:0.85rem;">Q${idx+1}: ${q.question}</label>
                            <input type="text" class="quiz-answer-input" data-correct="${q.correct}" placeholder="Your answer..." style="margin-bottom:0;" />
                        </div>
                    `).join('')}
                </div>
                <button class="btn-action" onclick="submitMultiQuiz(${lesson.id}, ${questions.length})" style="background:var(--success); color:white;">Submit Quiz 🎯</button>
            `;
        }

        async function submitMultiQuiz(lessonId, totalQ) {
            const inputs = document.querySelectorAll('.quiz-answer-input');
            let score = 0;
            inputs.forEach(inp => {
                if(inp.value.trim().toLowerCase() === inp.getAttribute('data-correct').trim().toLowerCase()) score++;
            });

            const res = await fetch('/api/quiz/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ lesson_id: lessonId, student_username: sessionUser.username, student_name: sessionUser.full_name, score, total_questions: totalQ })
            });
            if(res.ok) {
                showToast(`Quiz completed! Score: ${score}/${totalQ}. +50 XP ⭐`);
                openStudyHub();
            }
        }

        /* FRIENDS & SOCIAL HUB */
        async function openSocialHub() {
            playSound('click');
            const res = await fetch('/api/friends/list?username=' + sessionUser.username);
            socialData = await res.json();
            const box = document.getElementById('simulation-box');

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">💬 Friends & Social Hub</h3>
                    <span style="font-size: 0.72rem; color: var(--success); font-weight: 800;">Social Network</span>
                </div>
                
                <div style="background:var(--bg-deep); padding:0.9rem; border-radius:14px; border:1px solid var(--border-glow); margin-bottom:1rem;">
                    <label><b>Add Friend by Username</b></label>
                    <div style="display:flex; gap:8px;">
                        <input type="text" id="friend-target-user" placeholder="@username" style="margin-bottom:0; flex:1;" />
                        <button class="btn-action" onclick="sendFriendReq()" style="width:100px; margin-top:0; padding:10px; font-size:0.8rem;">Add Friend ➕</button>
                    </div>
                </div>

                ${socialData.incoming_requests.length > 0 ? `
                    <h4 style="font-size:0.8rem; color:var(--warning); margin-bottom:0.4rem;">Incoming Friend Requests</h4>
                    <div style="display:flex; flex-direction:column; gap:6px; margin-bottom:1rem;">
                        ${socialData.incoming_requests.map(req => `
                            <div style="background:var(--bg-deep); padding:8px 12px; border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:0.85rem; color:white;"><b>@${req.sender_username}</b> sent you a request</span>
                                <button class="btn-action" onclick="acceptFriend('${req.sender_username}')" style="width:80px; padding:6px; font-size:0.75rem; background:var(--success); color:white; margin-top:0;">Accept</button>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                    <h4 style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">My Friends (${socialData.friends.length})</h4>
                    <button class="btn-action" onclick="openCreateFriendGroup()" style="width:130px; padding:4px; font-size:0.75rem; background:var(--warning); color:var(--bg-deep); margin-top:0;">+ Create Friend Group</button>
                </div>
                <div style="max-height:110px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; margin-bottom:1rem; scrollbar-width:none;" id="friends-list-box">
                    ${socialData.friends.length === 0 ? '<div style="color:var(--text-muted); font-size:0.75rem; text-align:center;">No friends added yet.</div>' :
                      socialData.friends.map(f => `
                        <div style="background:var(--bg-deep); padding:8px 12px; border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
                            <div><b style="color:white; font-size:0.85rem;">${f.full_name}</b> <span style="color:var(--text-muted); font-size:0.75rem;">(@${f.username})</span></div>
                            <button class="btn-action" onclick="openDirectChat('${f.username}', '${f.full_name}')" style="width:90px; padding:6px; font-size:0.75rem; margin-top:0;">Chat 💬</button>
                        </div>
                    `).join('')}
                </div>

                <h4 style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:0.4rem;">My Friend Groups (${socialData.friend_groups.length})</h4>
                <div style="max-height:110px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; scrollbar-width:none;" id="friend-groups-box">
                    ${socialData.friend_groups.length === 0 ? '<div style="color:var(--text-muted); font-size:0.75rem; text-align:center;">No friend groups created yet.</div>' :
                      socialData.friend_groups.map(g => `
                        <div style="background:var(--bg-deep); padding:8px 12px; border-radius:10px; display:flex; justify-content:space-between; align-items:center;">
                            <div><b style="color:white; font-size:0.85rem;">👥 ${g.group_name}</b> <span style="color:var(--text-muted); font-size:0.7rem;">(No code required)</span></div>
                            <button class="btn-action" onclick="openFriendGroupChat(${g.id}, '${g.group_name}')" style="width:90px; padding:6px; font-size:0.75rem; margin-top:0; background:var(--accent); color:var(--bg-deep);">Open Group</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function sendFriendReq() {
            playSound('click');
            const receiver = document.getElementById('friend-target-user').value.trim().replace('@','');
            if(!receiver) return;
            const res = await fetch('/api/friends/request', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sender_username: sessionUser.username, receiver_username: receiver })
            });
            if(res.ok) {
                showToast('Friend request sent!');
                openSocialHub();
            } else {
                showToast('User not found', true);
            }
        }

        async function acceptFriend(friendUser) {
            playSound('click');
            const res = await fetch('/api/friends/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username: sessionUser.username, friend_username: friendUser })
            });
            if(res.ok) {
                showToast('Friend request accepted!');
                openSocialHub();
            }
        }

        function openCreateFriendGroup() {
            playSound('click');
            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                    <h3 style="font-size:1.05rem; color:var(--warning); font-weight:900;">👥 Create Friend Group</h3>
                    <button class="btn-action" onclick="openSocialHub()" style="width:70px; padding:6px; font-size:0.75rem; margin-top:0;">Back</button>
                </div>
                <label>Group Name</label>
                <input type="text" id="fg-name" placeholder="e.g. Flight Cadets Study" />
                <label>Select Friends to Include</label>
                <div style="max-height:140px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; margin-bottom:1rem; scrollbar-width:none;" id="fg-members-list">
                    ${socialData.friends.map(f => `
                        <label style="font-size:0.85rem; color:white; display:flex; align-items:center; gap:8px; text-transform:none;">
                            <input type="checkbox" value="${f.username}" class="fg-member-checkbox" style="width:auto; margin-bottom:0;" /> ${f.full_name} (@${f.username})
                        </label>
                    `).join('')}
                </div>
                <button class="btn-action" onclick="submitCreateFriendGroup()" style="background:var(--success); color:white;">Create Group 🚀</button>
            `;
        }

        async function submitCreateFriendGroup() {
            playSound('click');
            const group_name = document.getElementById('fg-name').value.trim();
            const checkboxes = document.querySelectorAll('.fg-member-checkbox:checked');
            let members = [sessionUser.username];
            checkboxes.forEach(cb => members.push(cb.value));
            if(!group_name) { showToast('Enter group name', true); return; }

            const res = await fetch('/api/friend-groups/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_name, creator_username: sessionUser.username, members })
            });
            if(res.ok) {
                showToast('Friend group created successfully!');
                openSocialHub();
            }
        }

        let activeChatFriendUser = null;
        let activeChatFriendName = '';

        async function openDirectChat(friendUsername, friendFullName) {
            playSound('click');
            activeChatFriendUser = friendUsername;
            activeChatFriendName = friendFullName;
            const box = document.getElementById('simulation-box');

            async function fetchAndRenderMessages() {
                const res = await fetch(`/api/direct-messages/list?user1=${sessionUser.username}&user2=${friendUsername}`);
                const data = await res.json();
                const msgs = data.messages || [];
                const stream = document.getElementById('chat-msg-stream');
                if(stream) {
                    stream.innerHTML = msgs.map(m => {
                        let contentHtml = m.content;
                        if(m.content.startsWith('blob:') || m.content.startsWith('http') || m.content.startsWith('data:')) {
                            if(m.content.includes('.pdf') || m.content.includes('pdf')) {
                                contentHtml = `<a href="${m.content}" target="_blank" style="color:var(--accent); font-weight:800; text-decoration:underline;">📄 Download PDF Document</a>`;
                            } else if(m.content.match(/\.(jpeg|jpg|png|gif)/i) || m.content.startsWith('data:image')) {
                                contentHtml = `<img src="${m.content}" style="max-width:180px; border-radius:8px;" />`;
                            } else {
                                contentHtml = `<audio controls src="${m.content}" style="width:180px; height:32px;"></audio>`;
                            }
                        }
                        return `
                            <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                                <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name}</div>
                                <div>${contentHtml}</div>
                            </div>
                        `;
                    }).join('');
                    stream.scrollTop = stream.scrollHeight;
                }
            }

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900;">💬 Chat with ${friendFullName} (@${friendUsername})</h3>
                    <button class="btn-action" onclick="openSocialHub()" style="width:70px; padding:6px; font-size:0.75rem; margin-top:0;">Back</button>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-msg-stream"></div>
                    <div class="chat-input-bar">
                        <button onclick="startVoiceRecording('direct')" id="btn-mic" title="Record Audio" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">🎤</button>
                        <label title="Attach File / PDF / Photo" style="cursor:pointer; font-size:1.1rem; margin-bottom:0;">📎<input type="file" id="chat-file-input" onchange="handleFileUpload(event, 'direct')" style="display:none;" accept="image/*,.pdf,.doc,.docx" /></label>
                        <input type="text" id="chat-text-input" placeholder="Type message..." style="margin-bottom:0; flex:1; padding:7px 10px; font-size:0.82rem;" />
                        <button onclick="sendDirectMessageContent()" class="btn-action" style="width:60px; padding:7px; font-size:0.82rem; margin-top:0;">Send</button>
                    </div>
                    <div id="voice-recording-controls" class="hidden" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:var(--surface-card-hover); border-top:1px solid var(--border);">
                        <span style="font-size:0.78rem; color:var(--danger); font-weight:800;">🔴 Recording Voice Note...</span>
                        <div style="display:flex; gap:6px;">
                            <button onclick="cancelVoiceRecording()" style="padding:4px 10px; border-radius:8px; border:none; background:var(--danger); color:white; font-size:0.75rem; font-weight:700; cursor:pointer;">Cancel</button>
                            <button onclick="stopAndSendVoiceRecording('direct')" style="padding:4px 10px; border-radius:8px; border:none; background:var(--success); color:white; font-size:0.75rem; font-weight:700; cursor:pointer;">Stop & Send 🚀</button>
                        </div>
                    </div>
                </div>
            `;
            await fetchAndRenderMessages();
            if(dmPollingInterval) clearInterval(dmPollingInterval);
            dmPollingInterval = setInterval(fetchAndRenderMessages, 2500);
        }

        function handleFileUpload(event, mode, groupId = null, groupTitle = null) {
            const file = event.target.files[0];
            if(!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                if(mode === 'direct') {
                    sendDirectMessageContent(e.target.result);
                } else {
                    sendFriendGroupMsgContent(groupId, groupTitle, e.target.result);
                }
                showToast('File attached & sent!');
            };
            reader.readAsDataURL(file);
        }

        async function startVoiceRecording(mode, groupId = null, groupTitle = null) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                let options = { mimeType: 'audio/webm' };
                if (!MediaRecorder.isTypeSupported('audio/webm')) {
                    options = { mimeType: 'audio/mp4' };
                }
                mediaRecorder = new MediaRecorder(stream, options);
                audioChunks = [];
                mediaRecorder.ondataavailable = e => {
                    if (e.data && e.data.size > 0) audioChunks.push(e.data);
                };
                mediaRecorder.start();
                showToast('Recording voice note...');
                const controls = document.getElementById('voice-recording-controls');
                if(controls) controls.classList.remove('hidden');
                const micBtn = document.getElementById('btn-mic');
                if(micBtn) micBtn.style.color = 'var(--danger)';
            } catch(e) {
                showToast('Microphone unavailable or permission denied', true);
            }
        }

        function cancelVoiceRecording() {
            if(mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
            audioChunks = [];
            const controls = document.getElementById('voice-recording-controls');
            if(controls) controls.classList.add('hidden');
            const micBtn = document.getElementById('btn-mic');
            if(micBtn) micBtn.style.color = 'var(--accent)';
            showToast('Voice recording cancelled', true);
        }

        async function stopAndSendVoiceRecording(mode, groupId = null, groupTitle = null) {
            if(mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                    const reader = new FileReader();
                    reader.onload = async function(e) {
                        const base64Audio = e.target.result;
                        if(mode === 'direct') {
                            await sendDirectMessageContent(base64Audio);
                        } else {
                            await sendFriendGroupMsgContent(groupId, groupTitle, base64Audio);
                        }
                        showToast('Voice note sent!');
                    };
                    reader.readAsDataURL(audioBlob);
                };
                mediaRecorder.stop();
            }
            const controls = document.getElementById('voice-recording-controls');
            if(controls) controls.classList.add('hidden');
            const micBtn = document.getElementById('btn-mic');
            if(micBtn) micBtn.style.color = 'var(--accent)';
        }

        async function sendDirectMessageContent(contentOverride = null) {
            playSound('click');
            const input = document.getElementById('chat-text-input');
            const content = contentOverride || (input ? input.value.trim() : '');
            if(!content) return;

            await fetch('/api/direct-messages/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sender_username: sessionUser.username, receiver_username: activeChatFriendUser, sender_name: sessionUser.full_name, content })
            });
            if(!contentOverride && input) input.value = '';
            
            const res = await fetch(`/api/direct-messages/list?user1=${sessionUser.username}&user2=${activeChatFriendUser}`);
            const data = await res.json();
            const msgs = data.messages || [];
            const stream = document.getElementById('chat-msg-stream');
            if(stream) {
                stream.innerHTML = msgs.map(m => {
                    let contentHtml = m.content;
                    if(m.content.startsWith('blob:') || m.content.startsWith('http') || m.content.startsWith('data:')) {
                        if(m.content.includes('pdf')) {
                            contentHtml = `<a href="${m.content}" target="_blank" style="color:var(--accent); font-weight:800; text-decoration:underline;">📄 Download PDF Document</a>`;
                        } else if(m.content.startsWith('data:image')) {
                            contentHtml = `<img src="${m.content}" style="max-width:180px; border-radius:8px;" />`;
                        } else {
                            contentHtml = `<audio controls src="${m.content}" style="width:180px; height:32px;"></audio>`;
                        }
                    }
                    return `
                        <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                            <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name}</div>
                            <div>${contentHtml}</div>
                        </div>
                    `;
                }).join('');
                stream.scrollTop = stream.scrollHeight;
            }
        }

        async function openFriendGroupChat(groupId, title) {
            playSound('click');
            if(dmPollingInterval) clearInterval(dmPollingInterval);
            if(groupMsgPollingInterval) clearInterval(groupMsgPollingInterval);
            const box = document.getElementById('simulation-box');

            async function fetchAndRenderGroupMessages() {
                const res = await fetch(`/api/friend-groups/messages?group_id=${groupId}`);
                const data = await res.json();
                const msgs = data.messages || [];
                const stream = document.getElementById('chat-msg-stream');
                if(stream) {
                    stream.innerHTML = msgs.map(m => {
                        let contentHtml = m.content;
                        if(m.content.startsWith('blob:') || m.content.startsWith('http') || m.content.startsWith('data:')) {
                            if(m.content.includes('pdf')) {
                                contentHtml = `<a href="${m.content}" target="_blank" style="color:var(--accent); font-weight:800; text-decoration:underline;">📄 Download PDF Document</a>`;
                            } else if(m.content.startsWith('data:image')) {
                                contentHtml = `<img src="${m.content}" style="max-width:180px; border-radius:8px;" />`;
                            } else {
                                contentHtml = `<audio controls src="${m.content}" style="width:180px; height:32px;"></audio>`;
                            }
                        }
                        return `
                            <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                                <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name}</div>
                                <div>${contentHtml}</div>
                            </div>
                        `;
                    }).join('');
                    stream.scrollTop = stream.scrollHeight;
                }
            }

            box.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                    <h3 style="font-size:1.05rem; color:var(--accent); font-weight:900;">💬 Group: ${title}</h3>
                    <button class="btn-action" onclick="openSocialHub()" style="width:70px; padding:6px; font-size:0.75rem; margin-top:0;">Back</button>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-msg-stream"></div>
                    <div class="chat-input-bar">
                        <button onclick="startVoiceRecording('group', ${groupId}, '${title}')" id="btn-mic" title="Record Audio" style="background:none; border:none; color:var(--accent); font-size:1.1rem; cursor:pointer;">🎤</button>
                        <label title="Attach File / PDF / Photo" style="cursor:pointer; font-size:1.1rem; margin-bottom:0;">📎<input type="file" id="chat-file-input" onchange="handleFileUpload(event, 'group', ${groupId}, '${title}')" style="display:none;" accept="image/*,.pdf,.doc,.docx" /></label>
                        <input type="text" id="fg-text-input" placeholder="Type message..." style="margin-bottom:0; flex:1; padding:7px 10px; font-size:0.82rem;" />
                        <button onclick="sendFriendGroupMsgContent(${groupId}, '${title}')" class="btn-action" style="width:60px; padding:7px; font-size:0.82rem; margin-top:0;">Send</button>
                    </div>
                    <div id="voice-recording-controls" class="hidden" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:var(--surface-card-hover); border-top:1px solid var(--border);">
                        <span style="font-size:0.78rem; color:var(--danger); font-weight:800;">🔴 Recording Voice Note...</span>
                        <div style="display:flex; gap:6px;">
                            <button onclick="cancelVoiceRecording()" style="padding:4px 10px; border-radius:8px; border:none; background:var(--danger); color:white; font-size:0.75rem; font-weight:700; cursor:pointer;">Cancel</button>
                            <button onclick="stopAndSendVoiceRecording('group', ${groupId}, '${title}')" style="padding:4px 10px; border-radius:8px; border:none; background:var(--success); color:white; font-size:0.75rem; font-weight:700; cursor:pointer;">Stop & Send 🚀</button>
                        </div>
                    </div>
                </div>
            `;
            await fetchAndRenderGroupMessages();
            groupMsgPollingInterval = setInterval(fetchAndRenderGroupMessages, 2500);
        }

        async function sendFriendGroupMsgContent(groupId, title, contentOverride = null) {
            playSound('click');
            const input = document.getElementById('fg-text-input');
            const content = contentOverride || (input ? input.value.trim() : '');
            if(!content) return;
            await fetch('/api/friend-groups/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ group_id: groupId, sender_username: sessionUser.username, sender_name: sessionUser.full_name, content })
            });
            if(!contentOverride && input) input.value = '';
            
            const res = await fetch(`/api/friend-groups/messages?group_id=${groupId}`);
            const data = await res.json();
            const msgs = data.messages || [];
            const stream = document.getElementById('chat-msg-stream');
            if(stream) {
                stream.innerHTML = msgs.map(m => {
                    let contentHtml = m.content;
                    if(m.content.startsWith('blob:') || m.content.startsWith('http') || m.content.startsWith('data:')) {
                        if(m.content.includes('pdf')) {
                            contentHtml = `<a href="${m.content}" target="_blank" style="color:var(--accent); font-weight:800; text-decoration:underline;">📄 Download PDF Document</a>`;
                        } else if(m.content.startsWith('data:image')) {
                            contentHtml = `<img src="${m.content}" style="max-width:180px; border-radius:8px;" />`;
                        } else {
                            contentHtml = `<audio controls src="${m.content}" style="width:180px; height:32px;"></audio>`;
                        }
                    }
                    return `
                        <div class="chat-bubble ${m.sender_username === sessionUser.username ? 'outgoing' : 'incoming'}">
                            <div style="font-size:0.68rem; font-weight:800; color:var(--accent); margin-bottom:2px;">${m.sender_name}</div>
                            <div>${contentHtml}</div>
                        </div>
                    `;
                }).join('');
                stream.scrollTop = stream.scrollHeight;
            }
        }

        /* MODALS & BOUTIQUE */
        function openAvatarStudio() { playSound('click'); document.getElementById('avatar-studio-modal').style.display = 'flex'; }
        function closeAvatarStudio() { playSound('click'); document.getElementById('avatar-studio-modal').style.display = 'none'; }
        async function saveAvatarChanges() {
            playSound('click');
            const avatar_gender = document.getElementById('mod-gender').value;
            const res = await fetch('/api/user/avatar-update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, avatar_gender })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                updateDashboardUI();
                closeAvatarStudio();
                showToast('Avatar updated!');
            }
        }
        function openSettingsModal() { playSound('click'); document.getElementById('settings-modal').style.display = 'flex'; }
        function closeSettingsModal() { playSound('click'); document.getElementById('settings-modal').style.display = 'none'; }
        async function submitPasswordChangeModal() {
            playSound('click');
            const recovery_pin = document.getElementById('set-pin').value.trim();
            const new_password = document.getElementById('set-new-pass').value.trim();
            if(!recovery_pin || !new_password) { showToast('Fill all fields', true); return; }
            const res = await fetch('/api/user/password-change', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, recovery_pin, new_password })
            });
            if(res.ok) { showToast('Password updated!'); closeSettingsModal(); }
            else { showToast('Invalid PIN', true); }
        }

        async function openShop() {
            playSound('click');
            const res = await fetch('/api/shop/skins');
            const data = await res.json();
            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: #a78bfa; font-weight: 900;">🎁 Cabin Crew Equipment Boutique</h3>
                    <span style="font-size: 0.8rem; color: var(--warning); font-weight: 800;">⭐ ${sessionUser.xp_points} Stars</span>
                </div>
                <div style="max-height: 220px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; scrollbar-width: thin;">
                    ${data.skins.map(skin => {
                        const skinName = activeLang === 'fr' ? skin.skin_name_fr : (activeLang === 'ar' ? skin.skin_name_ar : skin.skin_name_en);
                        const skinDesc = activeLang === 'fr' ? skin.desc_fr : (activeLang === 'ar' ? skin.desc_ar : skin.desc_en);
                        const isEquipped = sessionUser.active_skin === skin.skin_name_en;
                        return `
                        <div style="background: var(--bg-deep); padding: 0.7rem 1rem; border-radius: 12px; border: 1px solid var(--border-glow); display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.6rem;">${skin.preview_svg}</span>
                                <div style="color: white; font-size: 0.85rem;"><b>${skinName}</b><div style="color: var(--text-muted); font-size: 0.7rem;">${skinDesc}</div></div>
                            </div>
                            <button class="btn-action" onclick="buySkin('${skin.skin_name_en}',${skin.cost})" style="width:95px; padding:6px; font-size:0.75rem; background:${isEquipped ? 'var(--success)' : '#8b5cf6'}; color:white; margin-top:0;">${isEquipped ? 'Equipped ✓' : (skin.cost === 0 ? 'Equipped' : skin.cost + ' ⭐')}</button>
                        </div>
                    `;}).join('')}
                </div>
            `;
        }

        async function buySkin(skinName, cost) {
            playSound('click');
            const res = await fetch('/api/shop/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, skin_name: skinName, cost })
            });
            const data = await res.json();
            if(res.ok) {
                sessionUser = data.user;
                localStorage.setItem('aero_crew_user_pro22', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast('Equipped ' + skinName + ' successfully!');
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
