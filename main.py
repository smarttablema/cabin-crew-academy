import os
import difflib
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Iro Crew Academy Elite", version="10.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Permanent users table supporting roles (student / teacher), groups, and referral codes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iro_crew_users_v10 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            role VARCHAR(20) DEFAULT 'student',
            crew_avatar VARCHAR(20) DEFAULT 'steward',
            active_skin VARCHAR(100) DEFAULT 'Standard Aviator Suit',
            group_code VARCHAR(50) DEFAULT 'EASA-ALPHA-1',
            referred_by VARCHAR(50) DEFAULT '',
            xp_points INT DEFAULT 850,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Teacher PDF / Lesson broadcast table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS instructor_lessons_v10 (
            id SERIAL PRIMARY KEY,
            teacher_name VARCHAR(100),
            group_code VARCHAR(50),
            lesson_title TEXT,
            pdf_url TEXT,
            lesson_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Premium Shop Skins
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iro_shop_skins_v10 (
            id SERIAL PRIMARY KEY,
            category VARCHAR(20),
            skin_name VARCHAR(50),
            cost INT,
            preview_svg TEXT,
            desc_en TEXT
        );
    """)
    # Curriculum Modules
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iro_curriculum_v10 (
            id SERIAL PRIMARY KEY,
            year_level INT,
            node_order INT,
            category VARCHAR(50),
            title_en TEXT,
            title_ar TEXT,
            title_fr TEXT,
            content_en TEXT,
            content_ar TEXT,
            content_fr TEXT
        );
    """)
    # Drills
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iro_drills_v10 (
            id SERIAL PRIMARY KEY,
            year_level INT,
            term_en VARCHAR(100),
            term_ar VARCHAR(100),
            term_fr VARCHAR(100),
            category VARCHAR(50),
            hint_en TEXT,
            hint_ar TEXT,
            hint_fr TEXT
        );
    """)

    # Seed Premium Skins (Male & Female Collections)
    cur.execute("""
        INSERT INTO iro_shop_skins_v10 (category, skin_name, cost, preview_svg, desc_en)
        VALUES 
        ('male', 'Supersonic Gold Captain', 200, '👨‍✈️⭐', 'Four golden sleeve stripes with commander wings and polished visor.'),
        ('male', 'First Officer Elite', 120, '🧑‍✈️🎖️', 'Sleek double silver epaulets with tailored midnight blazer.'),
        ('male', 'Private Jet Chief Purser', 150, '👔✨', 'Executive gold-trimmed tie and luxury service badge.'),
        ('male', 'Global Express Pilot', 180, '🕶️✈️', 'Aviator sunglasses and captain badge.'),
        
        ('female', 'Supreme Chief Hostess', 200, '👩‍✈️💎', 'Designer couture airline uniform with diamond wing brooch.'),
        ('female', 'Senior Purser Silk Scarf', 130, '🧣✨', 'Signature scarlet silk necktie and professional skirt suit.'),
        ('female', 'First Officer Wings', 150, '👩‍✈️🎖️', 'Sleek silver epaulets with modern European styling.'),
        ('female', 'VIP Charter Specialist', 180, '👜👑', 'Exclusive VIP cabin manager gold insignia.')
        ON CONFLICT DO NOTHING;
    """)

    # Seed Curriculum
    cur.execute("""
        INSERT INTO iro_curriculum_v10 (year_level, node_order, category, title_en, title_ar, title_fr, content_en, content_ar, content_fr)
        VALUES 
        (1, 1, 'SEP', 'Module 1: EASA Regulatory Framework & Pre-Flight Safety', 'الوحدة 1: لوائح EASA وفحوصات السلامة', 'Module 1: Cadre EASA et sécurité', 
         '1. Regulatory Framework: Cabin crew operate under European Union Aviation Safety Agency (EASA) Part-CC regulations.\n\n2. Pre-Flight Checks: Mandatory inspections of exit doors, slide pressure gauges, ELT, life vests, and PBO oxygen bottles.\n\n3. Sterile Flight Deck: Strict communication protocols during taxi, takeoff, and landing.',
         '1. الإطار التنظيمي: يعمل طاقم المقصورة تحت لوائح EASA الجزء CC.\n\n2. فحوصات ما قبل الرحلة: عمليات تفتيش إلزامية لأبواب المخارج ومعدات الطوارئ.\n\n3. قمرة القيادة المعقمة: بروتوكولات اتصال صارمة أثناء الإقلاع والهبوط.',
         '1. Cadre réglementaire : Les équipages opèrent sous la réglementation EASA Part-CC.\n\n2. Vérifications pré-vol : Inspections obligatoires des portes et équipements de secours.\n\n3. Cockpit stérile : Protocoles de communication stricts.'),
        
        (1, 2, 'SEP', 'Module 2: Emergency Evacuation & 90-Second Rule', 'الوحدة 2: الإخلاء الطارئ وقاعدة 90 ثانية', 'Module 2: Évacuation d urgence', 
         '1. The 90-Second Mandate: Complete aircraft evacuation must be achievable within 90 seconds using 50% exits.\n\n2. Slide Arming & Cross-Checking: Manual slide inflation checks and door cross-checks.\n\n3. Crowd Control: Authoritative commands ("LEAVE ALL BAGS, JUMP AND SLIDE!").',
         '1. تفويض 90 ثانية: يجب إخلاء الطائرة بالكامل خلال 90 ثانية.\n\n2. تجهيز المنحدرات: فحوصات يفحصها الطاقم للأبواب والمنحدرات.\n\n3. السيطرة على الحشود: أوامر حاسمة بصوت قوي.',
         '1. La règle des 90 secondes : Évacuation complète en 90 secondes maximum.\n\n2. Armement des toboggans : Vérifications croisées des portes.\n\n3. Gestion des foules : Commandes vocales directives.'),

        (2, 1, 'CRM', 'Module 5: Advanced Crew Resource Management', 'الوحدة 5: إدارة موارد الطاقم المتقدمة', 'Module 5: Gestion CRM avancée', 
         '1. Leadership Dynamics: Multicultural team coordination and conflict resolution.\n\n2. Threat and Error Management (TEM): Proactive operational threat identification.\n\n3. Decision Frameworks: FORCES and DOT-DEDUCT under high stress.',
         '1. ديناميكيات القيادة: تنسيق الفرق متعددة الثقافات وحل النزاعات.\n\n2. إدارة التهديدات والأخطاء (TEM): التحديد الاستباقي للتهديدات.\n\n3. أطر اتخاذ القرار تحت الضغط العالي.',
         '1. Leadership : Coordination d équipes multiculturelles et gestion des conflits.\n\n2. Gestion des menaces et erreurs (TEM).\n\n3. Cadres de décision sous haute pression.')
        ON CONFLICT DO NOTHING;
    """)

    # Seed Drills
    cur.execute("""
        INSERT INTO iro_drills_v10 (year_level, term_en, term_ar, term_fr, category, hint_en, hint_ar, hint_fr)
        VALUES 
        (1, 'Altimeter', 'مقياس الارتفاع', 'Altimètre', 'Instruments', 'Measures barometric altitude.', 'يقيس الارتفاع الجوي.', 'Mesure l altitude barométrique.'),
        (1, 'Bulkhead', 'الجدار الفاصل', 'Cloison', 'Cabin', 'Structural cabin partition.', 'فاصل هيكلي للمقصورة.', 'Cloison structurelle de cabine.'),
        (1, 'Decompression', 'إزالة الضغط', 'Décompression', 'Emergency', 'Loss of cabin pressurization.', 'فقدان ضغط المقصورة.', 'Perte de pressurisation en cabine.'),
        (1, 'Evacuation', 'إخلاء الطائرة', 'Évacuation', 'SEP', 'Rapid emergency passenger exit.', 'خروج طارئ سريع للركاب.', 'Sortie d urgence rapide.'),
        (2, 'Crew Resource Management', 'إدارة موارد الطاقم', 'CRM', 'CRM', 'Effective utilization of all resources.', 'الاستفادة الفعالة من جميع الموارد.', 'Utilisation efficace des ressources.'),
        (2, 'Sterile Flight Deck', 'قمرة القيادة المعقمة', 'Cockpit stérile', 'AVSEC', 'No non-essential tasks below 10,000 feet.', 'منع المهام غير الضرورية تحت 10000 قدم.', 'Interdiction des tâches non essentielles.')
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
    role: str = 'student'
    crew_avatar: str = 'steward'
    group_code: str = 'EASA-ALPHA-1'
    referred_by: Optional[str] = ''

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

