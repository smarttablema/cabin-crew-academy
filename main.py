import os
import json
import base64
import hmac
import time
import hashlib
import random
import csv
import io
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from datetime import date, timedelta, datetime

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it in Railway > Variables (never put it in the code).")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

SECRET_KEYS = {"password", "recovery_pin"}

def _strip_secrets(x):
    """Removes secrets and neutralises HTML tags in every text sent to the browser (blocks injected scripts)."""
    if isinstance(x, dict):
        return {k: (v if k == "preview_svg" else _strip_secrets(v)) for k, v in x.items() if k not in SECRET_KEYS}
    if isinstance(x, list):
        return [_strip_secrets(v) for v in x]
    if isinstance(x, str):
        return x.replace("<", "\u2039").replace(">", "\u203a")
    return x

class SafeJSONResponse(JSONResponse):
    """Never lets password hashes or recovery PINs leave the server."""
    def render(self, content):
        return super().render(_strip_secrets(content))

def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return "p1$" + salt.hex() + "$" + dk.hex()

def verify_password(pw: str, stored: str) -> bool:
    stored = stored or ""
    if stored.startswith("p1$"):
        try:
            _, salt_hex, dk_hex = stored.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), 200_000)
            return hmac.compare_digest(dk.hex(), dk_hex)
        except Exception:
            return False
    return hmac.compare_digest(stored.encode(), pw.encode())  # old plain-text account, upgraded at login

SECRET = (os.getenv("SECRET_KEY") or hashlib.sha256(DATABASE_URL.encode()).hexdigest()).encode()

def make_token(user) -> str:
    payload = "|".join([user["username"], user["phone_number"], user["role"], str(int(time.time()) + 30 * 86400)])
    sig = hmac.new(SECRET, payload.encode(), "sha256").hexdigest()
    return base64.urlsafe_b64encode(payload.encode()).decode() + "." + sig

def read_token(tok: str):
    try:
        b, sig = tok.rsplit(".", 1)
        payload = base64.urlsafe_b64decode(b.encode()).decode()
        if not hmac.compare_digest(hmac.new(SECRET, payload.encode(), "sha256").hexdigest(), sig):
            return None
        username, phone, role, exp = payload.split("|")
        if int(exp) < time.time():
            return None
        return {"username": username, "phone": phone, "role": role}
    except Exception:
        return None

PUBLIC_API = {"/api/login", "/api/register", "/api/user/password-change", "/api/health"}
TEACHER_ONLY = {"/api/teacher/adjust-xp", "/api/teacher/dashboard", "/api/teacher/export-csv", "/api/exam/create",
                "/api/exam/create-advanced", "/api/exam/upload-pdf", "/api/exam/delete",
                "/api/lesson/create", "/api/lesson/delete", "/api/attendance/groups", "/api/attendance/group/save", "/api/attendance/group/delete", "/api/attendance/roll", "/api/attendance/mark", "/api/demo/seed", "/api/demo/clear", "/api/announce/create", "/api/announce/delete", "/api/teacher/set-code", "/api/exam/reset-submission", "/api/exam/review"}
ACTOR_FIELDS = ("username", "student_username", "teacher_username", "sender_username")

def identity_problem(scope, body: bytes, user):
    from urllib.parse import parse_qs
    if scope["path"] in TEACHER_ONLY and user["role"] != "teacher":
        return "Teachers only."
    if scope["path"].startswith("/api/admin/") and user["role"] != "admin":
        return "Academy directors only."
    fields = {k: v[0] for k, v in parse_qs(scope.get("query_string", b"").decode()).items()}
    try:
        j = json.loads(body) if body else None
        if isinstance(j, dict):
            fields.update({k: v for k, v in j.items() if isinstance(v, (str, int))})
    except Exception:
        pass
    teacher_action = user["role"] == "teacher" and scope["path"] in TEACHER_ONLY
    for f in ACTOR_FIELDS:
        if f == "student_username" and teacher_action:
            continue
        if f in fields and str(fields[f]) != user["username"]:
            return "You can only act as yourself."
    if "phone_number" in fields and str(fields["phone_number"]) != user["phone"]:
        return "You can only act as yourself."
    return None

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith("/api/") or path in PUBLIC_API:
            return await self.app(scope, receive, send)
        auth = dict(scope["headers"]).get(b"authorization", b"").decode()
        user = read_token(auth[7:]) if auth.startswith("Bearer ") else None
        if not user:
            return await SafeJSONResponse({"detail": "Session expired. Please log in again."}, status_code=401)(scope, receive, send)
        body, more = b"", True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
        problem = identity_problem(scope, body, user)
        if problem:
            return await SafeJSONResponse({"detail": problem}, status_code=403)(scope, receive, send)
        sent = False
        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()
        scope.setdefault("state", {})["auth"] = user
        await self.app(scope, replay, send)

