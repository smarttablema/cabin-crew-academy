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

app = FastAPI(title="AeroCrew Pro Academy Elite", version="4.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crew_students_v4 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            xp_points INT DEFAULT 150,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS official_modules_v4 (
            id SERIAL PRIMARY KEY,
            title_en VARCHAR(150),
            title_ar VARCHAR(150),
            title_fr VARCHAR(150),
            category VARCHAR(50),
            content_en TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS official_drills_v4 (
            id SERIAL PRIMARY KEY,
            term_en VARCHAR(100),
            term_ar VARCHAR(100),
            term_fr VARCHAR(100),
            category VARCHAR(50),
            hint_en TEXT
        );
    """)
    # Seed official accredited EASA / ICAO cabin crew curriculum with fixed column names
    cur.execute("""
        INSERT INTO official_modules_v4 (title_en, title_ar, title_fr, category, content_en)
        VALUES 
        ('SEP: Emergency Evacuation & Brace Positions', 'إجراءات الإخلاء الطارئ ووضعيات الاستعداد', 'Procédures d évacuation d urgence', 'SEP', 'During an emergency water or land landing, cabin crew must immediately yell commanding brace commands, assess exit conditions for fire or water hazards, and deploy slides within 90 seconds.'),
        ('Dangerous Goods (Hazmat) Handling', 'التعامل مع البضائع الخطرة', 'Gestion des marchandises dangereuses', 'Cargo/DG', 'Lithium battery thermal runaways in cabin overhead bins require immediate cooling with water or specialized fire extinguishers following strict airline dangerous goods protocols.'),
        ('Aeromedical First Aid & Hypoxia', 'الإسعافات الأولية ونقص الأكسجين', 'Premiers secours aéromédicaux', 'Medical', 'Rapid decompression causes hypoxia symptoms including tunnel vision and euphoria. Crew must don portable oxygen bottles immediately before assisting incapacitated passengers.')
        ON CONFLICT DO NOTHING;
    """)
    cur.execute("""
        INSERT INTO official_drills_v4 (term_en, term_ar, term_fr, category, hint_en)
        VALUES 
        ('Altimeter', 'مقياس الارتفاع', 'Altimètre', 'Instruments', 'Measures barometric altitude above sea level.'),
        ('Bulkhead', 'الجدار الفاصل', 'Cloison', 'Cabin', 'Structural partition dividing cabin zones.'),
        ('Decompression', 'إزالة الضغط', 'Décompression', 'Emergency', 'Loss of cabin pressurization at cruising altitude.'),
        ('Turbulence', 'مطبات هوائية', 'Turbulence', 'Meteorology', 'Unsteady atmospheric air currents causing bumps.'),
        ('Evacuation', 'إخلاء الطائرة', 'Évacuation', 'SEP', 'Emergency rapid exit of all passengers.'),
        ('Brace', 'وضعية الاستعداد', 'Position de sécurité', 'SEP', 'Protective crash position for passengers.')
        ON CONFLICT DO NOTHING;
    """)
    conn.commit()
    cur.close()
    conn.close()

class RegisterModel(BaseModel):
    phone_number: str
    full_name: str
    password: str
    recovery_pin: str

class LoginModel(BaseModel):
    phone_number: str
    password: str

class ResetModel(BaseModel):
    phone_number: str
    recovery_pin: str
    new_password: str

class DrillAttemptModel(BaseModel):
    phone_number: str
    drill_id: int
    user_answer: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crew_students_v4 WHERE phone_number = %s;", (data.phone_number,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered.")
    
    cur.execute(
        "INSERT INTO crew_students_v4 (phone_number, full_name, password, recovery_pin) VALUES (%s, %s, %s, %s) RETURNING *;",
        (data.phone_number, data.full_name, data.password, data.recovery_pin)
    )
    student = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "student": student}

@app.post("/api/login")
def login(data: LoginModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crew_students_v4 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
    student = cur.fetchone()
    cur.close()
    conn.close()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return {"status": "success", "student": student}

@app.post("/api/reset")
def reset_pass(data: ResetModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crew_students_v4 WHERE phone_number = %s AND recovery_pin = %s;", (data.phone_number, data.recovery_pin))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid recovery PIN.")
    cur.execute("UPDATE crew_students_v4 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/academy/data")
def get_academy_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM official_modules_v4 ORDER BY id ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM official_drills_v4 ORDER BY id ASC;")
    drills = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "drills": drills}

@app.post("/api/drill/verify")
def verify_drill(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM official_drills_v4 WHERE id = %s;", (data.drill_id,))
    drill = cur.fetchone()
    cur.execute("SELECT * FROM crew_students_v4 WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    
    if not drill or not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found.")
    
    correct_term = drill["term_en"].strip().lower()
    user_input = data.user_answer.strip().lower()
    
    similarity = difflib.SequenceMatcher(None, user_input, correct_term).ratio()
    
    if user_input == correct_term:
        cur.execute("UPDATE crew_students_v4 SET xp_points = xp_points + 25 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "typo_detected": False, "message": "Perfect execution! +25 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    elif similarity >= 0.78:
        cur.execute("UPDATE crew_students_v4 SET xp_points = xp_points + 15 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "typo_detected": True, "message": f"Accepted with minor typo! Official spelling: '{drill['term_en']}'. +15 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    else:
        new_hearts = max(0, student["hearts"] - 1)
        cur.execute("UPDATE crew_students_v4 SET hearts = %s WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (new_hearts, data.phone_number))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": False, "typo_detected": False, "message": f"Incorrect! Official standard term is '{drill['term_en']}'. Heart lost!", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AeroCrew Pro Academy | Elite Aviation Training</title>
    <link rel="icon" href="https://img.icons8.com/color/48/airplane-take-off.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #030712;
            --surface: #0f172a;
            --surface-card: #1e293b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.25);
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        
        .app-shell { width: 100%; max-width: 500px; background: var(--surface); border-radius: 28px; padding: 2rem; border: 1px solid var(--border); box-shadow: 0 35px 70px rgba(0, 0, 0, 0.85); position: relative; overflow: hidden; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.8rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.1rem; color: var(--accent); }
        .brand-title img { width: 32px; height: 32px; }
        
        .lang-switch { display: flex; gap: 6px; }
        .lang-badge { background: var(--surface-card); border: 1px solid var(--border); border-radius: 8px; padding: 4px 8px; font-size: 0.7rem; font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-badge.active, .lang-badge:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.35rem; }
        p.sub-desc { font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.4; }
        
        label { display: block; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.5px; }
        input { width: 100%; padding: 0.9rem 1rem; border-radius: 14px; border: 1px solid var(--border); background: var(--bg-deep); color: white; font-size: 0.95rem; margin-bottom: 1.1rem; outline: none; transition: all 0.2s; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 0.95rem; border-radius: 14px; border: none; background: var(--accent); color: var(--bg-deep); font-weight: 800; font-size: 0.95rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s; box-shadow: 0 4px 14px var(--accent-glow); }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.92; }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; font-size: 0.8rem; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 600; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.9rem 1.2rem; border-radius: 16px; border: 1px solid var(--border); margin-bottom: 1.2rem; }
        .stat-item { font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; gap: 5px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.2rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.2s; }
        .mode-tile:hover { border-color: var(--accent); background: var(--accent-glow); transform: translateY(-2px); }
        .mode-tile h4 { font-size: 0.88rem; font-weight: 700; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 20px; padding: 1.5rem; border: 1px solid var(--border); margin-bottom: 1rem; position: relative; }
        
        .mic-circle { width: 75px; height: 75px; border-radius: 50%; background: var(--accent); border: none; display: flex; justify-content: center; align-items: center; margin: 1.5rem auto 1rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s; }
        .mic-circle.recording { background: var(--danger); animation: pulseAnim 1.5s infinite; }
        @keyframes pulseAnim { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); } 70% { box-shadow: 0 0 0 22px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 12px 24px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 2000; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Icon">
                <span>AeroCrew Pro</span>
            </div>
            <div class="lang-switch">
                <button class="lang-badge active" onclick="setLanguage('en')">EN</button>
                <button class="lang-badge" onclick="setLanguage('fr')">FR</button>
                <button class="lang-badge" onclick="setLanguage('ar')">AR</button>
            </div>
        </div>

        <div id="screen-login">
            <h2 id="ui-login-title">Cabin Crew Portal</h2>
            <p class="sub-desc" id="ui-login-sub">Access accredited EASA/ICAO simulation modules.</p>
            
            <label>Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn-action" onclick="submitLogin()" id="ui-login-btn">Sign In to Simulator</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-register')">Create Account</a>
                <a onclick="navigateTo('screen-reset')">Forgot Password?</a>
            </div>
        </div>

        <div id="screen-register" class="hidden">
            <h2>Cadet Enrollment</h2>
            <p class="sub-desc">Register your official student training profile.</p>
            
            <label>Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label>Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label>Recovery PIN (4-6 digits)</label>
            <input type="password" id="reg-pin" placeholder="e.g. 2026" maxlength="6" />
            
            <button class="btn-action" onclick="submitRegister()" style="background: var(--success); color: white;">Initialize Profile</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-login')">Already have an account? Sign In</a>
            </div>
        </div>

        <div id="screen-reset" class="hidden">
            <h2>Recovery PIN Reset</h2>
            <p class="sub-desc">Enter your phone and secret recovery PIN.</p>
            
            <label>Phone Number</label>
            <input type="tel" id="reset-phone" placeholder="e.g. 0612345678" />

            <label>Secret Recovery PIN</label>
            <input type="password" id="reset-pin" placeholder="Your secret PIN" />

            <label>New Password</label>
            <input type="password" id="reset-new" placeholder="Enter new password" />
            
            <button class="btn-action" onclick="submitReset()" style="background: var(--warning); color: var(--bg-deep);">Update Credentials</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-login')">Back to Sign In</a>
            </div>
        </div>

        <div id="screen-dashboard" class="hidden">
            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent);">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted);">EASA Professional Track</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">150</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">3</span></div>
                </div>
            </div>

            <div class="mode-grid">
                <div class="mode-tile" onclick="launchMode('modules')">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4>EASA Modules</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('voice')">
                    <span style="font-size: 1.4rem;">🎙️</span>
                    <h4>Voice Drill</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('typing')">
                    <span style="font-size: 1.4rem;">⌨️</span>
                    <h4>Strict Typing</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('vault')">
                    <span style="font-size: 1.4rem;">📚</span>
                    <h4>Glossary Vault</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container"></div>
            
            <button class="btn-action" onclick="resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border); margin-top: 0.5rem;">← Return to Command Hub</button>
        </div>
    </div>

    <script>
        let sessionUser = null;
        let academyData = { modules: [], drills: [] };
        let activeLang = 'en';
        let drillPointer = 0;

        const localization = {
            en: { title: "Cabin Crew Portal", sub: "Access accredited EASA/ICAO simulation modules.", btn: "Sign In to Simulator" },
            fr: { title: "Portail Personnel de Cabine", sub: "Accédez aux modules de simulation EASA/ICAO.", btn: "Se connecter" },
            ar: { title: "بوابة طاقم الطائرة", sub: "الوصول إلى وحدات المحاكاة المعتمدة من EASA/ICAO.", btn: "تسجيل الدخول للمحاكي" }
        };

        function showToast(text, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = text;
            t.style.background = isError ? 'var(--danger)' : 'var(--success)';
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3500);
        }

        function navigateTo(id) {
            ['screen-login', 'screen-register', 'screen-reset', 'screen-dashboard'].forEach(s => document.getElementById(s).classList.add('hidden'));
            document.getElementById(id).classList.remove('hidden');
        }

        function setLanguage(lang) {
            activeLang = lang;
            document.querySelectorAll('.lang-badge').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            if(localization[lang]) {
                document.getElementById('ui-login-title').innerText = localization[lang].title;
                document.getElementById('ui-login-sub').innerText = localization[lang].sub;
                document.getElementById('ui-login-btn').innerText = localization[lang].btn;
            }
            showToast('Language updated: ' + lang.toUpperCase());
        }

        async function submitRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();

            if(!full_name || !phone_number || !password || !recovery_pin) { showToast('Complete all fields', true); return; }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ full_name, phone_number, password, recovery_pin })
            });
            const data = await res.json();
            if(res.ok) {
                showToast('Cadet profile created successfully!');
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
                sessionUser = data.student;
                document.getElementById('dash-name').innerText = sessionUser.full_name;
                document.getElementById('dash-xp').innerText = sessionUser.xp_points;
                document.getElementById('dash-hearts').innerText = sessionUser.hearts;
                document.getElementById('dash-streak').innerText = sessionUser.streak;
                navigateTo('screen-dashboard');
                fetchAcademyContent();
                showToast('Welcome aboard, Captain ' + sessionUser.full_name + '!');
            } else {
                showToast('Invalid phone or password', true);
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
            const res = await fetch('/api/academy/data');
            academyData = await res.json();
            launchMode('modules');
        }

        function resetToMenu() {
            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1rem; margin-bottom: 0.5rem; color: var(--accent);">Select Training Command</h3>
                <p style="font-size: 0.8rem; color: var(--text-muted);">Choose a training mode above to start interactive practice.</p>
            `;
        }

        function launchMode(mode) {
            const box = document.getElementById('simulation-box');
            if(mode === 'modules') {
                const mod = academyData.modules[0];
                box.innerHTML = `
                    <span style="font-size: 0.68rem; font-weight: 800; background: rgba(56,189,248,0.1); color: var(--accent); padding: 2px 8px; border-radius: 4px;">OFFICIAL MODULE: ${mod.category}</span>
                    <h3 style="font-size: 1.05rem; margin: 0.5rem 0; color: white;">${mod.title_en}</h3>
                    <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1rem;">${mod.content_en}</p>
                    <button class="btn-action" onclick="launchMode('voice')">Proceed to Voice Drill →</button>
                `;
            } else if(mode === 'voice') {
                const term = academyData.drills[drillPointer % academyData.drills.length];
                box.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.68rem; font-weight: 800; color: var(--warning);">VOICE PRONUNCIATION DRILL</span>
                        <span style="font-size: 0.72rem; color: var(--text-muted);">Drill ${ (drillPointer % academyData.drills.length) + 1 } of ${academyData.drills.length}</span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: white; margin-bottom: 4px;">Say: "${term.term_en}"</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 1rem;">Hint: ${term.hint_en}</div>
                    <button class="mic-circle" id="mic-trigger" onclick="startSpeechRecognition(${term.id})">
                        <span style="font-size: 1.8rem;">🎙️</span>
                    </button>
                    <div id="speech-feedback" style="text-align: center; font-size: 0.78rem; color: var(--text-muted);">Click microphone and state the aviation term clearly</div>
                `;
            } else if(mode === 'typing') {
                const term = academyData.drills[drillPointer % academyData.drills.length];
                box.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.68rem; font-weight: 800; color: var(--success);">STRICT TYPING & SPELLING</span>
                        <span style="font-size: 0.72rem; color: var(--text-muted);">Test ${ (drillPointer % academyData.drills.length) + 1 }</span>
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: white; margin-bottom: 4px;">Translate: ${term.term_ar} / ${term.term_fr}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 1rem;">Type official English standard terminology:</div>
                    <input type="text" id="typing-input" placeholder="Type term exactly..." autocomplete="off" />
                    <button class="btn-action" onclick="verifyTypingInput(${term.id})" style="background: var(--success); color: white;">Validate Spelling ✓</button>
                `;
            } else if(mode === 'vault') {
                box.innerHTML = `
                    <h3 style="font-size: 1rem; margin-bottom: 0.8rem; color: var(--accent);">EASA Glossary Vault</h3>
                    <div style="max-height: 200px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; padding-right: 4px;">
                        ${academyData.drills.map(d => `
                            <div style="background: var(--bg-deep); padding: 0.6rem 0.8rem; border-radius: 10px; border: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 0.8rem;">
                                <span><b>${d.term_en}</b></span>
                                <span style="color: var(--accent);">${d.term_ar} /${d.term_fr}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
        }

        function startSpeechRecognition(drillId) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRec) {
                showToast('Speech recognition not supported in your browser. Use Google Chrome.', true);
                return;
            }

            const rec = new SpeechRec();
            rec.lang = 'en-US';
            const micBtn = document.getElementById('mic-trigger');
            const feedback = document.getElementById('speech-feedback');

            micBtn.classList.add('recording');
            feedback.innerText = "Listening... Speak now!";

            rec.onresult = async function(e) {
                micBtn.classList.remove('recording');
                const spoken = e.results[0][0].transcript;
                feedback.innerText = `Detected: "${spoken}"`;

                const res = await fetch('/api/drill/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: sessionUser.phone_number, drill_id: drillId, user_answer: spoken })
                });
                const data = await res.json();
                showToast(data.message, !data.correct);
                document.getElementById('dash-xp').innerText = data.xp;
                document.getElementById('dash-hearts').innerText = data.hearts;
                document.getElementById('dash-streak').innerText = data.streak;
                if(data.correct) {
                    drillPointer++;
                    setTimeout(() => launchMode('voice'), 1800);
                }
            };

            rec.onerror = function() {
                micBtn.classList.remove('recording');
                feedback.innerText = "Microphone timeout. Try again.";
                showToast('Microphone error detected', true);
            };

            rec.start();
        }

        async function verifyTypingInput(drillId) {
            const inp = document.getElementById('typing-input');
            const val = inp.value.trim();
            if(!val) { showToast('Type an answer first', true); return; }

            const res = await fetch('/api/drill/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, drill_id: drillId, user_answer: val })
            });
            const data = await res.json();
            showToast(data.message, !data.correct);
            document.getElementById('dash-xp').innerText = data.xp;
            document.getElementById('dash-hearts').innerText = data.hearts;
            document.getElementById('dash-streak').innerText = data.streak;
            if(data.correct) {
                drillPointer++;
                setTimeout(() => launchMode('typing'), 1500);
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