class BuySkinModel(BaseModel):
    phone_number: str
    skin_name: str
    cost: int

class UploadLessonModel(BaseModel):
    teacher_name: str
    group_code: str
    lesson_title: str
    pdf_url: str
    lesson_notes: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM iro_crew_users_v10 WHERE phone_number = %s;", (data.phone_number,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered.")
    
    cur.execute(
        "INSERT INTO iro_crew_users_v10 (phone_number, full_name, password, recovery_pin, role, crew_avatar, group_code, referred_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *;",
        (data.phone_number, data.full_name, data.password, data.recovery_pin, data.role, data.crew_avatar, data.group_code, data.referred_by)
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
    cur.execute("SELECT * FROM iro_crew_users_v10 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
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
    cur.execute("SELECT * FROM iro_crew_users_v10 WHERE phone_number = %s AND recovery_pin = %s;", (data.phone_number, data.recovery_pin))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid recovery PIN.")
    cur.execute("UPDATE iro_crew_users_v10 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/academy/content")
def get_academy_content(group_code: str = 'EASA-ALPHA-1'):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM iro_curriculum_v10 ORDER BY year_level ASC, node_order ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM iro_drills_v10 ORDER BY year_level ASC, id ASC;")
    drills = cur.fetchall()
    cur.execute("SELECT * FROM iro_shop_skins_v10 ORDER BY category ASC, cost ASC;")
    skins = cur.fetchall()
    cur.execute("SELECT * FROM instructor_lessons_v10 WHERE group_code = %s ORDER BY id DESC;", (group_code,))
    lessons = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "drills": drills, "skins": skins, "lessons": lessons}

@app.post("/api/teacher/upload")
def upload_lesson(data: UploadLessonModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO instructor_lessons_v10 (teacher_name, group_code, lesson_title, pdf_url, lesson_notes) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (data.teacher_name, data.group_code, data.lesson_title, data.pdf_url, data.lesson_notes)
    )
    lesson = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "lesson": lesson}