def today_local():
    """The academy day follows Morocco time, not UTC, so a student practising at 00:30 is counted on the right day."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Casablanca")).date()
    except Exception:
        return (datetime.utcnow() + timedelta(hours=1)).date()

def log_day(cur, username=None, phone=None):
    """Remembers every day a student practised (used for attendance sheets). Never breaks the caller."""
    try:
        cur.execute("SAVEPOINT logday")
        if phone:
            cur.execute("INSERT INTO aero_v22_activity (username, day) SELECT username, %s FROM aero_v22_users WHERE phone_number = %s ON CONFLICT DO NOTHING;", (today_local(), phone))
        else:
            cur.execute("INSERT INTO aero_v22_activity (username, day) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (username, today_local()))
        cur.execute("RELEASE SAVEPOINT logday")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT logday")

def bump_streak(cur, username):
    log_day(cur, username)
    cur.execute("SELECT streak, last_practice_date FROM aero_v22_users WHERE username = %s;", (username,))
    u = cur.fetchone()
    if not u:
        return
    today = today_local()
    last = u["last_practice_date"]
    if last == today:
        return
    streak = (u["streak"] or 0) + 1 if last == today - timedelta(days=1) else 1
    cur.execute("UPDATE aero_v22_users SET streak = %s, last_practice_date = %s WHERE username = %s;", (streak, today, username))

LOGIN_FAILS = {}
def login_blocked(key: str) -> bool:
    n, t0 = LOGIN_FAILS.get(key, (0, 0))
    if time.time() - t0 > 600:
        LOGIN_FAILS.pop(key, None)
        return False
    return n >= 8
def login_failed(key: str):
    n, t0 = LOGIN_FAILS.get(key, (0, time.time()))
    LOGIN_FAILS[key] = (n + 1, t0)

app = FastAPI(default_response_class=SafeJSONResponse)
app.add_middleware(AuthMiddleware)

STARTUP_ERRORS = []

def startup_extras():
    """Newer tables. Each statement is isolated so one failure can never stop the site from starting."""
    statements = [
        "ALTER TABLE aero_v22_users ALTER COLUMN password TYPE TEXT;",
        "ALTER TABLE aero_v22_exam_submissions ADD COLUMN IF NOT EXISTS answers JSONB;",
        """CREATE TABLE IF NOT EXISTS aero_v22_class_lessons (
               id SERIAL PRIMARY KEY, group_code VARCHAR(50), teacher_username VARCHAR(50),
               title VARCHAR(120), questions JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE IF NOT EXISTS aero_v22_owned_skins (
               id SERIAL PRIMARY KEY, username VARCHAR(50), skin_name_en VARCHAR(50), UNIQUE (username, skin_name_en));""",
        """INSERT INTO aero_v22_owned_skins (username, skin_name_en)
               SELECT username, active_skin FROM aero_v22_users WHERE active_skin IS NOT NULL ON CONFLICT DO NOTHING;""",
        """CREATE TABLE IF NOT EXISTS aero_v22_announcements (
               id SERIAL PRIMARY KEY, group_code VARCHAR(50), teacher_username VARCHAR(50),
               message VARCHAR(300), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        """CREATE TABLE IF NOT EXISTS aero_v22_weekly_xp (
               username VARCHAR(50), week_start DATE, start_xp INT, PRIMARY KEY (username, week_start));""",
        """CREATE TABLE IF NOT EXISTS aero_v22_payments (
               username VARCHAR(50) PRIMARY KEY, paid_until DATE, monthly_fee INT, remind_days INT DEFAULT 3,
               message VARCHAR(300), updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""",
        "ALTER TABLE aero_v22_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;",
        "ALTER TABLE aero_v22_users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE aero_v22_groups ADD COLUMN IF NOT EXISTS capacity INT DEFAULT 30;",
        "CREATE TABLE IF NOT EXISTS aero_v22_att_groups (id SERIAL PRIMARY KEY, teacher_username VARCHAR(50), name VARCHAR(80), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
        "CREATE TABLE IF NOT EXISTS aero_v22_att_members (group_id INT, student_username VARCHAR(50), PRIMARY KEY (group_id, student_username));",
        "CREATE TABLE IF NOT EXISTS aero_v22_attendance (group_id INT, student_username VARCHAR(50), day DATE, status VARCHAR(10), marked_by VARCHAR(50), marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (group_id, student_username, day));",
        "CREATE TABLE IF NOT EXISTS aero_v22_att_roster (id SERIAL PRIMARY KEY, group_id INT, name VARCHAR(80), nickname VARCHAR(40));",
        "CREATE TABLE IF NOT EXISTS aero_v22_att_marks (roster_id INT, day DATE, status VARCHAR(10), marked_by VARCHAR(50), marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (roster_id, day));",
        "CREATE TABLE IF NOT EXISTS aero_v22_activity (username VARCHAR(50), day DATE, PRIMARY KEY (username, day));",
        "CREATE TABLE IF NOT EXISTS aero_v22_payment_log (id SERIAL PRIMARY KEY, username VARCHAR(50), amount INT, months INT, paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
        """CREATE TABLE IF NOT EXISTS aero_v22_mistakes (
               id SERIAL PRIMARY KEY, username VARCHAR(50), question_text TEXT, incorrect_answer TEXT, correct_answer TEXT,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE (username, question_text));""",
    ]
    for sql in statements:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            STARTUP_ERRORS.append(str(e)[:200])
            print("STARTUP WARNING:", e)

EXPECTED_TABLES = ["users", "battles", "exams", "exam_submissions", "shop_skins", "mistakes", "class_lessons", "owned_skins", "announcements", "weekly_xp", "payments", "activity", "payment_log", "att_groups", "att_roster", "att_marks"]

@app.get("/api/health")
def health():
    """Open this address after every deploy: it shows whether all tables exist."""
    out = {"status": "ok", "tables": {}, "startup_errors": STARTUP_ERRORS}
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        have = {r["table_name"] for r in cur.fetchall()}
        cur.close()
        conn.close()
        for t in EXPECTED_TABLES:
            out["tables"][t] = ("aero_v22_" + t) in have
        if not all(out["tables"].values()) or STARTUP_ERRORS:
            out["status"] = "needs attention"
    except Exception as e:
        out["status"] = "database error: " + str(e)[:120]
    return out

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
            group_code VARCHAR(50) DEFAULT '',
            friends TEXT[] DEFAULT ARRAY[]::TEXT[],
            xp_points INT DEFAULT 1500,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 21,
            flight_hours INT DEFAULT 45,
            mistake_hangar TEXT[] DEFAULT ARRAY[]::TEXT[],
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
        cur.execute("ALTER TABLE aero_v22_users ADD COLUMN IF NOT EXISTS flight_hours INT DEFAULT 45;")
        cur.execute("ALTER TABLE aero_v22_users ADD COLUMN IF NOT EXISTS mistake_hangar TEXT[] DEFAULT ARRAY[]::TEXT[];")
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
        CREATE TABLE IF NOT EXISTS aero_v22_group_messages (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            sender_username VARCHAR(50),
            message TEXT,
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
        CREATE TABLE IF NOT EXISTS aero_v22_exams (
            id SERIAL PRIMARY KEY,
            group_code VARCHAR(50),
            teacher_username VARCHAR(50),
            title TEXT,
            exam_data JSONB,
            pdf_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    try:
        cur.execute("ALTER TABLE aero_v22_exams ADD COLUMN IF NOT EXISTS pdf_url TEXT;")
    except Exception:
        conn.commit()

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
        ('emergency', 'Marine', 'Slide-Raft Unit', 'Toboggan-Radeau d’Évacuation', 'طوافة الانزلاق للإخلاء', 600, '🛟', 'Multi-person inflatable slide and emergency sea rescue raft.', 'Toboggan et radeau de sauvetage.', 'منزلق قابل للنفخ وطوافة إنقاذ بحري طارئة.'),
        ('pilot', 'Exclusive', 'Captain Pilot Hat', 'Casquette de Commandant', 'قبعة قائد الطائرة', 750, '🧢', 'Official four-stripe captain visor hat for elite aviation commanders.', 'Casquette officielle de commandant.', 'قبعة القائد الرسمية للطيارين النخبة.')
        ON CONFLICT DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
    startup_extras()

class RegisterModel(BaseModel):
    phone_number: str
    username: str
    full_name: str
    password: str
    recovery_pin: str
    role: str = 'student'
    avatar_gender: str = 'steward'
    group_code: str = ''
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

class DeleteExamModel(BaseModel):
    exam_id: int
    teacher_username: str

class AdjustXPModel(BaseModel):
    teacher_username: str
    student_username: str
    xp_delta: int

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

class GroupMessageModel(BaseModel):
    group_code: str
    sender_username: str
    message: str

class DmShortModel(BaseModel):
    sender_username: str
    receiver_username: str
    message: str

class BuySkinModel(BaseModel):
    phone_number: str
    skin_name: str
    cost: int

class NodeCompleteModel(BaseModel):
    phone_number: str
    node_id: str
    lost_heart: bool = False
    mistake_question: str = None

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
    score: int = 0

class BattleAnswerModel(BaseModel):
    match_id: str
    username: str
    q_index: int
    choice: int

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
    import re
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", data.username or ""):
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Username: 3-30 letters, numbers, dot, dash or underscore (no spaces).")
    data.full_name = re.sub(r"[<>&\"'`]", "", data.full_name or "").strip()[:60]
    if not data.full_name:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Please enter your full name.")
    if len(data.password or "") < 6:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    if data.role == "teacher":
        invite = os.getenv("TEACHER_INVITE_CODE")
        if not invite:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Teacher registration is not enabled yet. Ask the administrator.")
        if not hmac.compare_digest((data.teacher_code or "").encode(), invite.encode()):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Invalid teacher access code.")
        assigned_role = "teacher"
        group_code = ""

    if data.role == "admin":
        invite = os.getenv("ADMIN_INVITE_CODE")
        if not invite:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Director registration is not enabled yet. Set ADMIN_INVITE_CODE on the server.")
        if not hmac.compare_digest((data.teacher_code or "").encode(), invite.encode()):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Invalid director access code.")
        assigned_role = "admin"
        group_code = ""

    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s OR username = %s;", (data.phone_number, data.username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number or username already taken.")
    
    cur.execute(
        """INSERT INTO aero_v22_users (phone_number, username, full_name, password, recovery_pin, role, avatar_gender, group_code, xp_points, streak, flight_hours) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0) RETURNING *;""",
        (data.phone_number, data.username, data.full_name, hash_password(data.password), data.recovery_pin, assigned_role, data.avatar_gender, group_code)
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
    return {"status": "success", "user": user, "token": make_token(user)}

@app.post("/api/login")
def login(data: LoginModel):
    conn = get_db_connection()
    cur = conn.cursor()
    if login_blocked(data.phone_number):
        cur.close()
        conn.close()
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait 10 minutes and try again.")
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user or not verify_password(data.password, user["password"]):
        login_failed(data.phone_number)
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    LOGIN_FAILS.pop(data.phone_number, None)
    if not (user["password"] or "").startswith("p1$"):
        cur.execute("UPDATE aero_v22_users SET password = %s WHERE id = %s;", (hash_password(data.password), user["id"]))

    today = today_local()
    last_prac = user.get("last_practice_date")
    streak = user.get("streak", 21)

    if last_prac and last_prac < today - timedelta(days=1):
        streak = 0
    elif not last_prac:
        streak = 0

    cur.execute("UPDATE aero_v22_users SET streak = %s WHERE id = %s RETURNING *;", (streak, user["id"]))
    updated_user = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    return {"status": "success", "user": updated_user, "token": make_token(updated_user)}

@app.get("/api/user/refresh")
def refresh_user(phone_number: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (phone_number,))
    user = cur.fetchone()
    if user:
        last = user.get("last_practice_date")
        if (not last or last < today_local() - timedelta(days=1)) and (user.get("streak") or 0) != 0:
            cur.execute("UPDATE aero_v22_users SET streak = 0 WHERE id = %s RETURNING *;", (user["id"],))
            user = cur.fetchone()
            conn.commit()
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
    if login_blocked("pin:" + data.phone_number):
        cur.close()
        conn.close()
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait 10 minutes and try again.")
    cur.execute("SELECT * FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if len(data.new_password or "") < 6:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if not user or not hmac.compare_digest(str(user["recovery_pin"] or "").encode(), str(data.recovery_pin or "").encode()):
        cur.close()
        conn.close()
        login_failed("pin:" + data.phone_number)
        raise HTTPException(status_code=400, detail="Invalid recovery PIN.")
    cur.execute("UPDATE aero_v22_users SET password = %s WHERE phone_number = %s;", (hash_password(data.new_password), data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/user/group-update")
def update_user_group(data: GroupUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    if not data.group_code.strip():
        cur.execute("UPDATE aero_v22_users SET group_code = '' WHERE phone_number = %s RETURNING *;", (data.phone_number,))
        left = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "user": left}
    cur.execute("SELECT * FROM aero_v22_groups WHERE UPPER(group_code) = UPPER(%s);", (data.group_code.strip(),))
    grp = cur.fetchone()
    if not grp:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid teacher/group code.")

    cur.execute("UPDATE aero_v22_users SET group_code = %s WHERE phone_number = %s RETURNING *;", (grp["group_code"], data.phone_number))
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

@app.get("/api/dm/list")
def get_dm_list_alias(user1: str, user2: str):
    return get_direct_messages(user1, user2)

@app.post("/api/dm/send")
def send_dm_alias(data: DmShortModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM aero_v22_users WHERE username = %s;", (data.sender_username,))
    u = cur.fetchone()
    sender_name = u["full_name"] if u else data.sender_username
    cur.close()
    conn.close()
    
    dm_data = DirectMessageModel(
        sender_username=data.sender_username,
        receiver_username=data.receiver_username,
        sender_name=sender_name,
        content=data.message
    )
    return send_direct_message(dm_data)

@app.get("/api/group/messages")
def get_group_messages(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_group_messages WHERE group_code = %s ORDER BY id ASC LIMIT 50;", (group_code,))
    msgs = cur.fetchall()
    cur.close()
    conn.close()
    return {"messages": msgs}

@app.post("/api/group/message/send")
def send_group_message(data: GroupMessageModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO aero_v22_group_messages (group_code, sender_username, message) VALUES (%s, %s, %s) RETURNING *;", (data.group_code, data.sender_username, data.message))
    msg = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": msg}

@app.get("/api/group/info")
def get_group_info(group_code: str, request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_groups WHERE group_code = %s;", (group_code,))
    grp = cur.fetchone()
    cur.execute("SELECT username, full_name, role, avatar_gender, xp_points, flight_hours, streak, completed_nodes FROM aero_v22_users WHERE group_code = %s;", (group_code,))
    members = cur.fetchall()
    cur.execute("SELECT * FROM aero_v22_exams WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    exams = cur.fetchall()

    cur.execute("""
        SELECT s.*, e.group_code FROM aero_v22_exam_submissions s
        JOIN aero_v22_exams e ON s.exam_id = e.id
        WHERE e.group_code = %s;
    """, (group_code,))
    submissions = cur.fetchall()

    cur.close()
    conn.close()
    if request.state.auth["role"] != "teacher":
        for e in exams:
            raw = e.get("exam_data")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = []
            e["exam_data"] = [{k: v for k, v in q.items() if k not in ("correct", "accepted")} for q in (raw or []) if isinstance(q, dict)]
    return {"group": grp, "members": members, "lessons": [], "exams": exams, "submissions": submissions}

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

@app.post("/api/exam/upload-pdf")
async def upload_pdf_exam(
    group_code: str = Form(...),
    teacher_username: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...)
):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Store dummy or mock URL or local path reference for the uploaded PDF
    pdf_url = f"https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf" # Mock viewer link or secure blob
    
    import json
    cur.execute(
        "INSERT INTO aero_v22_exams (group_code, teacher_username, title, exam_data, pdf_url) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (group_code, teacher_username, title, json.dumps([]), pdf_url)
    )
    exam = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "exam": exam}

@app.post("/api/exam/delete")
def delete_exam(data: DeleteExamModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aero_v22_exams WHERE id = %s AND teacher_username = %s RETURNING *;", (data.exam_id, data.teacher_username))
    exam = cur.fetchone()
    if not exam:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Exam not found or unauthorized.")
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/teacher/adjust-xp")
def adjust_student_xp(data: AdjustXPModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + %s WHERE username = %s RETURNING *;", (data.xp_delta, data.student_username))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found.")
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": user}

@app.get("/api/teacher/export-csv")
def export_gradebook_csv(group_code: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, full_name, xp_points, flight_hours, streak FROM aero_v22_users WHERE group_code = %s;", (group_code,))
    members = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Full Name", "XP Points", "Flight Hours", "Streak"])
    for m in members:
        writer.writerow([m["username"], m["full_name"], m["xp_points"], m["flight_hours"], m["streak"]])
    
    output.seek(0)
    cur.close()
    conn.close()
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=gradebook_{group_code}.csv"}
    )

def submit_exam(data: SubmitExamModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_exam_submissions WHERE exam_id = %s AND student_username = %s;", (data.exam_id, data.student_username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="You have already submitted this exam.")

    cur.execute(
        "INSERT INTO aero_v22_exam_submissions (exam_id, student_username, student_name, score, total_questions, time_spent_seconds) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.exam_id, data.student_username, data.student_name, data.score, data.total_questions, data.time_spent_seconds)
    )
    sub = cur.fetchone()
    cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 100, flight_hours = flight_hours + 5 WHERE username = %s;", (data.student_username,))
    bump_streak(cur, data.student_username)
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "submission": sub}

@app.post("/api/node/complete")
def complete_roadmap_node(data: NodeCompleteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT completed_nodes, xp_points, hearts, streak, flight_hours, mistake_hangar, last_practice_date FROM aero_v22_users WHERE phone_number = %s;", (data.phone_number,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    nodes = user.get("completed_nodes") or []
    hearts = user.get("hearts", 5)
    xp = user.get("xp_points", 0)
    streak = user.get("streak", 0)
    flight_hours = user.get("flight_hours", 45)
    mistakes = user.get("mistake_hangar") or []

    if data.lost_heart:
        hearts = max(0, hearts - 1)
        if data.mistake_question and data.mistake_question not in mistakes:
            mistakes.append(data.mistake_question)
        cur.execute("UPDATE aero_v22_users SET hearts = %s, last_heart_loss_date = %s, mistake_hangar = %s WHERE phone_number = %s;", (hearts, today_local(), mistakes, data.phone_number))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "completed_nodes": nodes, "xp": xp, "hearts": hearts, "streak": streak, "flight_hours": flight_hours}

    if hearts <= 0:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Out of hearts! Visit the Heart Recovery Lounge.")

    today = today_local()
    last_day = user.get("last_practice_date")
    if last_day != today:
        streak = streak + 1 if last_day == today - timedelta(days=1) else 1

    if data.node_id not in nodes:
        nodes.append(data.node_id)
        cur.execute("UPDATE aero_v22_users SET completed_nodes = %s, xp_points = xp_points + 50, flight_hours = flight_hours + 1, streak = %s, last_practice_date = %s WHERE phone_number = %s RETURNING completed_nodes, xp_points, hearts, streak, flight_hours;", (nodes, streak, today, data.phone_number))
    else:
        cur.execute("UPDATE aero_v22_users SET streak = %s, last_practice_date = %s WHERE phone_number = %s RETURNING completed_nodes, xp_points, hearts, streak, flight_hours;", (streak, today, data.phone_number))
    res = cur.fetchone()
    log_day(cur, phone=data.phone_number)
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "completed_nodes": res["completed_nodes"], "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"], "flight_hours": res["flight_hours"]}

@app.get("/api/shop/skins")
def get_skins(request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_shop_skins ORDER BY cost ASC;")
    skins = cur.fetchall()
    cur.execute("SELECT skin_name_en FROM aero_v22_owned_skins WHERE username = %s;", (request.state.auth["username"],))
    owned = [r["skin_name_en"] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return {"skins": skins, "owned": owned}

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
    cur.execute("SELECT cost FROM aero_v22_shop_skins WHERE skin_name_en = %s LIMIT 1;", (data.skin_name,))
    sk = cur.fetchone()
    if not sk:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Unknown skin.")
    cur.execute("SELECT 1 FROM aero_v22_owned_skins WHERE username = %s AND skin_name_en = %s;", (user["username"], data.skin_name))
    already_owned = bool(cur.fetchone()) or user.get("active_skin") == data.skin_name or sk["cost"] == 0
    price = 0 if already_owned else sk["cost"]
    if user["xp_points"] < price:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough XP stars!")
    new_xp = user["xp_points"] - price
    cur.execute("UPDATE aero_v22_users SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated = cur.fetchone()
    cur.execute("INSERT INTO aero_v22_owned_skins (username, skin_name_en) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (user["username"], data.skin_name))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "user": updated}

@app.post("/api/battle/invite")
def send_battle_invite(data: BattleInviteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    if data.receiver_username == data.sender_username:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="You cannot challenge yourself.")
    cur.execute("SELECT 1 FROM aero_v22_users WHERE username = %s;", (data.receiver_username,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Opponent not found.")
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

def _strip_correct(qs):
    return [{"q": q["q"], "options": q["options"]} for q in (qs or [])]

def _load_match(cur, match_id, me):
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (match_id,))
    m = cur.fetchone()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if me not in (m["sender_username"], m["receiver_username"]):
        raise HTTPException(status_code=403, detail="This is not your match.")
    return m

def _set_score_key(cur, match_id, key, value):
    cur.execute("UPDATE aero_v22_battles SET scores = jsonb_set(COALESCE(scores, '{}'::jsonb), %s::text[], %s::jsonb, true) WHERE match_id = %s;",
                ([key], json.dumps(value), match_id))

def _try_finalize(cur, match_id):
    """Decides the winner on the server once both players finished (or one finished and the other abandoned for 15 min)."""
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (match_id,))
    m = cur.fetchone()
    sc = m.get("scores") or {}
    if sc.get("_final") or m["status"] != "accepted":
        return m
    a, b = m["sender_username"], m["receiver_username"]
    da, db = sc.get(a, {}).get("done"), sc.get(b, {}).get("done")
    expired = bool(m.get("created_at")) and (datetime.utcnow() - m["created_at"]).total_seconds() > 900
    if not ((da and db) or ((da or db) and expired)):
        return m
    cur.execute("UPDATE aero_v22_battles SET scores = jsonb_set(COALESCE(scores, '{}'::jsonb), '{_final}', 'true'::jsonb, true), status = 'completed' "
                "WHERE match_id = %s AND NOT (COALESCE(scores, '{}'::jsonb) ? '_final') RETURNING match_id;", (match_id,))
    if cur.fetchone():
        sa, sb = sc.get(a, {}).get("score", 0), sc.get(b, {}).get("score", 0)
        bump_streak(cur, a)
        bump_streak(cur, b)
        for user, mine, theirs in ((a, sa, sb), (b, sb, sa)):
            if mine > theirs:
                cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 100, flight_hours = flight_hours + 3 WHERE username = %s;", (user,))
            elif mine == theirs:
                cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + 50, flight_hours = flight_hours + 1 WHERE username = %s;", (user,))
    cur.execute("SELECT * FROM aero_v22_battles WHERE match_id = %s;", (match_id,))
    return cur.fetchone()

def _battle_view(m, me):
    sc = m.get("scores") or {}
    opp = m["receiver_username"] if me == m["sender_username"] else m["sender_username"]
    mine, theirs = sc.get(me, {}), sc.get(opp, {})
    view = {"status": m["status"], "questions": _strip_correct(m["questions"]), "opponent": opp,
            "your_score": mine.get("score", 0), "your_answered": len(mine.get("answers", {})), "you_done": bool(mine.get("done")),
            "opponent_answered": len(theirs.get("answers", {})), "opponent_done": bool(theirs.get("done"))}
    if sc.get("_final"):
        os_, ys = theirs.get("score", 0), mine.get("score", 0)
        view.update({"opponent_score": os_, "result": "win" if ys > os_ else "draw" if ys == os_ else "loss"})
    return view

@app.get("/api/battle/incoming")
def get_incoming_battle(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT match_id, sender_username, sender_name FROM aero_v22_battles WHERE receiver_username = %s AND status = 'pending' ORDER BY created_at DESC LIMIT 1;", (username,))
    invite = cur.fetchone()
    cur.close()
    conn.close()
    return {"invite": invite}

@app.post("/api/battle/respond")
def respond_battle_invite(data: BattleRespondModel, request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        m = _load_match(cur, data.match_id, me)
        if m["receiver_username"] != me or m["status"] != "pending":
            raise HTTPException(status_code=400, detail="This invitation can no longer be answered.")
        new_status = "accepted" if data.accept else "rejected"
        cur.execute("UPDATE aero_v22_battles SET status = %s, created_at = CURRENT_TIMESTAMP WHERE match_id = %s;", (new_status, data.match_id))
        conn.commit()
        return {"status": new_status, "questions": _strip_correct(m["questions"])}
    finally:
        cur.close()
        conn.close()

@app.get("/api/battle/status")
def get_battle_status(match_id: str, request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        _load_match(cur, match_id, me)
        m = _try_finalize(cur, match_id)
        conn.commit()
        return _battle_view(m, me)
    finally:
        cur.close()
        conn.close()

@app.post("/api/battle/cancel")
def cancel_battle(data: BattleCancelModel, request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        m = _load_match(cur, data.match_id, me)
        if m["status"] in ("pending", "accepted") and not m.get("scores"):
            cur.execute("UPDATE aero_v22_battles SET status = 'canceled' WHERE match_id = %s;", (data.match_id,))
            conn.commit()
        return {"status": "canceled"}
    finally:
        cur.close()
        conn.close()

@app.post("/api/battle/answer")
def battle_answer(data: BattleAnswerModel):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        m = _load_match(cur, data.match_id, data.username)
        if m["status"] != "accepted":
            raise HTTPException(status_code=400, detail="The battle is not active.")
        qs = m["questions"] or []
        if data.q_index < 0 or data.q_index >= len(qs):
            raise HTTPException(status_code=400, detail="Invalid question.")
        mine = (m.get("scores") or {}).get(data.username) or {"answers": {}, "score": 0, "done": False}
        if mine.get("done") or str(data.q_index) in mine["answers"]:
            raise HTTPException(status_code=400, detail="Already answered.")
        ok = data.choice == qs[data.q_index]["correct"]
        mine["answers"][str(data.q_index)] = data.choice
        mine["score"] = mine.get("score", 0) + (1 if ok else 0)
        _set_score_key(cur, data.match_id, data.username, mine)
        conn.commit()
        return {"correct": ok, "correct_index": qs[data.q_index]["correct"], "your_score": mine["score"]}
    finally:
        cur.close()
        conn.close()

@app.post("/api/battle/submit")
def submit_battle_score(data: BattleSubmitModel):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        m = _load_match(cur, data.match_id, data.username)
        mine = (m.get("scores") or {}).get(data.username) or {"answers": {}, "score": 0, "done": False}
        mine["done"] = True
        _set_score_key(cur, data.match_id, data.username, mine)
        m = _try_finalize(cur, data.match_id)
        conn.commit()
        return _battle_view(m, data.username)
    finally:
        cur.close()
        conn.close()

class MistakeLogModel(BaseModel):
    username: str
    question_text: str
    incorrect_answer: str = ""
    correct_answer: str = ""

class AdvancedExamModel(BaseModel):
    group_code: str
    teacher_username: str
    title: str
    exam_data: list = []
    is_pdf: bool = False
    pdf_url: str = None

@app.get("/api/student/mistakes")
def get_student_mistakes(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT question_text, incorrect_answer, correct_answer, created_at FROM aero_v22_mistakes WHERE username = %s ORDER BY id DESC LIMIT 100;", (username,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"mistakes": rows}

@app.post("/api/student/log-mistake")
def log_student_mistake(data: MistakeLogModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO aero_v22_mistakes (username, question_text, incorrect_answer, correct_answer)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (username, question_text)
           DO UPDATE SET incorrect_answer = EXCLUDED.incorrect_answer, correct_answer = EXCLUDED.correct_answer, created_at = CURRENT_TIMESTAMP;""",
        (data.username, data.question_text, data.incorrect_answer, data.correct_answer)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/exam/create-advanced")
def create_advanced_exam(data: AdvancedExamModel):
    import json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM aero_v22_users WHERE username = %s;", (data.teacher_username,))
    t = cur.fetchone()
    if not t or t["role"] != "teacher":
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Only teachers can publish exams.")
    import re
    if len(data.exam_data) > 101:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="An exam can have at most 100 questions.")
    code = data.group_code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_-]{3,30}", code):
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Choose a code of 3-30 letters, numbers, - or _.")
    cur.execute("SELECT 1 FROM aero_v22_exams WHERE group_code = %s AND teacher_username <> %s LIMIT 1;", (code, data.teacher_username))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=409, detail="This code already belongs to another teacher. Choose a different code.")
    pdf = None
    if data.is_pdf:
        pdf = (data.pdf_url or "").strip()
        if pdf and not re.match(r"^https?://", pdf, re.I):
            pdf = "https://" + pdf
        if not re.match(r"^https?://[^\s/]+\.[^\s/]+", pdf) or len(pdf) > 600:
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Enter a valid web link for the PDF (for example https://drive.google.com/...).")
    cur.execute(
        "INSERT INTO aero_v22_exams (group_code, teacher_username, title, exam_data, pdf_url) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (code, data.teacher_username, data.title, json.dumps(data.exam_data), pdf)
    )
    exam = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "exam": exam}

def _exam_questions(raw):
    for _ in range(3):
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                return []
        else:
            break
    if isinstance(raw, dict):
        raw = raw.get("questions") or raw.get("exam_data") or []
    return [q for q in (raw or []) if isinstance(q, dict) and not q.get("_meta")]

class SubmitFuzzyModel(BaseModel):
    exam_id: int
    student_username: str
    student_name: str = ""
    answers: list = []
    time_spent_seconds: int = 0

@app.post("/api/exam/submit-fuzzy")
def submit_exam_fuzzy(data: SubmitFuzzyModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT exam_data FROM aero_v22_exams WHERE id = %s;", (data.exam_id,))
    ex = cur.fetchone()
    cur.close()
    conn.close()
    if not ex:
        raise HTTPException(status_code=404, detail="Exam not found.")
    qs = _exam_questions(ex["exam_data"])
    if not qs:
        raise HTTPException(status_code=400, detail="This exam has no questions.")
    score = 0
    total = 0
    review = []
    for i, q in enumerate(qs):
        try:
            pts = max(1, min(20, int(q.get("points", 1) or 1)))
        except Exception:
            pts = 1
        total += pts
        given = str(data.answers[i]).strip().lower() if i < len(data.answers) else ""
        right = [str(q.get("correct", "")).strip().lower()] + [str(a).strip().lower() for a in (q.get("accepted") or [])]
        if q.get("type") in ("mcq", "true_false"):
            ok = bool(given) and given == right[0]
        else:
            ok = bool(given) and any(given == r or (len(given) >= 3 and given in r) for r in right if r)
        if ok:
            score += pts
        review.append({"question": q.get("question"), "type": q.get("type"), "given": (str(data.answers[i]).strip() if i < len(data.answers) else ""),
                       "correct": q.get("correct"), "ok": ok, "points": pts})
    result = submit_exam(SubmitExamModel(exam_id=data.exam_id, student_username=data.student_username, student_name=data.student_name,
                                         score=score, total_questions=total, time_spent_seconds=min(max(data.time_spent_seconds, 0), 86400)))
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE aero_v22_exam_submissions SET answers = %s WHERE exam_id = %s AND student_username = %s;", (json.dumps(review), data.exam_id, data.student_username))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("answers not stored:", e)
    if isinstance(result, dict):
        result["score"] = score
    return result

@app.get("/api/teacher/dashboard")
def teacher_dashboard(group_code: str, teacher_username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM aero_v22_users WHERE username = %s;", (teacher_username,))
    t = cur.fetchone()
    if not t or t["role"] != "teacher":
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Teachers only.")
    cur.execute("""SELECT username, full_name, xp_points, streak, hearts, completed_nodes, last_practice_date
                   FROM aero_v22_users WHERE group_code = %s AND role = 'student' ORDER BY xp_points DESC;""", (group_code,))
    today = today_local()
    students = []
    for r in cur.fetchall():
        nodes = [n for n in (r["completed_nodes"] or []) if str(n).startswith("year1_")]
        last = r.get("last_practice_date")
        days = (today - last).days if last else None
        status = "active" if days is not None and days <= 1 else ("at_risk" if days is not None and days <= 4 else "inactive")
        students.append({"username": r["username"], "full_name": r["full_name"], "xp": r["xp_points"] or 0, "streak": r["streak"] or 0,
                         "hearts": r["hearts"], "nodes_done": len(nodes), "days_since": days, "status": status})
    cur.execute("""SELECT m.question_text, COUNT(*) AS misses, MAX(m.correct_answer) AS correct_answer
                   FROM aero_v22_mistakes m JOIN aero_v22_users u ON u.username = m.username
                   WHERE u.group_code = %s AND u.role = 'student'
                   GROUP BY m.question_text ORDER BY misses DESC LIMIT 5;""", (group_code,))
    hard = cur.fetchall()
    cur.execute("""SELECT e.title, COUNT(s.id) AS submissions,
                          ROUND(AVG(100.0 * s.score / NULLIF(s.total_questions, 0))) AS avg_pct,
                          ROUND(AVG(s.time_spent_seconds)) AS avg_seconds
                   FROM aero_v22_exams e LEFT JOIN aero_v22_exam_submissions s ON s.exam_id = e.id
                   WHERE e.teacher_username = %s GROUP BY e.id, e.title ORDER BY e.id DESC LIMIT 8;""", (teacher_username,))
    exams = cur.fetchall()
    cur.execute("""SELECT s.exam_id, e.title, s.student_name, s.student_username, s.score, s.total_questions, s.time_spent_seconds, s.submitted_at
                   FROM aero_v22_exam_submissions s JOIN aero_v22_exams e ON e.id = s.exam_id
                   WHERE e.teacher_username = %s ORDER BY s.submitted_at DESC LIMIT 60;""", (teacher_username,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    n = len(students)
    summary = {"students": n,
               "avg_xp": round(sum(x["xp"] for x in students) / n) if n else 0,
               "avg_nodes": round(sum(x["nodes_done"] for x in students) / n, 1) if n else 0,
               "active": sum(1 for x in students if x["status"] == "active"),
               "attention": sum(1 for x in students if x["status"] != "active")}
    return {"summary": summary, "students": students, "hard_questions": hard, "exams": exams, "results": results}

class LessonCreateModel(BaseModel):
    group_code: str
    teacher_username: str
    title: str
    questions: list

class LessonDeleteModel(BaseModel):
    lesson_id: int
    teacher_username: str

@app.post("/api/lesson/create")
def create_class_lesson(data: LessonCreateModel):
    title = data.title.strip()[:120]
    if not title or not data.group_code.strip():
        raise HTTPException(status_code=400, detail="A title and a class code are required.")
    if not 1 <= len(data.questions) <= 40:
        raise HTTPException(status_code=400, detail="A lesson needs between 1 and 40 questions.")
    clean = []
    for i, q in enumerate(data.questions):
        text = str(q.get("q", "")).strip()[:300]
        opts = [str(o).strip()[:160] for o in (q.get("options") or [])][:4]
        opts = [o for o in opts if o]
        c = q.get("correct")
        if not text or len(opts) < 2 or not isinstance(c, int) or not 0 <= c < len(opts):
            raise HTTPException(status_code=400, detail=f"Question {i + 1} is incomplete (needs text, 2+ options and a correct answer).")
        clean.append({"q": text, "options": opts, "correct": c})
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO aero_v22_class_lessons (group_code, teacher_username, title, questions) VALUES (%s, %s, %s, %s) RETURNING id;",
                (data.group_code.strip(), data.teacher_username, title, json.dumps(clean)))
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "id": new_id}

@app.get("/api/lesson/list")
def list_class_lessons(group_code: str, request: Request):
    auth = request.state.auth
    conn = get_db_connection()
    cur = conn.cursor()
    if auth["role"] != "teacher":
        cur.execute("SELECT group_code FROM aero_v22_users WHERE username = %s;", (auth["username"],))
        me = cur.fetchone()
        if not me or me["group_code"] != group_code:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="This is not your class.")
    cur.execute("SELECT id, title, teacher_username, questions, created_at FROM aero_v22_class_lessons WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    lessons = cur.fetchall()
    cur.close()
    conn.close()
    return {"lessons": lessons}

@app.post("/api/lesson/delete")
def delete_class_lesson(data: LessonDeleteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aero_v22_class_lessons WHERE id = %s AND teacher_username = %s;", (data.lesson_id, data.teacher_username))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

class DemoModel(BaseModel):
    group_code: str
    teacher_username: str

@app.post("/api/demo/seed")
def seed_demo(data: DemoModel):
    code = data.group_code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="A class code is required.")
    people = [("Sara Benali", 2400, 12, 38, 0, 5), ("Yassine Alaoui", 1900, 7, 27, 0, 4), ("Imane Idrissi", 1500, 4, 19, 1, 5),
              ("Omar Chraibi", 900, 0, 9, 3, 3), ("Lina Berrada", 620, 0, 5, 6, 2), ("Hamza Tazi", 150, 0, 1, None, 5)]
    pw = hash_password(os.urandom(8).hex())
    qs = [("What does ETA stand for?", "Early time alert", "Estimated time of arrival"),
          ("Which phonetic word is used for the letter B?", "Beta", "Bravo"),
          ("What should passengers do first in a decompression?", "Take off shoes", "Put on their own oxygen mask")]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM aero_v22_users WHERE group_code = %s AND phone_number LIKE 'demo-%%';", (code,))
    if cur.fetchone()["n"] == 0:
        for i, (name, xp, streak, nodes, ago, hearts) in enumerate(people, 1):
            uname = f"demo_{i}_{code}"[:50]
            last = (today_local() - timedelta(days=ago)) if ago is not None else None
            cur.execute("""INSERT INTO aero_v22_users (phone_number, username, full_name, password, recovery_pin, role, group_code,
                           xp_points, hearts, streak, completed_nodes, last_practice_date)
                           VALUES (%s, %s, %s, %s, '0000', 'student', %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;""",
                        (f"demo-{code}-{i}"[:20], uname, name, pw, code, xp, hearts, streak, [f"year1_{n}" for n in range(1, nodes + 1)], last))
            for k, (q, wrong, right) in enumerate(qs):
                if (i + k) % 3 != 0:
                    cur.execute("INSERT INTO aero_v22_mistakes (username, question_text, incorrect_answer, correct_answer) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                                (uname, q, wrong, right))
        lesson = [{"q": q, "options": [wrong, right], "correct": 1} for q, wrong, right in qs]
        cur.execute("INSERT INTO aero_v22_class_lessons (group_code, teacher_username, title, questions) VALUES (%s, %s, %s, %s);",
                    (code, data.teacher_username, "Demo: Cabin crew basics", json.dumps(lesson)))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/demo/clear")
def clear_demo(data: DemoModel):
    code = data.group_code.strip()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aero_v22_mistakes WHERE username IN (SELECT username FROM aero_v22_users WHERE group_code = %s AND phone_number LIKE 'demo-%%');", (code,))
    cur.execute("DELETE FROM aero_v22_users WHERE group_code = %s AND phone_number LIKE 'demo-%%';", (code,))
    cur.execute("DELETE FROM aero_v22_class_lessons WHERE group_code = %s AND title LIKE 'Demo:%%';", (code,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/overview")
def admin_overview():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, full_name, role, group_code, xp_points, completed_nodes, last_practice_date FROM aero_v22_users;")
    users = cur.fetchall()
    cur.execute("SELECT group_code, group_name, teacher_username FROM aero_v22_groups;")
    groups = {g["group_code"]: g for g in cur.fetchall()}
    cur.execute("SELECT teacher_username, COUNT(*) AS c FROM aero_v22_class_lessons GROUP BY teacher_username;")
    lessons = {r["teacher_username"]: r["c"] for r in cur.fetchall()}
    cur.execute("SELECT teacher_username, COUNT(*) AS c FROM aero_v22_exams GROUP BY teacher_username;")
    exams = {r["teacher_username"]: r["c"] for r in cur.fetchall()}
    cur.close()
    conn.close()
    today = today_local()
    students = [u for u in users if u["role"] == "student"]
    teachers = [u for u in users if u["role"] == "teacher"]
    nodes = lambda u: len([n for n in (u["completed_nodes"] or []) if str(n).startswith("year1_")])
    active = lambda u: bool(u["last_practice_date"]) and (today - u["last_practice_date"]).days <= 6
    by_class = {}
    for u in students:
        by_class.setdefault(u["group_code"] or "-", []).append(u)
    classes = []
    for code, members in by_class.items():
        g = groups.get(code, {})
        classes.append({"group_code": code, "group_name": g.get("group_name") or ("Class " + code), "teacher": g.get("teacher_username"),
                        "students": len(members), "active_7d": sum(1 for m in members if active(m)),
                        "avg_nodes": round(sum(nodes(m) for m in members) / len(members), 1),
                        "avg_xp": round(sum((m["xp_points"] or 0) for m in members) / len(members))})
    classes.sort(key=lambda c: -c["students"])
    teacher_rows = [{"username": t["username"], "full_name": t["full_name"],
                     "students": len(by_class.get(t["group_code"], [])), "lessons": lessons.get(t["username"], 0), "exams": exams.get(t["username"], 0)} for t in teachers]
    activity = [{"days_ago": d, "students": sum(1 for u in students if u["last_practice_date"] == today - timedelta(days=d))} for d in range(6, -1, -1)]
    top = sorted(students, key=lambda u: -(u["xp_points"] or 0))[:5]
    return {"totals": {"students": len(students), "teachers": len(teachers), "classes": len(classes), "active_7d": sum(1 for u in students if active(u)),
                       "avg_nodes": round(sum(nodes(u) for u in students) / len(students), 1) if students else 0},
            "classes": classes, "teachers": teacher_rows, "activity": activity,
            "top": [{"full_name": u["full_name"], "xp": u["xp_points"] or 0, "group_code": u["group_code"]} for u in top]}

class AnnounceModel(BaseModel):
    group_code: str
    teacher_username: str
    message: str

class AnnounceDeleteModel(BaseModel):
    announcement_id: int
    teacher_username: str

@app.post("/api/announce/create")
def create_announcement(data: AnnounceModel):
    msg = data.message.strip()[:280]
    if not msg or not data.group_code.strip():
        raise HTTPException(status_code=400, detail="Write a message first.")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS n FROM aero_v22_announcements WHERE teacher_username = %s AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';", (data.teacher_username,))
    if cur.fetchone()["n"] >= 10:
        cur.close()
        conn.close()
        raise HTTPException(status_code=429, detail="Too many announcements in the last hour.")
    cur.execute("INSERT INTO aero_v22_announcements (group_code, teacher_username, message) VALUES (%s, %s, %s);", (data.group_code.strip(), data.teacher_username, msg))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/announce/latest")
def latest_announcements(group_code: str, request: Request):
    auth = request.state.auth
    conn = get_db_connection()
    cur = conn.cursor()
    if auth["role"] != "teacher":
        cur.execute("SELECT group_code FROM aero_v22_users WHERE username = %s;", (auth["username"],))
        me = cur.fetchone()
        group_code = (me or {}).get("group_code") or "-"
    codes = [group_code, "*TEACHERS*" if auth["role"] == "teacher" else "*STUDENTS*"]
    cur.execute("SELECT id, teacher_username, message, created_at FROM aero_v22_announcements WHERE group_code = ANY(%s) ORDER BY id DESC LIMIT 5;", (codes,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"announcements": rows}

@app.post("/api/announce/delete")
def delete_announcement(data: AnnounceDeleteModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aero_v22_announcements WHERE id = %s AND teacher_username = %s;", (data.announcement_id, data.teacher_username))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/league/class")
def class_league(group_code: str, request: Request):
    auth = request.state.auth
    conn = get_db_connection()
    cur = conn.cursor()
    if auth["role"] != "teacher":
        cur.execute("SELECT group_code FROM aero_v22_users WHERE username = %s;", (auth["username"],))
        me = cur.fetchone()
        if not me or me["group_code"] != group_code:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="This is not your class.")
    today = today_local()
    monday = today - timedelta(days=today.weekday())
    cur.execute("SELECT username, full_name, xp_points, streak FROM aero_v22_users WHERE group_code = %s AND role = 'student';", (group_code,))
    members = cur.fetchall()
    for m in members:
        cur.execute("INSERT INTO aero_v22_weekly_xp (username, week_start, start_xp) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;",
                    (m["username"], monday, m["xp_points"] or 0))
    conn.commit()
    names = [m["username"] for m in members]
    base = {}
    if names:
        cur.execute("SELECT username, start_xp FROM aero_v22_weekly_xp WHERE week_start = %s AND username = ANY(%s);", (monday, names))
        base = {r["username"]: r["start_xp"] for r in cur.fetchall()}
    cur.close()
    conn.close()
    rows = [{"username": m["username"], "full_name": m["full_name"], "xp": m["xp_points"] or 0, "streak": m["streak"] or 0,
             "week_xp": max(0, (m["xp_points"] or 0) - base.get(m["username"], m["xp_points"] or 0))} for m in members]
    rows.sort(key=lambda r: (-r["week_xp"], -r["xp"]))
    return {"week_start": str(monday), "days_left": 6 - today.weekday(), "members": rows}

class SetCodeModel(BaseModel):
    teacher_username: str
    new_code: str

@app.post("/api/teacher/set-code")
def set_class_code(data: SetCodeModel):
    import re
    new = data.new_code.strip().upper()
    if new and not re.fullmatch(r"[A-Z0-9_-]{3,20}", new):
        raise HTTPException(status_code=400, detail="Use 3-20 letters, numbers, - or _.")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_code FROM aero_v22_users WHERE username = %s;", (data.teacher_username,))
    me = cur.fetchone()
    old = (me or {}).get("group_code") or ""
    if new == "":
        if old:
            cur.execute("UPDATE aero_v22_users SET group_code = '' WHERE group_code = %s;", (old,))
            cur.execute("DELETE FROM aero_v22_groups WHERE group_code = %s AND teacher_username = %s;", (old, data.teacher_username))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "group_code": ""}
    if new != old:
        cur.execute("SELECT 1 FROM aero_v22_groups WHERE group_code = %s AND teacher_username <> %s;", (new, data.teacher_username))
        taken = cur.fetchone()
        cur.execute("SELECT 1 FROM aero_v22_users WHERE group_code = %s AND role = 'teacher' AND username <> %s;", (new, data.teacher_username))
        if taken or cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(status_code=409, detail="This code is already used by another class. Try a different one.")
        if old:
            cur.execute("UPDATE aero_v22_groups SET group_code = %s WHERE group_code = %s AND teacher_username = %s;", (new, old, data.teacher_username))
            cur.execute("UPDATE aero_v22_users SET group_code = %s WHERE group_code = %s;", (new, old))
            for table in ("aero_v22_exams", "aero_v22_class_lessons", "aero_v22_announcements"):
                cur.execute("UPDATE " + table + " SET group_code = %s WHERE group_code = %s;", (new, old))
        cur.execute("UPDATE aero_v22_users SET group_code = %s WHERE username = %s;", (new, data.teacher_username))
        cur.execute("INSERT INTO aero_v22_groups (group_name, group_code, teacher_username) VALUES (%s, %s, %s) ON CONFLICT (group_code) DO NOTHING;",
                    ("Class " + new, new, data.teacher_username))
        conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "group_code": new}

class ResetSubmissionModel(BaseModel):
    exam_id: int
    student_username: str
    teacher_username: str

@app.post("/api/exam/reset-submission")
def reset_submission(data: ResetSubmissionModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aero_v22_exam_submissions WHERE exam_id = %s AND student_username = %s AND exam_id IN (SELECT id FROM aero_v22_exams WHERE teacher_username = %s);",
                (data.exam_id, data.student_username, data.teacher_username))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/exam/review")
def exam_review(exam_id: int, student: str, request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT s.answers, s.score, s.total_questions, s.student_name, e.title
                   FROM aero_v22_exam_submissions s JOIN aero_v22_exams e ON e.id = s.exam_id
                   WHERE s.exam_id = %s AND s.student_username = %s AND e.teacher_username = %s;""", (exam_id, student, me))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Result not found.")
    ans = row["answers"]
    if isinstance(ans, str):
        ans = json.loads(ans)
    return {"title": row["title"], "student": row["student_name"], "score": row["score"], "total": row["total_questions"], "review": ans or []}

WHEEL = [("100 XP ⭐", "xp", 100, 4), ("Pilot Hat 🧢", "skin", "Captain Pilot Hat", 2), ("50 XP ⭐", "xp", 50, 12), ("5 Hearts ❤", "hearts", 5, 8),
         ("25 XP ⭐", "xp", 25, 20), ("0 XP 😢", "xp", 0, 22), ("2 Hearts ❤", "hearts", 2, 14), ("10 XP ⭐", "xp", 10, 18)]

@app.post("/api/wheel/spin")
def wheel_spin(request: Request):
    import time
    me = request.state.auth["username"]
    now = int(time.time() * 1000)
    day = 24 * 60 * 60 * 1000
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_users SET last_spin_timestamp = %s WHERE username = %s AND COALESCE(last_spin_timestamp, 0) <= %s RETURNING id;", (now, me, now - day))
    if not cur.fetchone():
        cur.execute("SELECT last_spin_timestamp FROM aero_v22_users WHERE username = %s;", (me,))
        row = cur.fetchone() or {}
        cur.close()
        conn.close()
        raise HTTPException(status_code=429, detail="One spin every 24 hours. Come back later!")
    idx = random.choices(range(len(WHEEL)), weights=[w[3] for w in WHEEL])[0]
    text, kind, val, _ = WHEEL[idx]
    if kind == "xp" and val:
        cur.execute("UPDATE aero_v22_users SET xp_points = xp_points + %s WHERE username = %s;", (val, me))
    elif kind == "hearts":
        cur.execute("UPDATE aero_v22_users SET hearts = LEAST(5, COALESCE(hearts, 5) + %s) WHERE username = %s;", (val, me))
    elif kind == "skin":
        cur.execute("UPDATE aero_v22_users SET active_skin = %s WHERE username = %s;", (val, me))
        cur.execute("INSERT INTO aero_v22_owned_skins (username, skin_name_en) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (me, val))
    cur.execute("SELECT * FROM aero_v22_users WHERE username = %s;", (me,))
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"index": idx, "prize": {"text": text, "type": kind, "val": val}, "user": user}

def add_months(d, n):
    import calendar
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))

def pay_status(paid_until, remind_days):
    if not paid_until:
        return "none", None
    left = (paid_until - today_local()).days
    return ("overdue" if left < 0 else "due_soon" if left <= (remind_days if remind_days is not None else 3) else "paid"), left

class PaymentUpdateModel(BaseModel):
    student: str
    action: str = "save"
    months: int = 1
    paid_until: str = None
    monthly_fee: int = None
    remind_days: int = None
    message: str = None

@app.get("/api/admin/payments")
def admin_payments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT u.username, u.full_name, u.group_code, u.phone_number, p.paid_until, p.monthly_fee, p.remind_days, p.message
                   FROM aero_v22_users u LEFT JOIN aero_v22_payments p ON p.username = u.username
                   WHERE u.role = 'student' ORDER BY u.full_name;""")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for r in rows:
        r["status"], r["days_left"] = pay_status(r["paid_until"], r["remind_days"])
    return {"students": rows}

@app.post("/api/admin/payments/update")
def admin_payments_update(data: PaymentUpdateModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM aero_v22_users WHERE username = %s AND role = 'student';", (data.student,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found.")
    cur.execute("SELECT * FROM aero_v22_payments WHERE username = %s;", (data.student,))
    row = cur.fetchone() or {}
    paid_until, fee, rem, msg = row.get("paid_until"), row.get("monthly_fee"), row.get("remind_days"), row.get("message")
    today = today_local()
    if data.action == "paid":
        base = paid_until if paid_until and paid_until >= today else today
        paid_until = add_months(base, max(1, min(12, data.months)))
    elif data.paid_until:
        try:
            paid_until = datetime.strptime(data.paid_until, "%Y-%m-%d").date()
        except Exception:
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="Use the date format YYYY-MM-DD.")
    if data.monthly_fee is not None:
        fee = max(0, min(100000, data.monthly_fee))
    if data.remind_days is not None:
        rem = max(0, min(30, data.remind_days))
    if data.message is not None:
        msg = data.message.strip()[:300]
    if data.action == "paid":
        cur.execute("INSERT INTO aero_v22_payment_log (username, amount, months) VALUES (%s, %s, %s);", (data.student, (fee or 0) * max(1, min(12, data.months)), max(1, min(12, data.months))))
    cur.execute("""INSERT INTO aero_v22_payments (username, paid_until, monthly_fee, remind_days, message, updated_at)
                   VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (username) DO UPDATE SET paid_until = EXCLUDED.paid_until, monthly_fee = EXCLUDED.monthly_fee,
                   remind_days = EXCLUDED.remind_days, message = EXCLUDED.message, updated_at = CURRENT_TIMESTAMP;""",
                (data.student, paid_until, fee, 3 if rem is None else rem, msg))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "paid_until": str(paid_until) if paid_until else None}

@app.get("/api/payments/mine")
def my_payment(request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aero_v22_payments WHERE username = %s;", (me,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"status": "none"}
    st, left = pay_status(row["paid_until"], row["remind_days"])
    return {"status": st, "days_left": left, "paid_until": str(row["paid_until"]) if row["paid_until"] else None,
            "fee": row["monthly_fee"], "message": row["message"], "remind_days": row["remind_days"]}

class BroadcastModel(BaseModel):
    audience: str
    message: str

class CapacityModel(BaseModel):
    group_code: str
    capacity: int

@app.post("/api/admin/broadcast")
def admin_broadcast(data: BroadcastModel, request: Request):
    msg = data.message.strip()[:280]
    targets = {"students": ["*STUDENTS*"], "teachers": ["*TEACHERS*"], "all": ["*STUDENTS*", "*TEACHERS*"]}.get(data.audience)
    if not msg or not targets:
        raise HTTPException(status_code=400, detail="Write a message and choose who receives it.")
    conn = get_db_connection()
    cur = conn.cursor()
    for t in targets:
        cur.execute("INSERT INTO aero_v22_announcements (group_code, teacher_username, message) VALUES (%s, %s, %s);", (t, request.state.auth["username"], msg))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.post("/api/admin/class-capacity")
def admin_capacity(data: CapacityModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE aero_v22_groups SET capacity = %s WHERE group_code = %s;", (max(1, min(500, data.capacity)), data.group_code))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/attendance")
def admin_attendance(group_code: str, month: str):
    import calendar
    try:
        start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Use the month format YYYY-MM.")
    end = add_months(start, 1)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, full_name FROM aero_v22_users WHERE role = 'student' AND group_code = %s ORDER BY full_name;", (group_code,))
    studs = cur.fetchall()
    days = {}
    if studs:
        cur.execute("SELECT username, day FROM aero_v22_activity WHERE day >= %s AND day < %s AND username = ANY(%s);", (start, end, [x["username"] for x in studs]))
        for r in cur.fetchall():
            days.setdefault(r["username"], []).append(r["day"].day)
    cur.close()
    conn.close()
    return {"days_in_month": calendar.monthrange(start.year, start.month)[1],
            "students": [{"username": x["username"], "full_name": x["full_name"], "days": sorted(days.get(x["username"], []))} for x in studs]}

@app.get("/api/admin/reports")
def admin_reports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT u.username, u.full_name, u.role, u.group_code, u.phone_number, u.completed_nodes, u.last_practice_date, u.created_at,
                          p.paid_until, p.monthly_fee, p.remind_days FROM aero_v22_users u LEFT JOIN aero_v22_payments p ON p.username = u.username;""")
    users = cur.fetchall()
    cur.execute("SELECT group_code, group_name, capacity, teacher_username FROM aero_v22_groups;")
    groups = {g["group_code"]: g for g in cur.fetchall()}
    counts = {}
    for q, key in (("SELECT teacher_username, COUNT(*) AS c FROM aero_v22_exams GROUP BY teacher_username;", "exams"),
                   ("SELECT teacher_username, COUNT(*) AS c FROM aero_v22_announcements GROUP BY teacher_username;", "ann"),
                   ("SELECT teacher_username, COUNT(*) AS c FROM aero_v22_class_lessons GROUP BY teacher_username;", "lessons")):
        cur.execute(q)
        counts[key] = {r["teacher_username"]: r["c"] for r in cur.fetchall()}
    today = today_local()
    month_start = today.replace(day=1)
    month_end = add_months(month_start, 1) - timedelta(days=1)
    cur.execute("SELECT COALESCE(SUM(amount), 0) AS t FROM aero_v22_payment_log WHERE paid_at >= %s;", (month_start,))
    collected = int(cur.fetchone()["t"])
    cur.close()
    conn.close()
    students = [u for u in users if u["role"] == "student"]
    due = overdue = 0
    due_week, inactive, new_regs, certs = [], [], [], []
    for u in students:
        fee = u["monthly_fee"] or 0
        st, left = pay_status(u["paid_until"], u["remind_days"])
        if u["paid_until"] and u["paid_until"] <= month_end:
            due += fee
        if st == "overdue":
            overdue += fee
        base = {"username": u["username"], "full_name": u["full_name"], "phone": u["phone_number"], "group_code": u["group_code"]}
        if u["paid_until"] and u["paid_until"] <= today + timedelta(days=7):
            due_week.append(dict(base, days_left=left, paid_until=str(u["paid_until"]), fee=fee))
        last = u["last_practice_date"]
        if not last or (today - last).days >= 7:
            inactive.append(dict(base, days=(today - last).days if last else None))
        if u["created_at"] and u["created_at"].date() >= today - timedelta(days=7):
            new_regs.append(dict(base, created=str(u["created_at"].date())))
        nodes = [str(n) for n in (u["completed_nodes"] or [])]
        y1, y2 = sum(1 for n in nodes if n.startswith("year1_")), sum(1 for n in nodes if n.startswith("year2_"))
        for path, k in (("First Year Path", y1), ("Second Year Path", y2)):
            if k >= 100:
                certs.append(dict(base, path=path))
    classes = {}
    for u in students:
        classes.setdefault(u["group_code"] or "-", 0)
        classes[u["group_code"] or "-"] += 1
    class_rows = [{"group_code": c, "name": (groups.get(c) or {}).get("group_name") or ("Class " + c), "students": n, "capacity": (groups.get(c) or {}).get("capacity") or 30} for c, n in classes.items()]
    teachers = [{"username": t["username"], "full_name": t["full_name"], "students": classes.get(t["group_code"], 0), "exams": counts["exams"].get(t["username"], 0),
                 "announcements": counts["ann"].get(t["username"], 0), "lessons": counts["lessons"].get(t["username"], 0)} for t in users if t["role"] == "teacher"]
    return {"money": {"collected": collected, "due": due, "overdue": overdue, "month": str(month_start)[:7]},
            "totals": {"students": len(students), "teachers": len(teachers), "classes": len(class_rows)},
            "due_week": due_week, "inactive": sorted(inactive, key=lambda x: -(x["days"] or 999)), "new_regs": new_regs, "classes": class_rows, "teachers": teachers, "certificates": certs}

class AttGroupModel(BaseModel):
    name: str
    students: list = []
    group_id: int = None

class AttDeleteModel(BaseModel):
    group_id: int

class AttMarkModel(BaseModel):
    group_id: int
    roster_id: int
    status: str
    day: str = None

def _own_group(cur, group_id, me):
    cur.execute("SELECT id, name FROM aero_v22_att_groups WHERE id = %s AND teacher_username = %s;", (group_id, me))
    g = cur.fetchone()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found.")
    return g

def _label(name, nick):
    return name + (' \u201c' + nick + '\u201d' if nick else "")

@app.get("/api/attendance/groups")
def att_groups(request: Request):
    me = request.state.auth["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM aero_v22_att_groups WHERE teacher_username = %s ORDER BY id;", (me,))
    groups = cur.fetchall()
    roster = {}
    if groups:
        cur.execute("SELECT id, group_id, name, nickname FROM aero_v22_att_roster WHERE group_id = ANY(%s) ORDER BY name;", ([g["id"] for g in groups],))
        for r in cur.fetchall():
            roster.setdefault(r["group_id"], []).append({"id": r["id"], "name": r["name"], "nickname": r["nickname"] or ""})
    cur.close()
    conn.close()
    for g in groups:
        g["students"] = roster.get(g["id"], [])
    return {"groups": groups}

@app.post("/api/attendance/group/save")
def att_group_save(data: AttGroupModel, request: Request):
    me = request.state.auth["username"]
    name = data.name.strip()[:80]
    if not name:
        raise HTTPException(status_code=400, detail="Give the group a name.")
    rows = []
    for st in data.students[:300]:
        if not isinstance(st, dict):
            continue
        nm = str(st.get("name", "")).strip()[:80]
        if nm:
            rows.append((st.get("id") if isinstance(st.get("id"), int) else None, nm, str(st.get("nickname") or "").strip()[:40]))
    conn = get_db_connection()
    cur = conn.cursor()
    if data.group_id:
        _own_group(cur, data.group_id, me)
        cur.execute("UPDATE aero_v22_att_groups SET name = %s WHERE id = %s;", (name, data.group_id))
        gid = data.group_id
    else:
        cur.execute("INSERT INTO aero_v22_att_groups (teacher_username, name) VALUES (%s, %s) RETURNING id;", (me, name))
        gid = cur.fetchone()["id"]
    cur.execute("SELECT id FROM aero_v22_att_roster WHERE group_id = %s;", (gid,))
    existing = {r["id"] for r in cur.fetchall()}
    keep = {r[0] for r in rows if r[0] in existing}
    for rid in existing - keep:
        cur.execute("DELETE FROM aero_v22_att_marks WHERE roster_id = %s;", (rid,))
        cur.execute("DELETE FROM aero_v22_att_roster WHERE id = %s;", (rid,))
    for rid, nm, nick in rows:
        if rid in existing:
            cur.execute("UPDATE aero_v22_att_roster SET name = %s, nickname = %s WHERE id = %s AND group_id = %s;", (nm, nick, rid, gid))
        else:
            cur.execute("INSERT INTO aero_v22_att_roster (group_id, name, nickname) VALUES (%s, %s, %s);", (gid, nm, nick))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "id": gid}

@app.post("/api/attendance/group/delete")
def att_group_delete(data: AttDeleteModel, request: Request):
    conn = get_db_connection()
    cur = conn.cursor()
    _own_group(cur, data.group_id, request.state.auth["username"])
    cur.execute("DELETE FROM aero_v22_att_marks WHERE roster_id IN (SELECT id FROM aero_v22_att_roster WHERE group_id = %s);", (data.group_id,))
    cur.execute("DELETE FROM aero_v22_att_roster WHERE group_id = %s;", (data.group_id,))
    cur.execute("DELETE FROM aero_v22_att_groups WHERE id = %s;", (data.group_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/attendance/roll")
def att_roll(group_id: int, request: Request, day: str = None):
    me = request.state.auth["username"]
    d = datetime.strptime(day, "%Y-%m-%d").date() if day else today_local()
    conn = get_db_connection()
    cur = conn.cursor()
    g = _own_group(cur, group_id, me)
    cur.execute("""SELECT r.id, r.name, r.nickname, m.status FROM aero_v22_att_roster r
                   LEFT JOIN aero_v22_att_marks m ON m.roster_id = r.id AND m.day = %s
                   WHERE r.group_id = %s ORDER BY r.name;""", (d, group_id))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"group": g, "day": str(d), "students": rows}

@app.post("/api/attendance/mark")
def att_mark(data: AttMarkModel, request: Request):
    me = request.state.auth["username"]
    if data.status not in ("present", "absent", "late"):
        raise HTTPException(status_code=400, detail="Invalid status.")
    d = datetime.strptime(data.day, "%Y-%m-%d").date() if data.day else today_local()
    if d > today_local():
        raise HTTPException(status_code=400, detail="You cannot mark a future date.")
    conn = get_db_connection()
    cur = conn.cursor()
    _own_group(cur, data.group_id, me)
    cur.execute("SELECT 1 FROM aero_v22_att_roster WHERE id = %s AND group_id = %s;", (data.roster_id, data.group_id))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="This student is not in the group.")
    cur.execute("""INSERT INTO aero_v22_att_marks (roster_id, day, status, marked_by, marked_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (roster_id, day) DO UPDATE SET status = EXCLUDED.status, marked_by = EXCLUDED.marked_by, marked_at = CURRENT_TIMESTAMP;""",
                (data.roster_id, d, data.status, me))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/roll")
def admin_roll(day: str = None):
    d = datetime.strptime(day, "%Y-%m-%d").date() if day else today_local()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT g.id, g.name, g.teacher_username, (SELECT COUNT(*) FROM aero_v22_att_roster r WHERE r.group_id = g.id) AS total FROM aero_v22_att_groups g ORDER BY g.name;")
    groups = cur.fetchall()
    cur.execute("""SELECT r.group_id, r.name, r.nickname, m.status, m.marked_at FROM aero_v22_att_marks m JOIN aero_v22_att_roster r ON r.id = m.roster_id
                   WHERE m.day = %s ORDER BY r.name;""", (d,))
    recs = {}
    for r in cur.fetchall():
        recs.setdefault(r["group_id"], []).append({"full_name": _label(r["name"], r["nickname"]), "status": r["status"], "time": r["marked_at"].strftime("%H:%M") if r["marked_at"] else ""})
    cur.close()
    conn.close()
    for g in groups:
        rr = recs.get(g["id"], [])
        g.update({"records": rr, "present": sum(1 for x in rr if x["status"] == "present"), "absent": sum(1 for x in rr if x["status"] == "absent"), "late": sum(1 for x in rr if x["status"] == "late")})
    return {"day": str(d), "groups": groups}

@app.get("/api/admin/roll-month")
def admin_roll_month(group_id: int, month: str):
    import calendar
    start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    end = add_months(start, 1)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, nickname FROM aero_v22_att_roster WHERE group_id = %s ORDER BY name;", (group_id,))
    studs = cur.fetchall()
    cur.execute("""SELECT m.roster_id, m.day, m.status FROM aero_v22_att_marks m JOIN aero_v22_att_roster r ON r.id = m.roster_id
                   WHERE r.group_id = %s AND m.day >= %s AND m.day < %s;""", (group_id, start, end))
    marks = {}
    for r in cur.fetchall():
        marks.setdefault(r["roster_id"], {})[r["day"].day] = r["status"]
    cur.close()
    conn.close()
    return {"days_in_month": calendar.monthrange(start.year, start.month)[1], "students": [{"full_name": _label(x["name"], x["nickname"]), "marks": marks.get(x["id"], {})} for x in studs]}

@app.get("/manifest.json")
def serve_manifest():
    return FileResponse("manifest.json", media_type="application/manifest+json")

@app.get("/sw.js")
def serve_service_worker():
    return FileResponse("sw.js", media_type="application/javascript", headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

@app.get("/icon-192.png")
def serve_icon_192():
    return FileResponse("icon-192.png")

@app.get("/icon-512.png")
def serve_icon_512():
    return FileResponse("icon-512.png")

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
