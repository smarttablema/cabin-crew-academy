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

app = FastAPI(title="AeroCrew Pro Academy Elite", version="6.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aviation_academy_students (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            xp_points INT DEFAULT 350,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS academy_path_modules_v6 (
            id SERIAL PRIMARY KEY,
            year_level INT,
            node_order INT,
            category VARCHAR(50),
            title_en TEXT,
            title_ar TEXT,
            title_fr TEXT,
            desc_en TEXT,
            desc_ar TEXT,
            desc_fr TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS official_drills_v6 (
            id SERIAL PRIMARY KEY,
            term_en VARCHAR(100),
            term_ar VARCHAR(100),
            term_fr VARCHAR(100),
            category VARCHAR(50),
            hint_en TEXT,
            hint_ar TEXT,
            hint_fr TEXT
        );
    """)
    
    # Seed Year 1 & Year 2 Professional Curriculum Nodes
    cur.execute("""
        INSERT INTO academy_path_modules_v6 (year_level, node_order, category, title_en, title_ar, title_fr, desc_en, desc_ar, desc_fr)
        VALUES 
        (1, 1, 'SEP', 'Introduction to Cabin Safety & SEP', 'مقدمة في سلامة المقصورة وإجراءات الطوارئ', 'Introduction à la sécurité cabine', 
         'Learn core aviation regulations, EASA standards, pre-flight safety checks, and sterile flight deck protocols.',
         'تعرف على لوائح الطيران الأساسية، معايير EASA، فحوصات السلامة قبل الرحلة، وبروتوكولات قمرة القيادة المعقمة.',
         'Apprenez la réglementation aéronautique, les normes EASA et les vérifications de sécurité avant vol.'),
        
        (1, 2, 'SEP', 'Emergency Evacuation & Exits', 'الإخلاء الطارئ ومخارج الطوارئ', 'Évacuation d urgence et issues', 
         'Master the 90-second evacuation rule, slide arming cross-checks, and emergency land/water brace commands.',
         'إتقان قاعدة الإخلاء في 90 ثانية، والتحقق المتقاطع لتجهيز المنحدرات، وأوامر وضعية الاستعداد.',
         'Maîtrisez la règle d évacuation de 90 secondes, l armement des toboggans et les positions de sécurité.'),
        
        (1, 3, 'Cargo/DG', 'Dangerous Goods (Hazmat) in Cabin', 'البضائع الخطرة والمواد الخطرة في المقصورة', 'Marchandises dangereuses en cabine', 
         'Identify prohibited cargo, lithium battery thermal runaway management in overhead lockers, and specialized extinguishers.',
         'تحديد البضائع المحظورة، وإدارة حرائق بطاريات الليثيوم في خزائن الأمتعة، واستخدام طفايات الحريق.',
         'Identifiez les marchandises prohibées, la gestion des feux de batteries au lithium et les extincteurs.'),

        (1, 4, 'Medical', 'Aeromedical First Aid & Hypoxia', 'الإسعافات الأولية الطبية ونقص الأكسجين', 'Premiers secours et hypoxie', 
         'Recognize hypoxia symptoms, administer portable oxygen bottles, perform CPR, and manage rapid cabin decompression.',
         'التعرف على أعراض نقص الأكسجين، وإدارة اسطوانات الأكسجين، وإجراء انعاش القلب، وإزالة الضغط.',
         'Reconnaître les symptômes de l hypoxie, administrer l oxygène portable et gérer la décompression.'),

        (2, 1, 'CRM', 'Advanced Crew Resource Management', 'إدارة موارد الطاقم المتقدمة', 'Gestion avancée des ressources (CRM)', 
         'Leadership in high-stress multi-crew environments, effective communication, decision-making, and error management.',
         'القيادة في بيئات الطاقم المتعدد عالية الضغط، التواصل الفعال، اتخاذ القرارات، وإدارة الأخطاء.',
         'Leadership dans les environnements multi-équipages à haut stress, communication efficace et gestion des erreurs.'),

        (2, 2, 'AVSEC', 'Aviation Security & Threat Levels', 'أمن الطيران ومستويات التهديد', 'Sûreté aérienne et menaces', 
         'Unruly passenger de-escalation, bomb threat checklist management, flight deck defense, and cabin search protocols.',
         'تهدئة الركاب المشاغبين، إدارة قوائم التهديد بالقنابل، دفاع قمرة القيادة، وبروتوكولات تفتيش المقصورة.',
         'Désescalade des passagers indisciplinés, gestion des alertes à la bombe et protocoles de fouille de cabine.'),

        (2, 3, 'SEP', 'Senior Purser & Crew Leadership', 'كبير المضيفين القيادة المتقدمة', 'Chef de cabine et leadership', 
         'Managing crew rosters, briefing protocols, emergency coordination with flight deck, and post-incident reporting.',
         'إدارة جداول الطاقم، بروتوكولات الإحاطة، التنسيق الطارئ مع قمرة القيادة، وتقارير ما بعد الحوادث.',
         'Gestion des plannings d équipage, protocoles de briefing et coordination d urgence avec le cockpit.')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO official_drills_v6 (term_en, term_ar, term_fr, category, hint_en, hint_ar, hint_fr)
        VALUES 
        ('Altimeter', 'مقياس الارتفاع', 'Altimètre', 'Instruments', 'Measures barometric altitude.', 'يقيس الارتفاع الجوي.', 'Mesure l altitude barométrique.'),
        ('Bulkhead', 'الجدار الفاصل', 'Cloison', 'Cabin', 'Structural cabin partition.', 'فاصل هيكلي للمقصورة.', 'Cloison structurelle de cabine.'),
        ('Decompression', 'إزالة الضغط', 'Décompression', 'Emergency', 'Loss of cabin pressurization.', 'فقدان ضغط المقصورة.', 'Perte de pressurisation en cabine.'),
        ('Turbulence', 'مطبات هوائية', 'Turbulence', 'Meteorology', 'Unsteady air currents.', 'تيارات هوائية غير مستقرة.', 'Courants d air instables.'),
        ('Evacuation', 'إخلاء الطائرة', 'Évacuation', 'SEP', 'Rapid emergency passenger exit.', 'خروج طارئ سريع للركاب.', 'Sortie d urgence rapide.'),
        ('Brace Position', 'وضعية الاستعداد', 'Position de sécurité', 'SEP', 'Protective crash position.', 'وضعية الحماية عند الاصطدام.', 'Position de protection antichoc.')
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
    cur.execute("SELECT * FROM aviation_academy_students WHERE phone_number = %s;", (data.phone_number,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered.")
    
    cur.execute(
        "INSERT INTO aviation_academy_students (phone_number, full_name, password, recovery_pin) VALUES (%s, %s, %s, %s) RETURNING *;",
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
    cur.execute("SELECT * FROM aviation_academy_students WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
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
    cur.execute("SELECT * FROM aviation_academy_students WHERE phone_number = %s AND recovery_pin = %s;", (data.phone_number, data.recovery_pin))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid recovery PIN.")
    cur.execute("UPDATE aviation_academy_students SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/academy/content")
def get_academy_content():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM academy_path_modules_v6 ORDER BY year_level ASC, node_order ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM official_drills_v6 ORDER BY id ASC;")
    drills = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "drills": drills}

@app.post("/api/drill/verify")
def verify_drill(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM official_drills_v6 WHERE id = %s;", (data.drill_id,))
    drill = cur.fetchone()
    cur.execute("SELECT * FROM aviation_academy_students WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    
    if not drill or not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found.")
    
    correct_term = drill["term_en"].strip().lower()
    user_input = data.user_answer.strip().lower()
    
    similarity = difflib.SequenceMatcher(None, user_input, correct_term).ratio()
    
    if user_input == correct_term:
        cur.execute("UPDATE aviation_academy_students SET xp_points = xp_points + 25 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": "Perfect execution! +25 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    elif similarity >= 0.75:
        cur.execute("UPDATE aviation_academy_students SET xp_points = xp_points + 15 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": f"Accepted with minor typo! Official: '{drill['term_en']}'. +15 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    else:
        new_hearts = max(0, student["hearts"] - 1)
        cur.execute("UPDATE aviation_academy_students SET hearts = %s WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (new_hearts, data.phone_number))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": False, "correct_term": drill["term_en"], "message": f"Incorrect! Standard term: '{drill['term_en']}'", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AeroCrew Pro Academy | Elite Aviation Training</title>
    <link rel="icon" href="https://img.icons8.com/color/48/airplane-take-off.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Tajawal:wght@450;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #020617;
            --surface: #0f172a;
            --surface-card: #1e293b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.3);
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        [dir="rtl"] * { font-family: 'Tajawal', sans-serif !important; }
        
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        
        .app-shell { width: 100%; max-width: 520px; background: var(--surface); border-radius: 32px; padding: 2.2rem; border: 1px solid var(--border); box-shadow: 0 40px 80px rgba(0, 0, 0, 0.9); position: relative; overflow: hidden; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.8rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.15rem; color: var(--accent); }
        .brand-title img { width: 34px; height: 34px; }
        
        .lang-switch { display: flex; gap: 6px; }
        .lang-badge { background: var(--surface-card); border: 1px solid var(--border); border-radius: 8px; padding: 5px 10px; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-badge.active, .lang-badge:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.4rem; }
        p.sub-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.74rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.5px; }
        input { width: 100%; padding: 0.95rem 1.1rem; border-radius: 14px; border: 1px solid var(--border); background: var(--bg-deep); color: white; font-size: 0.95rem; margin-bottom: 1.1rem; outline: none; transition: all 0.2s; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1rem; border-radius: 14px; border: none; background: var(--accent); color: var(--bg-deep); font-weight: 800; font-size: 0.98rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s; box-shadow: 0 4px 16px var(--accent-glow); }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.92; }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; font-size: 0.82rem; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 600; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.95rem 1.2rem; border-radius: 16px; border: 1px solid var(--border); margin-bottom: 1.2rem; }
        .stat-item { font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; gap: 5px; }
        
        /* 2x2 Grid requested by user */
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.2rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.2s; }
        .mode-tile:hover { border-color: var(--accent); background: var(--accent-glow); transform: translateY(-2px); }
        .mode-tile h4 { font-size: 0.88rem; font-weight: 700; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 20px; padding: 1.5rem; border: 1px solid var(--border); margin-bottom: 1rem; position: relative; min-height: 240px; }
        
        /* Duolingo-style Learning Path Tree */
        .path-container { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 10px 0; max-height: 230px; overflow-y: auto; }
        .path-node { width: 56px; height: 56px; border-radius: 50%; background: var(--accent); color: var(--bg-deep); display: flex; justify-content: center; align-items: center; font-weight: 800; font-size: 1.1rem; cursor: pointer; box-shadow: 0 0 20px var(--accent-glow); transition: transform 0.2s; position: relative; }
        .path-node:hover { transform: scale(1.1); }
        .path-node.locked { background: var(--border); color: var(--text-muted); box-shadow: none; cursor: not-allowed; }
        .path-node:nth-child(even) { transform: translateX(25px); }
        .path-node:nth-child(odd) { transform: translateX(-25px); }

        .mic-circle { width: 75px; height: 75px; border-radius: 50%; background: var(--accent); border: none; display: flex; justify-content: center; align-items: center; margin: 1rem auto 0.5rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s; }
        .mic-circle.recording { background: var(--danger); animation: pulseAnim 1.5s infinite; }
        @keyframes pulseAnim { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); } 70% { box-shadow: 0 0 0 22px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

        .timer-bar { width: 100%; height: 4px; background: var(--border); border-radius: 2px; margin-bottom: 1rem; overflow: hidden; }
        .timer-progress { width: 100%; height: 100%; background: var(--warning); transition: width 1s linear; }

        .inline-feedback { text-align: center; font-size: 0.82rem; font-weight: 700; margin-top: 8px; min-height: 20px; transition: color 0.2s; }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 12px 24px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 4000; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Icon">
                <span id="txt-brand">AeroCrew Pro</span>
            </div>
            <div class="lang-switch">
                <button class="lang-badge active" onclick="setLanguage('en')">EN</button>
                <button class="lang-badge" onclick="setLanguage('fr')">FR</button>
                <button class="lang-badge" onclick="setLanguage('ar')">AR</button>
            </div>
        </div>

        <!-- 1. SIGN IN SCREEN -->
        <div id="screen-login">
            <h2 id="ui-login-title">Cabin Crew Portal</h2>
            <p class="sub-desc" id="ui-login-sub">Access accredited EASA/ICAO simulation modules.</p>
            
            <label id="lbl-phone">Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label id="lbl-pass">Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn-action" onclick="submitLogin()" id="ui-login-btn">Sign In to Simulator</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-register')" id="nav-reg">Create Account</a>
                <a onclick="navigateTo('screen-reset')" id="nav-reset">Forgot Password?</a>
            </div>
        </div>

        <!-- 2. REGISTER SCREEN -->
        <div id="screen-register" class="hidden">
            <h2 id="reg-title">Cadet Enrollment</h2>
            <p class="sub-desc" id="reg-sub">Register your official student training profile.</p>
            
            <label id="reg-lbl-name">Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label id="reg-lbl-phone">Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label id="reg-lbl-pass">Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label id="reg-lbl-pin">Recovery PIN (4-6 digits)</label>
            <input type="password" id="reg-pin" placeholder="e.g. 2026" maxlength="6" />
            
            <button class="btn-action" onclick="submitRegister()" style="background: var(--success); color: white;" id="reg-btn-sub">Initialize Profile</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-login')" id="reg-back">Already have an account? Sign In</a>
            </div>
        </div>

        <!-- 3. RESET PASSWORD SCREEN -->
        <div id="screen-reset" class="hidden">
            <h2 id="res-title">Recovery PIN Reset</h2>
            <p class="sub-desc" id="res-sub">Enter your phone and secret recovery PIN.</p>
            
            <label id="res-lbl-phone">Phone Number</label>
            <input type="tel" id="reset-phone" placeholder="e.g. 0612345678" />

            <label id="res-lbl-pin">Secret Recovery PIN</label>
            <input type="password" id="reset-pin" placeholder="Your secret PIN" />

            <label id="res-lbl-new">New Password</label>
            <input type="password" id="reset-new" placeholder="Enter new password" />
            
            <button class="btn-action" onclick="submitReset()" style="background: var(--warning); color: var(--bg-deep);" id="res-btn-sub">Update Credentials</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-login')" id="res-back">Back to Sign In</a>
            </div>
        </div>

        <!-- 4. GAMIFIED DASHBOARD -->
        <div id="screen-dashboard" class="hidden">
            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent);">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted);" id="dash-track">EASA Professional Track</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">350</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">7</span></div>
                </div>
            </div>

            <!-- Requested 2x2 Grid Layout -->
            <div class="mode-grid">
                <div class="mode-tile" onclick="launchYearPath(1)">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4 id="tile-year1">First Year</h4>
                </div>
                <div class="mode-tile" onclick="launchYearPath(2)">
                    <span style="font-size: 1.4rem;">🏆</span>
                    <h4 id="tile-year2">Second Year</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('typing')">
                    <span style="font-size: 1.4rem;">⌨️</span>
                    <h4 id="tile-typing">Strict Typing</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('voice')">
                    <span style="font-size: 1.4rem;">🎙️</span>
                    <h4 id="tile-voice">Voice Drill</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container"></div>
            
            <button class="btn-action" onclick="resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border); margin-top: 0.5rem;" id="btn-menu">← Return to Command Hub</button>
        </div>
    </div>

    <script>
        let sessionUser = null;
        let academyData = { modules: [], drills: [] };
        let activeLang = 'en';
        let drillPointer = 0;
        let timerInterval = null;
        let secondsLeft = 30;

        const translations = {
            en: {
                loginTitle: "Cabin Crew Portal", loginSub: "Access accredited EASA/ICAO simulation modules.",
                phoneLbl: "Phone Number", passLbl: "Password", loginBtn: "Sign In to Simulator",
                regNav: "Create Account", resetNav: "Forgot Password?",
                regTitle: "Cadet Enrollment", regSub: "Register your official student training profile.",
                regName: "Full Name", regPass: "Password", regPin: "Recovery PIN (4-6 digits)", regBtn: "Initialize Profile", regBack: "Already have an account? Sign In",
                resTitle: "Recovery PIN Reset", resSub: "Enter your phone and secret recovery PIN.", resNew: "New Password", resBtn: "Update Credentials",
                tileYear1: "First Year", tileYear2: "Second Year", tileTyping: "Strict Typing", tileVoice: "Voice Drill",
                menuBtn: "← Return to Command Hub"
            },
            fr: {
                loginTitle: "Portail Personnel de Cabine", loginSub: "Accédez aux modules de simulation EASA/ICAO.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter au simulateur",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                regTitle: "Inscription Cadet", regSub: "Enregistrez votre profil de formation officiel.",
                regName: "Nom et Prénom", regPass: "Mot de passe", regPin: "PIN de récupération (4-6 chiffres)", regBtn: "Initialiser le profil", regBack: "Déjà un compte ? Se connecter",
                resTitle: "Réinitialisation PIN", resSub: "Entrez votre téléphone et votre PIN secret.", resNew: "Nouveau mot de passe", resBtn: "Mettre à jour",
                tileYear1: "Première Année", tileYear2: "Seconde Année", tileTyping: "Saisie Stricte", tileVoice: "Drill Vocal",
                menuBtn: "← Retour au Menu"
            },
            ar: {
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى وحدات المحاكاة المعتمدة من EASA/ICAO.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول للمحاكي",
                regNav: "إنشاء حساب", resetNav: "هل نسيت كلمة المرور؟",
                regTitle: "تسجيل المتدرب", regSub: "سجل ملف تدريب الطالب الرسمي الخاص بك.",
                regName: "الاسم الكامل", regPass: "كلمة المرور", regPin: "رمز الاسترداد (4-6 أرقام)", regBtn: "تهيئة الملف الشخصي", regBack: "لديك حساب بالفعل؟ تسجيل الدخول",
                resTitle: "إعادة تعيين الرمز", resSub: "أدخل هاتفك ورقم الرمز السري للاسترداد.", resNew: "كلمة المرور الجديدة", resBtn: "تحديث بيانات الاعتماد",
                tileYear1: "السنة الأولى", tileYear2: "السنة الثانية", tileTyping: "الكتابة الدقيقة", tileVoice: "تدريب الصوت",
                menuBtn: "← العودة إلى القائمة الرئيسية"
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
            ['screen-login', 'screen-register', 'screen-reset', 'screen-dashboard'].forEach(s => document.getElementById(s).classList.add('hidden'));
            document.getElementById(id).classList.remove('hidden');
        }

        function setLanguage(lang) {
            activeLang = lang;
            document.querySelectorAll('.lang-badge').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            
            const root = document.getElementById('html-root');
            if(lang === 'ar') {
                root.setAttribute('dir', 'rtl');
            } else {
                root.setAttribute('dir', 'ltr');
            }

            const t = translations[lang];
            if(t) {
                document.getElementById('ui-login-title').innerText = t.loginTitle;
                document.getElementById('ui-login-sub').innerText = t.loginSub;
                document.getElementById('lbl-phone').innerText = t.phoneLbl;
                document.getElementById('lbl-pass').innerText = t.passLbl;
                document.getElementById('ui-login-btn').innerText = t.loginBtn;
                document.getElementById('nav-reg').innerText = t.regNav;
                document.getElementById('nav-reset').innerText = t.resetNav;
                
                document.getElementById('reg-title').innerText = t.regTitle;
                document.getElementById('reg-sub').innerText = t.regSub;
                document.getElementById('reg-lbl-name').innerText = t.regName;
                document.getElementById('reg-lbl-phone').innerText = t.phoneLbl;
                document.getElementById('reg-lbl-pass').innerText = t.regPass;
                document.getElementById('reg-lbl-pin').innerText = t.regPin;
                document.getElementById('reg-btn-sub').innerText = t.regBtn;
                document.getElementById('reg-back').innerText = t.regBack;

                document.getElementById('res-title').innerText = t.resTitle;
                document.getElementById('res-sub').innerText = t.resSub;
                document.getElementById('res-lbl-phone').innerText = t.phoneLbl;
                document.getElementById('res-lbl-pin').innerText = t.regPin;
                document.getElementById('res-lbl-new').innerText = t.resNew;
                document.getElementById('res-btn-sub').innerText = t.resBtn;
                document.getElementById('res-back').innerText = t.regBack;

                document.getElementById('tile-year1').innerText = t.tileYear1;
                document.getElementById('tile-year2').innerText = t.tileYear2;
                document.getElementById('tile-typing').innerText = t.tileTyping;
                document.getElementById('tile-voice').innerText = t.tileVoice;
                document.getElementById('btn-menu').innerText = t.menuBtn;
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
            const res = await fetch('/api/academy/content');
            academyData = await res.json();
            resetToMenu();
        }

        function resetToMenu() {
            if(timerInterval) clearInterval(timerInterval);
            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1.05rem; margin-bottom: 0.5rem; color: var(--accent);">EASA Professional Training Center</h3>
                <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5;">Select <b>First Year</b> or <b>Second Year</b> above to explore the official Duolingo-style interactive path, or jump straight into typing & voice drills.</p>
            `;
        }

        function launchYearPath(yearNum) {
            if(timerInterval) clearInterval(timerInterval);
            const box = document.getElementById('simulation-box');
            const yearMods = academyData.modules.filter(m => m.year_level === yearNum);

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: var(--accent); font-weight: 800;">Year ${yearNum} Official Learning Path</h3>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Interactive Roadmap</span>
                </div>
                <div class="path-container">
                    ${yearMods.map((mod, idx) => {
                        let title = mod.title_en;
                        if(activeLang === 'ar') title = mod.title_ar;
                        if(activeLang === 'fr') title = mod.title_fr;
                        return `
                            <div class="path-node" onclick="viewModuleDetail(${mod.id})" title="${title}">
                                ${idx + 1}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        function viewModuleDetail(modId) {
            const mod = academyData.modules.find(m => m.id === modId);
            if(!mod) return;
            let title = mod.title_en;
            let desc = mod.desc_en;
            if(activeLang === 'ar') { title = mod.title_ar; desc = mod.desc_ar; }
            if(activeLang === 'fr') { title = mod.title_fr; desc = mod.desc_fr; }

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <span style="font-size: 0.7rem; font-weight: 800; background: rgba(56,189,248,0.15); color: var(--accent); padding: 3px 10px; border-radius: 6px;">EASA OFFICIAL CURRICULUM : ${mod.category}</span>
                <h3 style="font-size: 1.15rem; margin: 0.6rem 0; color: white; font-weight: 800;">${title}</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 1.5rem; background: var(--bg-deep); padding: 1rem; border-radius: 12px; border: 1px solid var(--border);">${desc}</p>
                <button class="btn-action" onclick="launchYearPath(${mod.year_level})">← Back to Path</button>
            `;
        }

        function start30SecTimer(callbackWhenDone) {
            if(timerInterval) clearInterval(timerInterval);
            secondsLeft = 30;
            const bar = document.getElementById('timer-fill');
            const txt = document.getElementById('timer-text');
            
            timerInterval = setInterval(() => {
                secondsLeft--;
                if(bar) bar.style.width = ((secondsLeft / 30) * 100) + '%';
                if(txt) txt.innerText = `${secondsLeft}s remaining`;
                
                if(secondsLeft <= 0) {
                    clearInterval(timerInterval);
                    if(callbackWhenDone) callbackWhenDone();
                }
            }, 1000);
        }

        function revealAnswer(termEn) {
            if(timerInterval) clearInterval(timerInterval);
            document.getElementById('inline-msg').style.color = 'var(--warning)';
            document.getElementById('inline-msg').innerText = `Official Answer: "${termEn}"`;
        }

        function launchMode(mode) {
            if(timerInterval) clearInterval(timerInterval);
            const box = document.getElementById('simulation-box');
            const term = academyData.drills[drillPointer % academyData.drills.length];

            if(mode === 'voice') {
                let hint = term.hint_en;
                if(activeLang === 'ar') hint = term.hint_ar;
                if(activeLang === 'fr') hint = term.hint_fr;

                box.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.7rem; font-weight: 800; color: var(--warning);">VOICE PRONUNCIATION DRILL</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);" id="timer-text">30s remaining</span>
                    </div>
                    <div class="timer-bar"><div id="timer-fill" class="timer-progress"></div></div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: white; margin-bottom: 4px;">Say: "${term.term_en}"</div>
                    <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.5rem;">Hint: ${hint}</div>
                    <button class="mic-circle" id="mic-trigger" onclick="startSpeechRecognition(${term.id})">
                        <span style="font-size: 1.8rem;">🎙️</span>
                    </button>
                    <div id="inline-msg" class="inline-feedback" style="color: var(--text-muted);">Click mic and speak clearly</div>
                    <div id="reveal-container" style="text-align: center; margin-top: 6px;"></div>
                `;
                start30SecTimer(() => {
                    document.getElementById('reveal-container').innerHTML = `<button onclick="revealAnswer('${term.term_en}')" style="background:none; border:1px solid var(--warning); color:var(--warning); padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.75rem; cursor:pointer;">Reveal Answer 💡</button>`;
                });
            } else if(mode === 'typing') {
                let promptTerm = term.term_ar;
                if(activeLang === 'fr') promptTerm = term.term_fr;
                if(activeLang === 'en') promptTerm = term.hint_en;

                box.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.7rem; font-weight: 800; color: var(--success);">STRICT SPELLING & TYPING</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);" id="timer-text">30s remaining</span>
                    </div>
                    <div class="timer-bar"><div id="timer-fill" class="timer-progress"></div></div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: white; margin-bottom: 4px;">Translate: ${promptTerm}</div>
                    <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem;">Type exact English EASA terminology:</div>
                    <input type="text" id="typing-input" placeholder="Type term exactly..." autocomplete="off" />
                    <button class="btn-action" onclick="verifyTypingInput(${term.id})" style="background: var(--success); color: white; margin-bottom: 0.6rem;">Validate Spelling ✓</button>
                    <div id="inline-msg" class="inline-feedback" style="color: var(--text-muted);"></div>
                    <div id="reveal-container" style="text-align: center; margin-top: 4px;"></div>
                `;
                start30SecTimer(() => {
                    document.getElementById('reveal-container').innerHTML = `<button onclick="revealAnswer('${term.term_en}')" style="background:none; border:1px solid var(--warning); color:var(--warning); padding:4px 12px; border-radius:6px; font-weight:700; font-size:0.75rem; cursor:pointer;">Reveal Answer 💡</button>`;
                });
            }
        }

        function startSpeechRecognition(drillId) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRec) {
                showToast('Speech recognition requires Google Chrome or Safari.', true);
                return;
            }

            const rec = new SpeechRec();
            rec.lang = 'en-US';
            const micBtn = document.getElementById('mic-trigger');
            const inlineMsg = document.getElementById('inline-msg');

            micBtn.classList.add('recording');
            inlineMsg.style.color = 'var(--accent)';
            inlineMsg.innerText = "Listening... Speak now!";

            rec.onresult = async function(e) {
                if(timerInterval) clearInterval(timerInterval);
                micBtn.classList.remove('recording');
                const spoken = e.results[0][0].transcript;

                const res = await fetch('/api/drill/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: sessionUser.phone_number, drill_id: drillId, user_answer: spoken })
                });
                const data = await res.json();
                document.getElementById('dash-xp').innerText = data.xp;
                document.getElementById('dash-hearts').innerText = data.hearts;
                document.getElementById('dash-streak').innerText = data.streak;

                if(data.correct) {
                    inlineMsg.style.color = 'var(--success)';
                    inlineMsg.innerText = data.message;
                    drillPointer++;
                    setTimeout(() => launchMode('voice'), 1500);
                } else {
                    inlineMsg.style.color = 'var(--danger)';
                    inlineMsg.innerText = "Incorrect! Try again or repeat.";
                }
            };

            rec.onerror = function() {
                micBtn.classList.remove('recording');
                inlineMsg.style.color = 'var(--danger)';
                inlineMsg.innerText = "Could not hear audio. Try again.";
            };

            rec.start();
        }

        async function verifyTypingInput(drillId) {
            if(timerInterval) clearInterval(timerInterval);
            const inp = document.getElementById('typing-input');
            const val = inp.value.trim();
            const inlineMsg = document.getElementById('inline-msg');
            if(!val) { showToast('Type an answer first', true); return; }

            const res = await fetch('/api/drill/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, drill_id: drillId, user_answer: val })
            });
            const data = await res.json();
            document.getElementById('dash-xp').innerText = data.xp;
            document.getElementById('dash-hearts').innerText = data.hearts;
            document.getElementById('dash-streak').innerText = data.streak;

            if(data.correct) {
                inlineMsg.style.color = 'var(--success)';
                inlineMsg.innerText = data.message;
                drillPointer++;
                setTimeout(() => launchMode('typing'), 1500);
            } else {
                inlineMsg.style.color = 'var(--danger)';
                inlineMsg.innerText = data.message;
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