@app.post("/api/shop/buy")
def buy_skin(data: BuySkinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM iro_crew_users_v10 WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    if not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    
    if student["xp_points"] < data.cost:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough stars/XP!")
    
    new_xp = student["xp_points"] - data.cost
    cur.execute("UPDATE iro_crew_users_v10 SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated_student = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "student": updated_student}

@app.post("/api/drill/verify")
def verify_drill(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM iro_drills_v10 WHERE id = %s;", (data.drill_id,))
    drill = cur.fetchone()
    cur.execute("SELECT * FROM iro_crew_users_v10 WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    
    if not drill or not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found.")
    
    correct_term = drill["term_en"].strip().lower()
    user_input = data.user_answer.strip().lower()
    
    similarity = difflib.SequenceMatcher(None, user_input, correct_term).ratio()
    
    if user_input == correct_term:
        cur.execute("UPDATE iro_crew_users_v10 SET xp_points = xp_points + 25 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": "Perfect execution! +25 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    elif similarity >= 0.75:
        cur.execute("UPDATE iro_crew_users_v10 SET xp_points = xp_points + 15 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": f"Accepted with minor typo! Official: '{drill['term_en']}'. +15 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    else:
        new_hearts = max(0, student["hearts"] - 1)
        cur.execute("UPDATE iro_crew_users_v10 SET hearts = %s WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (new_hearts, data.phone_number))
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
    <title>Iro Crew Academy Elite</title>
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
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        [dir="rtl"] * { font-family: 'Tajawal', sans-serif !important; }
        
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        
        .app-shell { width: 100%; max-width: 580px; background: var(--surface); border-radius: 36px; padding: 2.2rem; border: 1px solid var(--border-glow); box-shadow: 0 45px 90px rgba(0, 0, 0, 0.95), 0 0 40px rgba(56, 189, 248, 0.08); position: relative; overflow: hidden; }
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 1.25rem; color: var(--accent); letter-spacing: -0.5px; }
        .brand-title img { width: 38px; height: 38px; filter: drop-shadow(0 0 10px var(--accent-glow)); }
        
        .header-controls { display: flex; align-items: center; gap: 8px; }
        .shop-icon-btn { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 10px; width: 36px; height: 36px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: all 0.2s; font-size: 1.1rem; }
        .shop-icon-btn:hover { border-color: var(--accent); background: var(--accent-glow); box-shadow: 0 0 15px var(--accent-glow); }

        .lang-switch { display: flex; gap: 4px; }
        .lang-badge { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 8px; padding: 5px 9px; font-size: 0.7rem; font-weight: 800; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-badge.active, .lang-badge:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.5rem; color: white; }
        p.sub-desc { font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.8px; }
        input, select, textarea { width: 100%; padding: 0.95rem 1.1rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 0.95rem; margin-bottom: 1.1rem; outline: none; transition: all 0.2s; }
        input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1.05rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 1rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s, box-shadow 0.2s; box-shadow: 0 6px 20px var(--accent-glow); }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.95; box-shadow: 0 8px 25px var(--accent-glow); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.4rem; font-size: 0.85rem; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 700; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        /* Mascot Banner */
        .mascot-banner { display: flex; align-items: center; gap: 14px; background: linear-gradient(135deg, rgba(56,189,248,0.18) 0%, rgba(2,132,199,0.06) 100%); border: 1px solid rgba(56,189,248,0.35); padding: 0.9rem 1.2rem; border-radius: 18px; margin-bottom: 1.2rem; position: relative; overflow: hidden; }
        .mascot-avatar { font-size: 2.6rem; animation: bounceMascot 2s infinite ease-in-out; }
        @keyframes bounceMascot { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
        .mascot-speech { font-size: 0.82rem; color: #bae6fd; font-weight: 700; line-height: 1.4; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 0.9rem 1.2rem; border-radius: 18px; border: 1px solid var(--border-glow); margin-bottom: 1.2rem; }
        .stat-item { font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; gap: 5px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1.2rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 16px; padding: 1.1rem; text-align: center; cursor: pointer; transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .mode-tile:hover { border-color: var(--accent); background: var(--surface-card-hover); transform: translateY(-3px); box-shadow: 0 10px 25px rgba(56,189,248,0.15); }
        .mode-tile h4 { font-size: 0.88rem; font-weight: 800; margin-top: 6px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 22px; padding: 1.6rem; border: 1px solid var(--border-glow); margin-bottom: 1.2rem; position: relative; min-height: 280px; }
        
        .path-container { display: flex; flex-direction: column; align-items: center; gap: 18px; padding: 10px 0; max-height: 260px; overflow-y: auto; }
        .path-node { width: 62px; height: 62px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); display: flex; justify-content: center; align-items: center; font-weight: 900; font-size: 1.15rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s, box-shadow 0.2s; position: relative; border: 3px solid #bae6fd; }
        .path-node:hover { transform: scale(1.12); box-shadow: 0 0 35px var(--accent); }
        .path-node:nth-child(even) { transform: translateX(30px); }
        .path-node:nth-child(odd) { transform: translateX(-30px); }

        .timer-bar { width: 100%; height: 5px; background: var(--border); border-radius: 3px; margin-bottom: 1.2rem; overflow: hidden; }
        .timer-progress { width: 100%; height: 100%; background: var(--warning); transition: width 1s linear; }

        .inline-feedback { text-align: center; font-size: 0.85rem; font-weight: 800; margin-top: 10px; min-height: 24px; }

        .toast-popup { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 14px 28px; border-radius: 35px; font-weight: 800; font-size: 0.9rem; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); z-index: 4000; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
        .toast-popup.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast-popup">Notification</div>

    <!-- ONBOARDING ROLE SELECTION MODAL (Pop-up on first registration/login) -->
    <div id="onboarding-modal" style="position:fixed; inset:0; background:rgba(2,6,23,0.92); backdrop-filter:blur(10px); display:flex; justify-content:center; align-items:center; z-index:5000; opacity:0; pointer-events:none; transition:opacity 0.3s;">
        <div style="background:var(--surface-card); border:1px solid var(--border-glow); border-radius:30px; padding:2.5rem; width:90%; max-width:440px; text-align:center; box-shadow:0 30px 60px rgba(0,0,0,0.9);">
            <div style="font-size:3rem; margin-bottom:0.5rem;" id="modal-char-emoji">✈️</div>
            <h3 style="font-size:1.4rem; font-weight:900; color:white; margin-bottom:0.4rem;" id="modal-heading">Choose Your Academy Avatar</h3>
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.8rem;">Select your professional crew character to begin your training flight path.</p>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:1.8rem;">
                <div onclick="selectAvatarRole('steward')" id="card-steward" style="background:var(--bg-deep); border:2px solid var(--border-glow); border-radius:20px; padding:1.2rem; cursor:pointer; transition:all 0.2s;">
                    <div style="font-size:2.2rem; margin-bottom:6px;">👔</div>
                    <b style="color:white; font-size:0.9rem;">Steward</b>
                    <div style="color:var(--text-muted); font-size:0.7rem; margin-top:2px;">Male Professional</div>
                </div>
                <div onclick="selectAvatarRole('hostess')" id="card-hostess" style="background:var(--bg-deep); border:2px solid var(--border-glow); border-radius:20px; padding:1.2rem; cursor:pointer; transition:all 0.2s;">
                    <div style="font-size:2.2rem; margin-bottom:6px;">👗</div>
                    <b style="color:white; font-size:0.9rem;">Hostess</b>
                    <div style="color:var(--text-muted); font-size:0.7rem; margin-top:2px;">Female Professional</div>
                </div>
            </div>

            <button class="btn-action" onclick="confirmAvatarSelection()" id="modal-start-btn">Take Off & Start Learning 🚀</button>
        </div>
    </div>

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Logo">
                <span id="txt-brand">Iro Crew</span>
            </div>
            <div class="header-controls">
                <div class="shop-icon-btn" onclick="playAudio('click'); openShop()" title="Uniform Boutique">🎁</div>
                <div class="lang-switch">
                    <button class="lang-badge active" onclick="playAudio('click'); setLanguage('en')">EN</button>
                    <button class="lang-badge" onclick="playAudio('click'); setLanguage('fr')">FR</button>
                    <button class="lang-badge" onclick="playAudio('click'); setLanguage('ar')">AR</button>
                </div>
            </div>
        </div>

        <!-- 1. SIGN IN SCREEN -->
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

        <!-- 2. REGISTER SCREEN -->
        <div id="screen-register" class="hidden">
            <h2 id="reg-title">Cadet & Instructor Enrollment</h2>
            <p class="sub-desc" id="reg-sub">Register your official profile for students or teachers.</p>
            
            <label id="reg-lbl-name">Full Name</label>
            <input type="text" id="reg-name" placeholder="First & Last Name" />

            <label id="reg-lbl-phone">Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label id="reg-lbl-pass">Password</label>
            <input type="password" id="reg-pass" placeholder="Secure password" />

            <label id="reg-lbl-pin">Recovery PIN (4-6 digits)</label>
            <input type="password" id="reg-pin" placeholder="e.g. 2026" maxlength="6" />

            <label id="reg-lbl-type">Account Type</label>
            <select id="reg-role" onchange="toggleTeacherFields()">
                <option value="student">👨‍‍🎓 Student Cadet</option>
                <option value="teacher">👩‍🏫 Academy Instructor / Teacher</option>
            </select>

            <div id="student-group-div">
                <label id="reg-lbl-group">Study Group Code</label>
                <input type="text" id="reg-group" value="EASA-ALPHA-1" placeholder="e.g. EASA-ALPHA-1" />
            </div>
            
            <button class="btn-action" onclick="playAudio('click'); submitRegister()" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); color: white;" id="reg-btn-sub">Initialize Profile</button>
            
            <div class="footer-nav">
                <a onclick="playAudio('click'); navigateTo('screen-login')" id="reg-back">Already have an account? Sign In</a>
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
            
            <button class="btn-action" onclick="playAudio('click'); submitReset()" style="background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); color: var(--bg-deep);" id="res-btn-sub">Update Credentials</button>
            
            <div class="footer-nav">
                <a onclick="playAudio('click'); navigateTo('screen-login')" id="res-back">Back to Sign In</a>
            </div>
        </div>

        <!-- 4. GAMIFIED DASHBOARD -->
        <div id="screen-dashboard" class="hidden">
            <!-- Animated Cute Character Banner -->
            <div class="mascot-banner">
                <div class="mascot-avatar" id="mascot-emoji">👔</div>
                <div class="mascot-speech" id="mascot-speech">"Welcome aboard, Captain! Ready to master your professional academy modules?"</div>
            </div>

            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1rem; color: var(--accent); font-weight: 900;">Cadet</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;" id="dash-skin">Standard Aviator Suit</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">850</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">15</span></div>
                </div>
            </div>

            <!-- Main Hub Grid -->
            <div class="mode-grid" id="main-grid-container">
                <div class="mode-tile" onclick="playAudio('click'); launchYearPath(1)">
                    <span style="font-size: 1.4rem;">📖</span>
                    <h4 id="tile-year1">First Year</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); launchYearPath(2)">
                    <span style="font-size: 1.4rem;">🏆</span>
                    <h4 id="tile-year2">Second Year</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); launchDrillHub(1)">
                    <span style="font-size: 1.4rem;">⌨️</span>
                    <h4 id="tile-typing">Year 1 Drills</h4>
                </div>
                <div class="mode-tile" onclick="playAudio('click'); openStudentReferral()">
                    <span style="font-size: 1.4rem;">🤝</span>
                    <h4 id="tile-referral">Invite Friends</h4>
                </div>
            </div>

            <!-- Teacher Upload Box (Appears only for instructors) -->
            <div id="teacher-command-panel" class="hidden" style="background:var(--surface-card); border:1px solid var(--border-glow); padding:1.2rem; border-radius:18px; margin-bottom:1.2rem;">
                <h3 style="font-size:1rem; color:var(--warning); margin-bottom:0.4rem; font-weight:900;">👩‍🏫 Instructor Lesson Broadcast</h3>
                <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.8rem;">Upload PDF documents and lesson notes for your student group.</p>
                <input type="text" id="teach-title" placeholder="Lesson Title (e.g. SEP Emergency Procedures PDF)" style="margin-bottom:0.6rem;" />
                <input type="text" id="teach-url" placeholder="PDF File URL / Link" style="margin-bottom:0.6rem;" />
                <textarea id="teach-notes" placeholder="Instructor notes & instructions..." style="width:100%; height:70px; background:var(--bg-deep); color:white; border:1px solid var(--border-glow); border-radius:12px; padding:0.8rem; font-size:0.85rem; margin-bottom:0.8rem; outline:none;"></textarea>
                <button class="btn-action" onclick="playAudio('click'); submitTeacherLesson()" style="background:var(--warning); color:var(--bg-deep); padding:0.8rem;">Broadcast to Group 📢</button>
            </div>

            <div id="simulation-box" class="card-container"></div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="playAudio('click'); resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1;" id="btn-menu">← Hub</button>
                <button class="btn-action" onclick="playAudio('click'); logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1;" id="btn-logout">Logout 🚪</button>
            </div>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('iro_crew_user') || 'null');
        let academyData = { modules: [], drills: [], skins: [], lessons: [] };
        let activeLang = localStorage.getItem('iro_crew_lang') || 'en';
        let currentDrillList = [];
        let drillPointer = 0;
        let timerInterval = null;
        let secondsLeft = 30;
        let pendingRegistrationData = null;

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
                tileYear1: "First Year", tileYear2: "Second Year", tileTyping: "Year 1 Drills", tileReferral: "Invite Friends",
                menuBtn: "← Hub", logoutBtn: "Logout 🚪"
            },
            fr: {
                loginTitle: "Portail Personnel de Cabine", loginSub: "Accédez au programme professionnel accrédité EASA/ICAO.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter au simulateur",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                tileYear1: "Première Année", tileYear2: "Seconde Année", tileTyping: "Drills Année 1", tileReferral: "Parrainer",
                menuBtn: "← Menu", logoutBtn: "Déconnexion 🚪"
            },
            ar: {
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى المنهج المهني المعتمد من EASA/ICAO.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول للمحاكي",
                regNav: "إنشاء حساب", resetNav: "هل نسيت كلمة المرور؟",
                tileYear1: "السنة الأولى", tileYear2: "السنة الثانية", tileTyping: "تدريبات السنة 1", tileReferral: "دعوة الأصدقاء",
                menuBtn: "← القائمة", logoutBtn: "تسجيل الخروج 🚪"
            }
        };

        window.onload = function() {
            setLanguage(activeLang);
            if(sessionUser) {
                updateDashboardUI();
                navigateTo('screen-dashboard');
                fetchAcademyContent();
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

            if(sessionUser.role === 'teacher') {
                document.getElementById('teacher-command-panel').classList.remove('hidden');
            } else {
                document.getElementById('teacher-command-panel').classList.add('hidden');
            }
        }

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

        function toggleTeacherFields() {
            const role = document.getElementById('reg-role').value;
            const groupDiv = document.getElementById('student-group-div');
            if(role === 'teacher') {
                groupDiv.style.display = 'none';
            } else {
                groupDiv.style.display = 'block';
            }
        }

        function logoutUser() {
            if(timerInterval) clearInterval(timerInterval);
            localStorage.removeItem('iro_crew_user');
            sessionUser = null;
            navigateTo('screen-login');
            showToast('Logged out successfully.');
        }

        function setLanguage(lang) {
            activeLang = lang;
            localStorage.setItem('iro_crew_lang', lang);
            document.querySelectorAll('.lang-badge').forEach(b => b.classList.remove('active'));
            if(event && event.target) event.target.classList.add('active');
            
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
                document.getElementById('tile-typing').innerText = t.tileTyping;
                document.getElementById('tile-referral').innerText = t.tileReferral;
                document.getElementById('btn-menu').innerText = t.menuBtn;
                document.getElementById('btn-logout').innerText = t.logoutBtn;
            }
        }

        async function submitRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();
            const role = document.getElementById('reg-role').value;
            const group_code = role === 'teacher' ? 'INSTRUCTOR-HUB' : document.getElementById('reg-group').value.trim();

            if(!full_name || !phone_number || !password || !recovery_pin) { showToast('Complete all fields', true); return; }

            pendingRegistrationData = { full_name, phone_number, password, recovery_pin, role, group_code, crew_avatar: 'steward' };
            
            // Show Onboarding Avatar Modal for selection
            document.getElementById('onboarding-modal').style.opacity = '1';
            document.getElementById('onboarding-modal').style.pointerEvents = 'auto';
        }

        let selectedAvatar = 'steward';
        function selectAvatarRole(role) {
            playAudio('click');
            selectedAvatar = role;
            document.getElementById('card-steward').style.borderColor = role === 'steward' ? 'var(--accent)' : 'var(--border-glow)';
            document.getElementById('card-hostess').style.borderColor = role === 'hostess' ? 'var(--accent)' : 'var(--border-glow)';
            document.getElementById('modal-char-emoji').innerText = role === 'hostess' ? '👗' : '👔';
        }

        async function confirmAvatarSelection() {
            playAudio('success');
            if(pendingRegistrationData) {
                pendingRegistrationData.crew_avatar = selectedAvatar;
                const res = await fetch('/api/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(pendingRegistrationData)
                });
                const data = await res.json();
                document.getElementById('onboarding-modal').style.opacity = '0';
                document.getElementById('onboarding-modal').style.pointerEvents = 'none';

                if(res.ok) {
                    showToast('Profile created successfully! Please sign in.');
                    navigateTo('screen-login');
                } else {
                    showToast(data.detail || 'Registration failed', true);
                }
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
                localStorage.setItem('iro_crew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
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
            const group = sessionUser ? sessionUser.group_code : 'EASA-ALPHA-1';
            const res = await fetch(`/api/academy/content?group_code=${group}`);
            academyData = await res.json();
            resetToMenu();
        }

        function resetToMenu() {
            if(timerInterval) clearInterval(timerInterval);
            let lessonsHtml = '';
            if(academyData.lessons && academyData.lessons.length > 0) {
                lessonsHtml = `
                    <div style="margin-top:1.2rem; background:var(--bg-deep); padding:1rem; border-radius:14px; border:1px solid var(--border-glow);">
                        <b style="color:var(--accent); font-size:0.85rem;">📚 Instructor Broadcasts (${sessionUser.group_code}):</b>
                        <div style="margin-top:8px; max-height:100px; overflow-y:auto; display:flex; flex-direction:column; gap:6px;">
                            ${academyData.lessons.map(l => `
                                <div style="display:flex; justify-content:space-between; align-items:center; background:var(--surface-card); padding:6px 10px; border-radius:8px;">
                                    <span style="font-size:0.78rem; color:white;"><b>${l.lesson_title}</b> (${l.teacher_name})</span>
                                    <a href="${l.pdf_url}" target="_blank" style="font-size:0.75rem; color:var(--accent); font-weight:800; text-decoration:none;">Open PDF 📄</a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year</b> or <b>Second Year</b> above to explore your curriculum path, or test your knowledge in drills.</p>
                ${lessonsHtml}
            `;
        }

        async function submitTeacherLesson() {
            const lesson_title = document.getElementById('teach-title').value.trim();
            const pdf_url = document.getElementById('teach-url').value.trim();
            const lesson_notes = document.getElementById('teach-notes').value.trim();

            if(!lesson_title || !pdf_url) { showToast('Enter lesson title and PDF URL', true); return; }

            const res = await fetch('/api/teacher/upload', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ teacher_name: sessionUser.full_name, group_code: sessionUser.group_code, lesson_title, pdf_url, lesson_notes })
            });
            if(res.ok) {
                showToast('Lesson broadcasted successfully to all students!');
                document.getElementById('teach-title').value = '';
                document.getElementById('teach-url').value = '';
                document.getElementById('teach-notes').value = '';
                fetchAcademyContent();
            } else {
                showToast('Broadcast failed', true);
            }
        }

        function launchYearPath(yearNum) {
            if(timerInterval) clearInterval(timerInterval);
            const box = document.getElementById('simulation-box');
            const yearMods = academyData.modules.filter(m => m.year_level === yearNum);

            document.getElementById('mascot-speech').innerText = `"Let's master Year ${yearNum} official academy manuals!"`;

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="font-size: 1.1rem; color: var(--accent); font-weight: 900;">Year ${yearNum} Interactive Path</h3>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Duolingo-Style Roadmap</span>
                </div>
                <div class="path-container">
                    ${yearMods.map((mod, idx) => {
                        let title = mod.title_en;
                        if(activeLang === 'ar') title = mod.title_ar;
                        if(activeLang === 'fr') title = mod.title_fr;
                        return `
                            <div class="path-node" onclick="playAudio('click'); viewModuleDetail(${mod.id})" title="${title}">
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
            let content = mod.content_en;
            if(activeLang === 'ar') { title = mod.title_ar; content = mod.content_ar; }
            if(activeLang === 'fr') { title = mod.title_fr; content = mod.content_fr; }

            document.getElementById('mascot-speech').innerText = `"Reading professional manuals guarantees cadet excellence!"`;

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <span style="font-size: 0.72rem; font-weight: 800; background: rgba(56,189,248,0.15); color: var(--accent); padding: 4px 10px; border-radius: 6px;">EASA OFFICIAL MANUAL : ${mod.category}</span>
                <h3 style="font-size: 1.15rem; margin: 0.8rem 0; color: white; font-weight: 900; line-height: 1.4;">${title}</h3>
                <div style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 1.5rem; background: var(--bg-deep); padding: 1.2rem; border-radius: 16px; border: 1px solid var(--border-glow); max-height: 220px; overflow-y: auto; white-space: pre-line;">${content}</div>
                <button class="btn-action" onclick="playAudio('click'); launchYearPath(${mod.year_level})">← Back to Roadmap</button>
            `;
        }

        function launchDrillHub(yearNum) {
            currentDrillList = academyData.drills.filter(d => d.year_level === yearNum);
            drillPointer = 0;
            if(currentDrillList.length === 0) {
                showToast('No drills found for this year.', true);
                return;
            }
            launchDrillCard(yearNum);
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
            playAudio('error');
            document.getElementById('inline-msg').style.color = 'var(--warning)';
            document.getElementById('inline-msg').innerText = `Official Answer: "${termEn}"`;
        }

        function launchDrillCard(yearNum) {
            if(timerInterval) clearInterval(timerInterval);
            const box = document.getElementById('simulation-box');
            const term = currentDrillList[drillPointer % currentDrillList.length];

            let hint = term.hint_en;
            let promptTerm = term.term_ar;
            if(activeLang === 'ar') { hint = term.hint_ar; promptTerm = term.term_en; }
            if(activeLang === 'fr') { hint = term.hint_fr; promptTerm = term.term_fr; }

            document.getElementById('mascot-speech').innerText = `"Drill Active: Type precise EASA terminology!"`;

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: var(--success);">DRILL (${(drillPointer % currentDrillList.length) + 1}/${currentDrillList.length})</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted);" id="timer-text">30s remaining</span>
                </div>
                <div class="timer-bar"><div id="timer-fill" class="timer-progress"></div></div>
                <div style="font-size: 1.2rem; font-weight: 900; color: white; margin-bottom: 4px;">Translate: ${promptTerm}</div>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem;">Hint: ${hint}</div>
                <input type="text" id="typing-input" placeholder="Type exact English term..." autocomplete="off" />
                <button class="btn-action" onclick="verifyDrillInput(${yearNum}, ${term.id})" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); color: white; margin-bottom: 0.8rem;">Validate Spelling ✓</button>
                <div id="inline-msg" class="inline-feedback" style="color: var(--text-muted);"></div>
                <div id="reveal-container" style="text-align: center; margin-top: 6px;"></div>
            `;
            start30SecTimer(() => {
                document.getElementById('reveal-container').innerHTML = `<button onclick="revealAnswer('${term.term_en}')" style="background:none; border:1px solid var(--warning); color:var(--warning); padding:5px 14px; border-radius:8px; font-weight:800; font-size:0.8rem; cursor:pointer;">Reveal Answer 💡</button>`;
            });
        }

        async function verifyDrillInput(yearNum, drillId) {
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
            sessionUser.xp_points = data.xp;
            sessionUser.hearts = data.hearts;
            sessionUser.streak = data.streak;
            localStorage.setItem('iro_crew_user', JSON.stringify(sessionUser));

            if(data.correct) {
                playAudio('success');
                inlineMsg.style.color = 'var(--success)';
                inlineMsg.innerText = data.message;
                drillPointer++;
                setTimeout(() => launchDrillCard(yearNum), 1500);
            } else {
                playAudio('error');
                inlineMsg.style.color = 'var(--danger)';
                inlineMsg.innerText = data.message;
            }
        }

        function openStudentReferral() {
            if(timerInterval) clearInterval(timerInterval);
            document.getElementById('mascot-speech').innerText = `"Invite your fellow cadets and earn bonus XP stars!"`;
            const box = document.getElementById('simulation-box');
            const refLink = `https://iro-crew-academy.up.railway.app/?ref=${sessionUser.phone_number}`;

            box.innerHTML = `
                <h3 style="font-size: 1.1rem; color: var(--accent); font-weight: 900; margin-bottom: 0.6rem;">🤝 Invite Friends & Earn Stars</h3>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.2rem; line-height: 1.5;">Share your exclusive cadet referral link with friends. When they join your study group, you both earn +100 XP Stars!</p>
                <input type="text" value="${refLink}" readonly style="background:var(--bg-deep); color:var(--accent); font-weight:700; text-align:center; margin-bottom:1rem;" />
                <button class="btn-action" onclick="navigator.clipboard.writeText('${refLink}'); showToast('Referral link copied to clipboard!');" style="background:var(--success); color:white;">Copy Link 📋</button>
            `;
        }

        function openShop(category = 'male') {
            if(timerInterval) clearInterval(timerInterval);
            document.getElementById('mascot-speech').innerText = `"Customize your crew uniform with stars!"`;
            const box = document.getElementById('simulation-box');
            const filteredSkins = academyData.skins.filter(s => s.category === category);

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.05rem; color: #a78bfa; font-weight: 900;">🎁 Uniform Boutique</h3>
                    <span style="font-size: 0.8rem; color: var(--warning); font-weight: 800;">⭐ ${sessionUser.xp_points} Stars</span>
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 0.8rem;">
                    <button onclick="playAudio('click'); openShop('male')" style="flex:1; padding:8px; border-radius:10px; border:1px solid ${category==='male'?'var(--accent)':'var(--border)'}; background:${category==='male'?'var(--accent-glow)':'var(--bg-deep)'}; color:white; font-weight:800; font-size:0.8rem; cursor:pointer;">👔 Steward Collection</button>
                    <button onclick="playAudio('click'); openShop('female')" style="flex:1; padding:8px; border-radius:10px; border:1px solid ${category==='female'?'var(--accent)':'var(--border)'}; background:${category==='female'?'var(--accent-glow)':'var(--bg-deep)'}; color:white; font-weight:800; font-size:0.8rem; cursor:pointer;">👗 Hostess Collection</button>
                </div>
                <div style="max-height: 190px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
                    ${filteredSkins.map(skin => `
                        <div style="background: var(--bg-deep); padding: 0.7rem 1rem; border-radius: 12px; border: 1px solid var(--border-glow); display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.6rem;">${skin.preview_svg}</span>
                                <div>
                                    <b style="color: white; font-size: 0.85rem;">${skin.skin_name}</b>
                                    <div style="color: var(--text-muted); font-size: 0.7rem;">${skin.desc_en}</div>
                                </div>
                            </div>
                            <button onclick="playAudio('click'); buySkin('${skin.skin_name}',${skin.cost}, '${category}')" style="background: #8b5cf6; color: white; border: none; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 0.75rem; cursor: pointer;">${skin.cost} ⭐</button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        async function buySkin(skinName, cost, category) {
            const res = await fetch('/api/shop/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: sessionUser.phone_number, skin_name: skinName, cost: cost })
            });
            const data = await res.json();
            if(res.ok) {
                playAudio('success');
                sessionUser = data.student;
                localStorage.setItem('iro_crew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast(`Successfully equipped: ${skinName}!`);
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
