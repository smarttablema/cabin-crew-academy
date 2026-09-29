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

app = FastAPI(title="AeroCrew Pro Academy Ultimate", version="9.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aviation_academy_students_v9 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            crew_role VARCHAR(20) DEFAULT 'steward',
            active_skin VARCHAR(50) DEFAULT 'Standard Uniform',
            xp_points INT DEFAULT 750,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 14,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mascot_shop_skins_v9 (
            id SERIAL PRIMARY KEY,
            category VARCHAR(20),
            skin_name VARCHAR(50),
            cost INT,
            icon VARCHAR(20),
            desc_en TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comprehensive_academy_modules_v9 (
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS official_drills_v9 (
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
    
    # Seed Massive Shop Skins (Male & Female Categories)
    cur.execute("""
        INSERT INTO mascot_shop_skins_v9 (category, skin_name, cost, icon, desc_en)
        VALUES 
        -- MALE CATEGORY
        ('male', 'Junior Steward Suit', 50, '👔', 'Classic professional grey steward suit.'),
        ('male', 'Senior Steward Uniform', 100, '👔', 'Executive tailored suit with silver tie.'),
        ('male', 'First Officer Epaulets', 180, '🎖️', 'Two golden stripes insignia.'),
        ('male', 'Captain Gold Wings', 250, '👨‍✈️', 'Four gold stripes and captain cap.'),
        ('male', 'Supersonic Aviator Shades', 90, '🕶️', 'Sleek pilot sunglasses.'),
        ('male', 'VIP Charter Blazer', 150, '🧥', 'Custom navy blue private jet blazer.'),
        ('male', 'Chief Purser Badging', 200, '⭐', 'Gold supervisor lapel badge.'),
        ('male', 'Global Express Scarf', 110, '🧣', 'Silk necktie for long-haul routes.'),
        
        -- FEMALE CATEGORY
        ('female', 'Junior Hostess Tailoring', 50, '👗', 'Elegant professional skirt suit.'),
        ('female', 'Senior Hostess Uniform', 100, '👗', 'Designer airline couture dress.'),
        ('female', 'Lead Purser Silk Scarf', 130, '🧣', 'Signature red designer neck scarf.'),
        ('female', 'First Officer Wings', 180, '👩‍✈️', 'Silver pilot wings and epaulets.'),
        ('female', 'Captain Commander Cap', 250, '👩‍✈️', 'Official four-stripe captain hat.'),
        ('female', 'Global Chic Handbag', 90, '👜', 'Matching leather cabin luggage bag.'),
        ('female', 'Executive Brooch Pin', 110, '💎', 'Gold diamond aviation wing brooch.'),
        ('female', 'First Class Specialist', 200, '✨', 'Premium service gold badge pin.')
        ON CONFLICT DO NOTHING;
    """)

    # Seed Curriculum Modules (Year 1 & Year 2)
    cur.execute("""
        INSERT INTO comprehensive_academy_modules_v9 (year_level, node_order, category, title_en, title_ar, title_fr, content_en, content_ar, content_fr)
        VALUES 
        (1, 1, 'SEP', 'Module 1: EASA Regulatory Framework & Pre-Flight Safety', 'الوحدة 1: لوائح EASA وفحوصات السلامة', 'Module 1: Cadre EASA et sécurité', 
         '1. Regulatory Framework: Cabin crew operate under European Union Aviation Safety Agency (EASA) Part-CC regulations.\n\n2. Pre-Flight Checks: Mandatory inspections of exit doors, slide pressure gauges, ELT, life vests, and PBO oxygen bottles.\n\n3. Sterile Flight Deck: Strict communication protocols during taxi, takeoff, and landing.',
         '1. الإطار التنظيمي: يعمل طاقم المقصورة تحت لوائح EASA الجزء CC.\n\n2. فحوصات ما قبل الرحلة: عمليات تفتيش إلزامية لأبواب المخارج ومعدات الطوارئ.\n\n3. قمرة القيادة المعقمة: بروتوكولات اتصال صارمة أثناء الإقلاع والهبوط.',
         '1. Cadre réglementaire : Les équipages opèrent sous la réglementation EASA Part-CC.\n\n2. Vérifications pré-vol : Inspections obligatoires des portes et équipements de secours.\n\n3. Cockpit stérile : Protocoles de communication stricts.'),
        
        (1, 2, 'SEP', 'Module 2: Emergency Evacuation & 90-Second Rule', 'الوحدة 2: الإخلاء الطارئ وقاعدة 90 ثانية', 'Module 2: Évacuation d urgence', 
         '1. The 90-Second Mandate: Complete aircraft evacuation must be achievable within 90 seconds using 50% exits.\n\n2. Slide Arming & Cross-Checking: Manual slide inflation checks and door cross-checks.\n\n3. Crowd Control: Authoritative commands ("LEAVE ALL BAGS, JUMP AND SLIDE!").',
         '1. تفويض 90 ثانية: يجب إخلاء الطائرة بالكامل خلال 90 ثانية.\n\n2. تجهيز المنحدرات: فحوصات يفحصها الطاقم للأبواب والمنحدرات.\n\n3. السيطرة على الحشود: أوامر حاسمة بصوت قوي.',
         '1. La règle des 90 secondes : Évacuation complète en 90 secondes maximum.\n\n2. Armement des toboggans : Vérifications croisées des portes.\n\n3. Gestion des foules : Commandes vocales directives.'),

        (1, 3, 'Cargo/DG', 'Module 3: Dangerous Goods & Lithium Batteries', 'الوحدة 3: البضائع الخطرة وبطاريات الليثيوم', 'Module 3: Marchandises dangereuses', 
         '1. Hazmat Recognition: Identifying hidden dangerous goods in passenger baggage.\n\n2. Thermal Runaway: Immediate response to overheating portable electronic devices (PEDs).\n\n3. Mitigation: Pouring water, deploying PBE, and utilizing fire containment bags.',
         '1. التعرف على المواد الخطرة: تحديد البضائع الخطرة المخفية.\n\n2. الهروب الحراري: الاستجابة الفورية للأجهزة الإلكترونية المحمولة الساخنة.\n\n3. التخفيف: صب الماء واستخدام أكياس احتواء الحريق.',
         '1. Reconnaissance des matières : Identifier les marchandises cachées.\n\n2. Emballement thermique : Réaction immédiate face aux appareils électroniques en surchauffe.\n\n3. Atténuation : Utilisation d eau et de sacs de confinement.'),

        (1, 4, 'Medical', 'Module 4: Aeromedical First Aid & Hypoxia', 'الوحدة 4: الإسعافات الأولية ونقص الأكسجين', 'Module 4: Premiers secours et hypoxie', 
         '1. Rapid Decompression: Immediate donning of portable oxygen bottles.\n\n2. Hypoxia Symptoms: Recognizing tunnel vision, cyanosis, and dizziness.\n\n3. CPR & AED: Cardiac arrest management and Heimlich maneuver.',
         '1. إزالة الضغط السريع: ارتداء اسطوانات الأكسجين المحمولة فوراً.\n\n2. أعراض نقص الأكسجين: التعرف على الرؤية النفقية والزرقة والدوخة.\n\n3. إنعاش القلب وجهاز الإزالة: إدارة السكتة القلبية.',
         '1. Décompression rapide : Enfilage immédiat des bouteilles d oxygène.\n\n2. Symptômes de l hypoxie : Reconnaître la vision tubulaire et la cyanose.\n\n3. RCP et défibrillateur : Gestion des arrêts cardiaques.'),

        (2, 1, 'CRM', 'Module 5: Advanced Crew Resource Management', 'الوحدة 5: إدارة موارد الطاقم المتقدمة', 'Module 5: Gestion CRM avancée', 
         '1. Leadership Dynamics: Multicultural team coordination and conflict resolution.\n\n2. Threat and Error Management (TEM): Proactive operational threat identification.\n\n3. Decision Frameworks: FORCES and DOT-DEDUCT under high stress.',
         '1. ديناميكيات القيادة: تنسيق الفرق متعددة الثقافات وحل النزاعات.\n\n2. إدارة التهديدات والأخطاء (TEM): التحديد الاستباقي للتهديدات.\n\n3. أطر اتخاذ القرار تحت الضغط العالي.',
         '1. Leadership : Coordination d équipes multiculturelles et gestion des conflits.\n\n2. Gestion des menaces et erreurs (TEM).\n\n3. Cadres de décision sous haute pression.'),

        (2, 2, 'AVSEC', 'Module 6: Aviation Security & Threat Levels', 'الوحدة 6: أمن الطيران ومستويات التهديد', 'Module 6: Sûreté et menaces', 
         '1. Unruly Matrix: Four-tier threat management from verbal to physical breach.\n\n2. Bomb Threat Checklists: Systematic cabin search protocols.\n\n3. Flight Deck Defense: Establishing sterile cockpit barriers.',
         '1. مصفوفة المشاغبين: إدارة التهديدات من الفئة الأولى إلى الرابعة.\n\n2. قوائم مراجعة التهديد بالقنابل وفحص المقصورة.\n\n3. دفاع قمرة القيادة وتأمين الحواجز.',
         '1. Matrice des passagers indisciplinés : Gestion des 4 niveaux de menace.\n\n2. Listes de contrôle d alerte à la bombe.\n\n3. Défense du poste de pilotage.')
        ON CONFLICT DO NOTHING;
    """)

    # Seed Expanded, Comprehensive Drills (Separate Year 1 and Year 2 pools with rich terminology)
    cur.execute("""
        INSERT INTO official_drills_v9 (year_level, term_en, term_ar, term_fr, category, hint_en, hint_ar, hint_fr)
        VALUES 
        -- YEAR 1 DRILLS (Extensive pool)
        (1, 'Altimeter', 'مقياس الارتفاع', 'Altimètre', 'Instruments', 'Measures barometric altitude.', 'يقيس الارتفاع الجوي.', 'Mesure l altitude barométrique.'),
        (1, 'Bulkhead', 'الجدار الفاصل', 'Cloison', 'Cabin', 'Structural cabin partition.', 'فاصل هيكلي للمقصورة.', 'Cloison structurelle de cabine.'),
        (1, 'Decompression', 'إزالة الضغط', 'Décompression', 'Emergency', 'Loss of cabin pressurization.', 'فقدان ضغط المقصورة.', 'Perte de pressurisation en cabine.'),
        (1, 'Turbulence', 'مطبات هوائية', 'Turbulence', 'Meteorology', 'Unsteady air currents.', 'تيارات هوائية غير مستقرة.', 'Courants d air instables.'),
        (1, 'Evacuation', 'إخلاء الطائرة', 'Évacuation', 'SEP', 'Rapid emergency passenger exit.', 'خروج طارئ سريع للركاب.', 'Sortie d urgence rapide.'),
        (1, 'Brace Position', 'وضعية الاستعداد', 'Position de sécurité', 'SEP', 'Protective crash position.', 'وضعية الحماية عند الاصطدام.', 'Position de protection antichoc.'),
        (1, 'Halon Extinguisher', 'طفاية هالون', 'Extincteur Halon', 'Fire', 'Class A, B, C fire suppressant.', 'مادة إخماد الحريق للفئات أ، ب، ج.', 'Extincteur pour feux A, B, C.'),
        (1, 'PBE', 'معدات التنفس الواقية', 'PBE', 'Safety', 'Protective Breathing Equipment.', 'معدات التنفس لحماية الدخان.', 'Équipement de protection respiratoire.'),
        (1, 'Oxygen Mask', 'قناع الأكسجين', 'Masque à oxygène', 'Medical', 'Deploys automatically during decompression.', 'ينشر تلقائياً أثناء إزالة الضغط.', 'Se déploie automatiquement.'),
        (1, 'Life Vest', 'سترة النجاة', 'Gilet de sauvetage', 'SEP', 'Flotation device for water ditching.', 'جهاز طفو للهبوط المائي.', 'Dispositif de flottabilité.'),

        -- YEAR 2 DRILLS (Extensive pool)
        (2, 'Crew Resource Management', 'إدارة موارد الطاقم', 'CRM', 'CRM', 'Effective utilization of all resources.', 'الاستفادة الفعالة من جميع الموارد.', 'Utilisation efficace des ressources.'),
        (2, 'Threat and Error Management', 'إدارة التهديدات والأخطاء', 'TEM', 'TEM', 'Proactive safety framework.', 'إطار عمل السلامة الاستباقي.', 'Cadre de sécurité proactif.'),
        (2, 'Sterile Flight Deck', 'قمرة القيادة المعقمة', 'Cockpit stérile', 'AVSEC', 'No non-essential tasks below 10,000 feet.', 'منع المهام غير الضرورية تحت 10000 قدم.', 'Interdiction des tâches non essentielles.'),
        (2, 'Air Marshal', 'مارشال الجو', 'Marshal de l air', 'AVSEC', 'Undercover armed security officer.', 'ضابط أمن مسلح سري.', 'Officier de sécurité armé en civil.'),
        (2, 'Thermal Runaway', 'الهروب الحراري', 'Emballement thermique', 'Cargo', 'Uncontrolled self-heating battery state.', 'حالة بطارية ذاتية التسخين غير مسيطر عليها.', 'État de batterie en surchauffe incontrôlée.'),
        (2, 'Hyperventilation', 'فرط التنفس', 'Hyperventilation', 'Medical', 'Rapid or deep breathing causing dizziness.', 'التنفس السريع المسبب للدوخة.', 'Respiration rapide provoquant des vertiges.'),
        (2, 'Hijack Checklist', 'قائمة اختطاف الطائرة', 'Procédure de détournement', 'AVSEC', 'Transponder emergency code 7500.', 'رمز استجابة الطوارئ 7500.', 'Code transpondeur d urgence 7500.'),
        (2, 'Unruly Passenger', 'راكب مشاغب', 'Passager indisciplinés', 'AVSEC', 'Tier 4 physical breach protocol.', 'بروتوكول الاختراق البدني من الفئة 4.', 'Protocole de violation physique.')
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
    crew_role: str

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

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aviation_academy_students_v9 WHERE phone_number = %s;", (data.phone_number,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered.")
    
    cur.execute(
        "INSERT INTO aviation_academy_students_v9 (phone_number, full_name, password, recovery_pin, crew_role) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (data.phone_number, data.full_name, data.password, data.recovery_pin, data.crew_role)
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
    cur.execute("SELECT * FROM aviation_academy_students_v9 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
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
    cur.execute("SELECT * FROM aviation_academy_students_v9 WHERE phone_number = %s AND recovery_pin = %s;", (data.phone_number, data.recovery_pin))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid recovery PIN.")
    cur.execute("UPDATE aviation_academy_students_v9 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/academy/content")
def get_academy_content():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM comprehensive_academy_modules_v9 ORDER BY year_level ASC, node_order ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM official_drills_v9 ORDER BY year_level ASC, id ASC;")
    drills = cur.fetchall()
    cur.execute("SELECT * FROM mascot_shop_skins_v9 ORDER BY category ASC, cost ASC;")
    skins = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "drills": drills, "skins": skins}

@app.post("/api/shop/buy")
def buy_skin(data: BuySkinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aviation_academy_students_v9 WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    if not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found.")
    
    if student["xp_points"] < data.cost:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough stars/XP!")
    
    new_xp = student["xp_points"] - data.cost
    cur.execute("UPDATE aviation_academy_students_v9 SET xp_points = %s, active_skin = %s WHERE phone_number = %s RETURNING *;", (new_xp, data.skin_name, data.phone_number))
    updated_student = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "student": updated_student}

@app.post("/api/drill/verify")
def verify_drill(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM official_drills_v9 WHERE id = %s;", (data.drill_id,))
    drill = cur.fetchone()
    cur.execute("SELECT * FROM aviation_academy_students_v9 WHERE phone_number = %s;", (data.phone_number,))
    student = cur.fetchone()
    
    if not drill or not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found.")
    
    correct_term = drill["term_en"].strip().lower()
    user_input = data.user_answer.strip().lower()
    
    similarity = difflib.SequenceMatcher(None, user_input, correct_term).ratio()
    
    if user_input == correct_term:
        cur.execute("UPDATE aviation_academy_students_v9 SET xp_points = xp_points + 25 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": "Perfect execution! +25 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    elif similarity >= 0.75:
        cur.execute("UPDATE aviation_academy_students_v9 SET xp_points = xp_points + 15 WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": f"Accepted with minor typo! Official: '{drill['term_en']}'. +15 XP", "xp": res["xp_points"], "hearts": res["hearts"], "streak": res["streak"]}
    else:
        new_hearts = max(0, student["hearts"] - 1)
        cur.execute("UPDATE aviation_academy_students_v9 SET hearts = %s WHERE phone_number = %s RETURNING xp_points, hearts, streak;", (new_hearts, data.phone_number))
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
    <title>AeroCrew Pro Academy Ultimate</title>
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
        
        .lang-switch { display: flex; gap: 6px; }
        .lang-badge { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 10px; padding: 6px 12px; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-badge.active, .lang-badge:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); box-shadow: 0 0 15px var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.5rem; color: white; }
        p.sub-desc { font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.8px; }
        input, select { width: 100%; padding: 1rem 1.2rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 1rem; margin-bottom: 1.2rem; outline: none; transition: all 0.2s; }
        input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1.05rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 1rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s, box-shadow 0.2s; box-shadow: 0 6px 20px var(--accent-glow); }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.95; box-shadow: 0 8px 25px var(--accent-glow); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.4rem; font-size: 0.85rem; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 700; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        /* Mascot Banner */
        .mascot-banner { display: flex; align-items: center; gap: 14px; background: linear-gradient(135deg, rgba(56,189,248,0.15) 0%, rgba(2,132,199,0.05) 100%); border: 1px solid rgba(56,189,248,0.3); padding: 0.9rem 1.2rem; border-radius: 18px; margin-bottom: 1.2rem; position: relative; overflow: hidden; }
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
        .path-node { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); display: flex; justify-content: center; align-items: center; font-weight: 900; font-size: 1.1rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s, box-shadow 0.2s; position: relative; border: 3px solid #bae6fd; }
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

    <div class="app-shell">
        <div class="top-header">
            <div class="brand-title">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Icon">
                <span id="txt-brand">AeroCrew Pro Elite</span>
            </div>
            <div class="lang-switch">
                <button class="lang-badge active" onclick="playAudio('click'); setLanguage('en')">EN</button>
                <button class="lang-badge" onclick="playAudio('click'); setLanguage('fr')">FR</button>
                <button class="lang-badge" onclick="playAudio('click'); setLanguage('ar')">AR</button>
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

            <label id="reg-lbl-role">Crew Role (Character)</label>
            <select id="reg-role">
                <option value="steward">👔 Steward (Male Crew Avatar)</option>
                <option value="hostess">👗 Hostess (Female Crew Avatar)</option>
            </select>
            
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
                    <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;" id="dash-skin">Standard Uniform</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">750</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">14</span></div>
                </div>
            </div>

            <!-- 2x2 Grid -->
            <div class="mode-grid">
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
                <div class="mode-tile" onclick="playAudio('click'); launchDrillHub(2)">
                    <span style="font-size: 1.4rem;">🎙️</span>
                    <h4 id="tile-voice">Year 2 Drills</h4>
                </div>
            </div>

            <button class="btn-action" onclick="playAudio('click'); openShop()" style="background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); color: white; margin-bottom: 0.8rem;" id="shop-btn">🎁 Uniform & Skin Shop (Male / Female)</button>

            <div id="simulation-box" class="card-container"></div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="playAudio('click'); resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1;" id="btn-menu">← Hub</button>
                <button class="btn-action" onclick="playAudio('click'); logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1;" id="btn-logout">Logout 🚪</button>
            </div>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('aerocrew_user') || 'null');
        let academyData = { modules: [], drills: [], skins: [] };
        let activeLang = localStorage.getItem('aerocrew_lang') || 'en';
        let currentDrillList = [];
        let drillPointer = 0;
        let timerInterval = null;
        let secondsLeft = 30;

        // Web Audio API Sound Generator
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
                    osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
                    osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.08); // E5
                    osc.frequency.setValueAtTime(783.99, audioCtx.currentTime + 0.16); // G5
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
                regTitle: "Cadet Enrollment", regSub: "Register your official student training profile.",
                regName: "Full Name", regPass: "Password", regPin: "Recovery PIN (4-6 digits)", regRole: "Crew Role (Character)", regBtn: "Initialize Profile", regBack: "Already have an account? Sign In",
                resTitle: "Recovery PIN Reset", resSub: "Enter your phone and secret recovery PIN.", resNew: "New Password", resBtn: "Update Credentials",
                tileYear1: "First Year", tileYear2: "Second Year", tileTyping: "Year 1 Drills", tileVoice: "Year 2 Drills",
                shopBtn: "🎁 Uniform & Skin Shop (Male / Female)", menuBtn: "← Hub", logoutBtn: "Logout 🚪"
            },
            fr: {
                loginTitle: "Portail Personnel de Cabine", loginSub: "Accédez au programme professionnel accrédité EASA/ICAO.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter au simulateur",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                regTitle: "Inscription Cadet", regSub: "Enregistrez votre profil de formation officiel.",
                regName: "Nom et Prénom", regPass: "Mot de passe", regPin: "PIN de récupération (4-6 chiffres)", regRole: "Rôle (Steward / Hostess)", regBtn: "Initialiser le profil", regBack: "Déjà un compte ? Se connecter",
                resTitle: "Réinitialisation PIN", resSub: "Entrez votre téléphone et votre PIN secret.", resNew: "Nouveau mot de passe", resBtn: "Mettre à jour",
                tileYear1: "Première Année", tileYear2: "Seconde Année", tileTyping: "Drills Année 1", tileVoice: "Drills Année 2",
                shopBtn: "🎁 Boutique d Uniformes (Homme / Femme)", menuBtn: "← Menu", logoutBtn: "Déconnexion 🚪"
            },
            ar: {
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى المنهج المهني المعتمد من EASA/ICAO.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول للمحاكي",
                regNav: "إنشاء حساب", resetNav: "هل نسيت كلمة المرور؟",
                regTitle: "تسجيل المتدرب", regSub: "سجل ملف تدريب الطالب الرسمي الخاص بك.",
                regName: "الاسم الكامل", regPass: "كلمة المرور", regPin: "رمز الاسترداد (4-6 أرقام)", regRole: "الدور المهني (مضيف / مضيفة)", regBtn: "تهيئة الملف الشخصي", regBack: "لديك حساب بالفعل؟ تسجيل الدخول",
                resTitle: "إعادة تعيين الرمز", resSub: "أدخل هاتفك ورقم الرمز السري للاسترداد.", resNew: "كلمة المرور الجديدة", resBtn: "تحديث بيانات الاعتماد",
                tileYear1: "السنة الأولى", tileYear2: "السنة الثانية", tileTyping: "تدريبات السنة 1", tileVoice: "تدريبات السنة 2",
                shopBtn: "🎁 متجر الأزياء والملابس (رجال / نساء)", menuBtn: "← القائمة", logoutBtn: "تسجيل الخروج 🚪"
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
            const emoji = sessionUser.crew_role === 'hostess' ? '👗' : '👔';
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
            ['screen-login', 'screen-register', 'screen-reset', 'screen-dashboard'].forEach(s => document.getElementById(s).classList.add('hidden'));
            document.getElementById(id).classList.remove('hidden');
        }

        function logoutUser() {
            if(timerInterval) clearInterval(timerInterval);
            localStorage.removeItem('aerocrew_user');
            sessionUser = null;
            navigateTo('screen-login');
            showToast('Logged out successfully.');
        }

        function setLanguage(lang) {
            activeLang = lang;
            localStorage.setItem('aerocrew_lang', lang);
            document.querySelectorAll('.lang-badge').forEach(b => b.classList.remove('active'));
            if(event && event.target) event.target.classList.add('active');
            
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
                document.getElementById('reg-lbl-role').innerText = t.regRole;
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
                document.getElementById('shop-btn').innerText = t.shopBtn;
                document.getElementById('btn-menu').innerText = t.menuBtn;
                document.getElementById('btn-logout').innerText = t.logoutBtn;
            }
        }

        async function submitRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();
            const crew_role = document.getElementById('reg-role').value;

            if(!full_name || !phone_number || !password || !recovery_pin) { showToast('Complete all fields', true); return; }

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ full_name, phone_number, password, recovery_pin, crew_role })
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
                localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));
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
            const res = await fetch('/api/academy/content');
            academyData = await res.json();
            resetToMenu();
        }

        function resetToMenu() {
            if(timerInterval) clearInterval(timerInterval);
            document.getElementById('simulation-box').innerHTML = `
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year</b> or <b>Second Year</b> above to explore your curriculum path, or test your knowledge in dedicated drill hubs.</p>
            `;
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

            document.getElementById('mascot-speech').innerText = `"Year ${yearNum} Drill Active: Type precise terminology!"`;

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: var(--success);">YEAR ${yearNum} DRILL (${(drillPointer % currentDrillList.length) + 1}/${currentDrillList.length})</span>
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
            localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));

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

        function openShop(category = 'male') {
            if(timerInterval) clearInterval(timerInterval);
            playAudio('click');
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
                                <span style="font-size: 1.6rem;">${skin.icon}</span>
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
                localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));
                updateDashboardUI();
                showToast(`Successfully unlocked: ${skinName}!`);
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
