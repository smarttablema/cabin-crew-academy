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

app = FastAPI(title="AeroCrew Pro Academy Elite", version="7.1.0")

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
            xp_points INT DEFAULT 450,
            hearts INT DEFAULT 5,
            streak INT DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comprehensive_academy_modules_v7 (
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
        CREATE TABLE IF NOT EXISTS official_drills_v7 (
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
    
    # Seed full, comprehensive, multi-paragraph professional EASA academy curriculum
    cur.execute("""
        INSERT INTO comprehensive_academy_modules_v7 (year_level, node_order, category, title_en, title_ar, title_fr, content_en, content_ar, content_fr)
        VALUES 
        (1, 1, 'SEP', 
         'Module 1: EASA Regulatory Framework & Pre-Flight Safety Checks', 
         'الوحدة 1: إطار لوائح وكالة سلامة الطيران الأوروبية وفحوصات ما قبل الرحلة', 
         'Module 1: Cadre réglementaire EASA et vérifications pré-vol',
         '1. Regulatory Framework: Cabin crew operate under strict European Union Aviation Safety Agency (EASA) regulations, specifically Part-CC and ORO.CC. Cabin crew are designated safety professionals responsible for passenger wellbeing, emergency preparedness, and security enforcement.\n\n2. Pre-Flight Inspection Protocols: Before every sector, mandatory cabin integrity checks must be conducted. Crew members inspect emergency exit doors (checking arming levers, slide pressure gauges, and gust locks), emergency locator transmitters (ELT), megaophones, life vests, portable oxygen cylinders (PBO), and fire suppression equipment (Halon/Water extinguishers and PBE smoke hoods).\n\n3. Sterile Flight Deck & Briefings: Effective communication between the Flight Crew and Cabin Crew is paramount. Standard operating procedures dictate silent review during taxi, takeoff, and landing, with strict entry protocols enforced via cockpit door surveillance systems.',
         '1. الإطار التنظيمي: يعمل طاقم المقصورة تحت لوائح صارمة لوكالة سلامة الطيران الأوروبية (EASA)، وتحديداً الجزء CC و ORO.CC.\n\n2. فحوصات ما قبل الرحلة: إجراء عمليات تفتيش إلزامية لسلامة المقصورة قبل كل رحلة، وفحص أبواب مخارج الطوارئ ومعدات مكافحة الحريق وأجهزة الأكسجين المحمولة.\n\n3. قمرة القيادة المعقمة والإحاطة: التواصل الفعال بين طاقم القيادة والمقصورة أمر بالغ الأهمية.',
         '1. Cadre réglementaire : Les membres d équipage de cabine opèrent sous la réglementation stricte de l AESA (Part-CC et ORO.CC).\n\n2. Protocoles d inspection pré-vol : Avant chaque vol, des contrôles obligatoires d intégrité de la cabine doivent être menés.\n\n3. Cockpit stérile et Briefings : Une communication efficace entre l équipage de conduite et la cabine est primordiale.'),

        (1, 2, 'SEP', 
         'Module 2: Emergency Evacuation & 90-Second Rule Dynamics', 
         'الوحدة 2: الإخلاء الطارئ وديناميكيات قاعدة 90 ثانية', 
         'Module 2: Évacuation d urgence et règle des 90 secondes',
         '1. The 90-Second Mandate: EASA certification standards require that an aircraft must be fully evacuated within 90 seconds using only 50% of available emergency exits under simulated emergency conditions.\n\n2. Slide Deployment & Cross-Checking: Upon command from the Senior Purser or Captain, doors are evaluated for exterior hazards (fire, water, terrain). Slides must be manually inflated if automatic inflation fails. Cross-checking ensures all doors are correctly armed or disarmed during flight transitions.\n\n3. Crowd Control & Brace Commands: Cabin crew must utilize authoritative, commanding vocal projection for brace commands ("HEADS DOWN, STAY DOWN!") and post-evacuation crowd control ("LEAVE ALL BAGS, JUMP AND SLIDE!").',
         '1. تفويض 90 ثانية: تتطلب معايير شهادة EASA إخلاء الطائرة بالكامل خلال 90 ثانية باستخدام 50% فقط من مخارج الطوارئ.\n\n2. نشر المنحدرات والتحقق المتقاطع: بناءً على توجيهات كبير المضيفين، يتم تقييم الأبواب للتأكد من عدم وجود مخاطر خارجية.\n\n3. السيطرة على الحشود وأوامر الاستعداد: يجب على أطقم المقصورة استخدام نبرة صوت قوية وحاسمة لأوامر الاستعداد والسيطرة على الحشود.',
         '1. La règle des 90 secondes : Les normes de certification exigent une évacuation complète en 90 secondes en utilisant 50% des issues.\n\n2. Déploiement des toboggans : Sur ordre du chef de cabine, les portes sont évaluées pour écarter les risques extérieurs.\n\n3. Gestion des foules et positions de sécurité : L équipage doit utiliser des ordres vocaux puissants et directifs.'),

        (1, 3, 'Cargo/DG', 
         'Module 3: Dangerous Goods (Hazmat) & Lithium Battery Thermal Runaway', 
         'الوحدة 3: البضائع الخطرة وحالات الهروب الحراري لبطاريات الليثيوم', 
         'Module 3: Marchandises dangereuses et emballement thermique au lithium',
         '1. Dangerous Goods Classification: Cabin crew are trained to recognize hidden hazardous materials (Class 9 miscellaneous, explosives, compressed gases, flammable liquids, and radioactive items).\n\n2. Lithium-Ion Battery Incidents: In the event of a portable electronic device (PED) overheating or entering thermal runaway in overhead bins or passenger seats, crew must immediately deploy specialized response protocols.\n\n3. Mitigation Procedure: Pour copious amounts of water or non-flammable liquid onto the device to cool thermal cells, deploy PBE (Protective Breathing Equipment), utilize fire gloves, and submerge the device in a dedicated DG fire containment bag.',
         '1. تصنيف البضائع الخطرة: يتم تدريب طاقم المقصورة على التعرف على المواد الخطرة المخفية.\n\n2. حوادث بطاريات الليثيوم أيون: في حالة ارتفاع حرارة الأجهزة الإلكترونية المحمولة، يجب تطبيق بروتوكولات الاستجابة الفورية.\n\n3. إجراءات التخفيف: صب كميات كبيرة من الماء أو السوائل غير القابلة للاشتعال لتبريد الخلايا الحرارية.',
         '1. Classification des marchandises dangereuses : L équipage est formé à reconnaître les matières dangereuses cachées.\n\n2. Incidents de batteries lithium-ion : En cas de surchauffe d un appareil électronique portable, appliquer les protocoles.\n\n3. Procédure d atténuation : Verser de grandes quantités d eau pour refroidir les cellules thermiques.'),

        (1, 4, 'Medical', 
         'Module 4: Aeromedical First Aid, Hypoxia & Decompression', 
         'الوحدة 4: الإسعافات الأولية الطبية ونقص الأكسجين وإزالة الضغط', 
         'Module 4: Premiers secours aéromédicaux, hypoxie et décompression',
         '1. Rapid Decompression: Characterized by a loud roaring sound, rush of air, fogging in the cabin, and automatic deployment of passenger oxygen masks. Cabin crew must immediately don portable oxygen bottles before moving to assist passengers.\n\n2. Hypoxia Recognition: Symptoms include tunnel vision, euphoria, cyanosis, impaired judgment, and dizziness. Immediate supplemental oxygen is critical.\n\n3. First Aid & CPR Protocols: Management of medical emergencies including cardiac arrest (AED operation), choking (Heimlich maneuver), asthma attacks, and cabin hyperventilation.',
         '1. إزالة الضغط السريع: تتميز بصوت عالٍ، وتدفق الهواء، والضباب في المقصورة، ونشر أقنعة الأكسجين تلقائياً.\n\n2. التعرف على نقص الأكسجين: تشمل الأعراض الرؤية النفقية، والنشوة، والزرقة، ضعف التمييز.\n\n3. الإسعافات الأولية وإنعاش القلب: إدارة الحالات الطبية الطارئة بما في ذلك السكتة القلبية.',
         '1. Décompression rapide : Caractérisée par un bruit sourd, un flux d air et le déploiement automatique des masques à oxygène.\n\n2. Reconnaissance de l hypoxie : Symptômes incluant vision tubulaire, euphorie, cyanose et vertiges.\n\n3. Premiers secours et réanimation : Gestion des urgences médicales incluant l arrêt cardiaque.'),

        (2, 1, 'CRM', 
         'Module 5 (Year 2): Advanced Crew Resource Management & Leadership', 
         'الوحدة 5 (السنة 2): إدارة موارد الطاقم المتقدمة والقيادة', 
         'Module 5 (Année 2) : Gestion des ressources d équipage et leadership',
         '1. Leadership & Command Dynamics: Second-year training transitions from operational compliance to advanced crew leadership, conflict resolution, and multicultural team coordination.\n\n2. Threat and Error Management (TEM): Proactive identification of operational threats, managing cockpit-cabin interface vulnerabilities, and debriefing critical safety events.\n\n3. Decision-Making Models: Utilizing structured frameworks (FORCES and DOT-DEDUCT) to make rapid, safety-critical decisions under extreme time constraints.',
         '1. القيادة وديناميكيات القيادة: ينتقل التدريب في السنة الثانية من الامتثال التشغيلي إلى قيادة الطاقم المتقدمة وحل النزاعات.\n\n2. إدارة التهديدات والأخطاء (TEM): التحديد الاستباقي للتهديدات التشغيلية وإدارة ثغرات واجهة قمرة القيادة.\n\n3. نماذج اتخاذ القرار: استخدام الأطر المنظمة لاتخاذ قرارات حرجة بسرعة.',
         '1. Leadership et dynamique d équipage : La formation de deuxième année passe de la conformité au leadership avancé.\n\n2. Gestion des menaces et des erreurs (TEM) : Identification proactive des menaces opérationnelles.\n\n3. Modèles de prise de décision : Utilisation de cadres structurés pour prendre des décisions critiques.'),

        (2, 2, 'AVSEC', 
         'Module 6 (Year 2): Aviation Security, Threat Levels & Unruly Passengers', 
         'الوحدة 6 (السنة 2): أمن الطيران ومستويات التهديد والركاب المشاغبين', 
         'Module 6 (Année 2) : Sûreté aérienne, niveaux de menaces et passagers indisciplinés',
         '1. Unruly Passenger Escalation Matrix: Four-tier threat level management ranging from verbal non-compliance (Tier 1) to physical breach of the flight deck (Tier 4).\n\n2. Cabin Search & Bomb Threat Checklists: Systematic search protocols for suspicious objects, coordination with air marshals, and security containment procedures.\n\n3. Flight Deck Defense Protocols: Establishing sterile barriers, securing cockpit access during emergency events, and coordinated defensive action plans.',
         '1. مصفوفة تصعيد الركاب المشاغبين: إدارة مستويات التهديد من الفئة الأولى إلى الرابعة.\n\n2. عمليات تفتيش المقصورة وقوائم مراجعة التهديد بالقنابل: بروتوكولات البحث المنهجي عن الأجسام المشبوهة.\n\n3. بروتوكولات دفاع قمرة القيادة: إنشاء حواجز معقمة وتأمين الوصول إلى قمرة القيادة.',
         '1. Matrice d escalation des passagers indisciplinés : Gestion des niveaux de menace de 1 à 4.\n\n2. Fouilles de cabine et listes de contrôle d alerte à la bombe : Protocoles de recherche systématique.\n\n3. Protocoles de défense du poste de pilotage : Établissement de barrières stériles.')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO official_drills_v7 (term_en, term_ar, term_fr, category, hint_en, hint_ar, hint_fr)
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
    cur.execute("SELECT * FROM comprehensive_academy_modules_v7 ORDER BY year_level ASC, node_order ASC;")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM official_drills_v7 ORDER BY id ASC;")
    drills = cur.fetchall()
    cur.close()
    conn.close()
    return {"modules": modules, "drills": drills}

@app.post("/api/drill/verify")
def verify_drill(data: DrillAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM official_drills_v7 WHERE id = %s;", (data.drill_id,))
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
    <title>AeroCrew Pro Academy Elite</title>
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
        
        .top-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.8rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
        .brand-title { display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 1.25rem; color: var(--accent); letter-spacing: -0.5px; }
        .brand-title img { width: 38px; height: 38px; filter: drop-shadow(0 0 10px var(--accent-glow)); }
        
        .lang-switch { display: flex; gap: 6px; }
        .lang-badge { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 10px; padding: 6px 12px; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-badge.active, .lang-badge:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); box-shadow: 0 0 15px var(--accent-glow); }

        h2 { font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0.4rem; font-size: 1.5rem; color: white; }
        p.sub-desc { font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1.6rem; line-height: 1.5; }
        
        label { display: block; font-size: 0.75rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.8px; }
        input { width: 100%; padding: 1rem 1.2rem; border-radius: 16px; border: 1px solid var(--border-glow); background: var(--bg-deep); color: white; font-size: 1rem; margin-bottom: 1.2rem; outline: none; transition: all 0.2s; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
        
        .btn-action { width: 100%; padding: 1.05rem; border-radius: 16px; border: none; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); font-weight: 800; font-size: 1rem; cursor: pointer; transition: transform 0.1s, opacity 0.2s, box-shadow 0.2s; box-shadow: 0 6px 20px var(--accent-glow); }
        .btn-action:active { transform: scale(0.98); }
        .btn-action:hover { opacity: 0.95; box-shadow: 0 8px 25px var(--accent-glow); }

        .footer-nav { display: flex; justify-content: space-between; margin-top: 1.4rem; font-size: 0.85rem; }
        .footer-nav a { color: var(--accent); text-decoration: none; font-weight: 700; cursor: pointer; }
        .footer-nav a:hover { text-decoration: underline; }

        .hidden { display: none !important; }

        .stats-dashboard { display: flex; justify-content: space-between; align-items: center; background: var(--surface-card); padding: 1rem 1.3rem; border-radius: 18px; border: 1px solid var(--border-glow); margin-bottom: 1.4rem; }
        .stat-item { font-weight: 800; font-size: 0.88rem; display: flex; align-items: center; gap: 6px; }
        
        .mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 1.4rem; }
        .mode-tile { background: var(--surface-card); border: 1px solid var(--border-glow); border-radius: 18px; padding: 1.2rem; text-align: center; cursor: pointer; transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .mode-tile:hover { border-color: var(--accent); background: var(--surface-card-hover); transform: translateY(-3px); box-shadow: 0 10px 25px rgba(56,189,248,0.15); }
        .mode-tile h4 { font-size: 0.92rem; font-weight: 800; margin-top: 8px; color: white; }

        .card-container { background: var(--surface-card); border-radius: 22px; padding: 1.6rem; border: 1px solid var(--border-glow); margin-bottom: 1.2rem; position: relative; min-height: 280px; }
        
        .path-container { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 12px 0; max-height: 280px; overflow-y: auto; }
        .path-node { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); color: var(--bg-deep); display: flex; justify-content: center; align-items: center; font-weight: 900; font-size: 1.2rem; cursor: pointer; box-shadow: 0 0 25px var(--accent-glow); transition: transform 0.2s, box-shadow 0.2s; position: relative; border: 3px solid #bae6fd; }
        .path-node:hover { transform: scale(1.12); box-shadow: 0 0 35px var(--accent); }
        .path-node:nth-child(even) { transform: translateX(35px); }
        .path-node:nth-child(odd) { transform: translateX(-35px); }

        .mic-circle { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); border: none; display: flex; justify-content: center; align-items: center; margin: 1.2rem auto 0.6rem; cursor: pointer; box-shadow: 0 0 30px var(--accent-glow); transition: transform 0.2s; }
        .mic-circle.recording { background: linear-gradient(135deg, #ef4444 0%, #991b1b 100%); animation: pulseAnim 1.5s infinite; }
        @keyframes pulseAnim { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); } 70% { box-shadow: 0 0 0 24px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

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
                <button class="lang-badge active" onclick="setLanguage('en')">EN</button>
                <button class="lang-badge" onclick="setLanguage('fr')">FR</button>
                <button class="lang-badge" onclick="setLanguage('ar')">AR</button>
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
            
            <button class="btn-action" onclick="submitRegister()" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); color: white;" id="reg-btn-sub">Initialize Profile</button>
            
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
            
            <button class="btn-action" onclick="submitReset()" style="background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%); color: var(--bg-deep);" id="res-btn-sub">Update Credentials</button>
            
            <div class="footer-nav">
                <a onclick="navigateTo('screen-login')" id="res-back">Back to Sign In</a>
            </div>
        </div>

        <!-- 4. GAMIFIED DASHBOARD -->
        <div id="screen-dashboard" class="hidden">
            <div class="stats-dashboard">
                <div>
                    <h3 id="dash-name" style="font-size: 1.05rem; color: var(--accent); font-weight: 900;">Cadet</h3>
                    <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 700;" id="dash-track">EASA Professional Track</span>
                </div>
                <div style="display: flex; gap: 10px;">
                    <div class="stat-item" style="color: var(--warning);">⭐ <span id="dash-xp">450</span></div>
                    <div class="stat-item" style="color: var(--danger);">❤️ <span id="dash-hearts">5</span></div>
                    <div class="stat-item" style="color: var(--success);">🔥 <span id="dash-streak">10</span></div>
                </div>
            </div>

            <!-- 2x2 Grid -->
            <div class="mode-grid">
                <div class="mode-tile" onclick="launchYearPath(1)">
                    <span style="font-size: 1.5rem;">📖</span>
                    <h4 id="tile-year1">First Year</h4>
                </div>
                <div class="mode-tile" onclick="launchYearPath(2)">
                    <span style="font-size: 1.5rem;">🏆</span>
                    <h4 id="tile-year2">Second Year</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('typing')">
                    <span style="font-size: 1.5rem;">⌨️</span>
                    <h4 id="tile-typing">Strict Typing</h4>
                </div>
                <div class="mode-tile" onclick="launchMode('voice')">
                    <span style="font-size: 1.5rem;">🎙️</span>
                    <h4 id="tile-voice">Voice Drill</h4>
                </div>
            </div>

            <div id="simulation-box" class="card-container"></div>
            
            <div style="display: flex; gap: 10px;">
                <button class="btn-action" onclick="resetToMenu()" style="background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border-glow); flex: 1;" id="btn-menu">← Hub</button>
                <button class="btn-action" onclick="logoutUser()" style="background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); flex: 1;" id="btn-logout">Logout 🚪</button>
            </div>
        </div>
    </div>

    <script>
        let sessionUser = JSON.parse(localStorage.getItem('aerocrew_user') || 'null');
        let academyData = { modules: [], drills: [] };
        let activeLang = localStorage.getItem('aerocrew_lang') || 'en';
        let drillPointer = 0;
        let timerInterval = null;
        let secondsLeft = 30;

        const translations = {
            en: {
                loginTitle: "Cabin Crew Portal", loginSub: "Access accredited EASA/ICAO professional curriculum.",
                phoneLbl: "Phone Number", passLbl: "Password", loginBtn: "Sign In to Simulator",
                regNav: "Create Account", resetNav: "Forgot Password?",
                regTitle: "Cadet Enrollment", regSub: "Register your official student training profile.",
                regName: "Full Name", regPass: "Password", regPin: "Recovery PIN (4-6 digits)", regBtn: "Initialize Profile", regBack: "Already have an account? Sign In",
                resTitle: "Recovery PIN Reset", resSub: "Enter your phone and secret recovery PIN.", resNew: "New Password", resBtn: "Update Credentials",
                tileYear1: "First Year", tileYear2: "Second Year", tileTyping: "Strict Typing", tileVoice: "Voice Drill",
                menuBtn: "← Hub", logoutBtn: "Logout 🚪"
            },
            fr: {
                loginTitle: "Portail Personnel de Cabine", loginSub: "Accédez au programme professionnel accrédité EASA/ICAO.",
                phoneLbl: "Numéro de téléphone", passLbl: "Mot de passe", loginBtn: "Se connecter au simulateur",
                regNav: "Créer un compte", resetNav: "Mot de passe oublié ?",
                regTitle: "Inscription Cadet", regSub: "Enregistrez votre profil de formation officiel.",
                regName: "Nom et Prénom", regPass: "Mot de passe", regPin: "PIN de récupération (4-6 chiffres)", regBtn: "Initialiser le profil", regBack: "Déjà un compte ? Se connecter",
                resTitle: "Réinitialisation PIN", resSub: "Entrez votre téléphone et votre PIN secret.", resNew: "Nouveau mot de passe", resBtn: "Mettre à jour",
                tileYear1: "Première Année", tileYear2: "Seconde Année", tileTyping: "Saisie Stricte", tileVoice: "Drill Vocal",
                menuBtn: "← Menu", logoutBtn: "Déconnexion 🚪"
            },
            ar: {
                loginTitle: "بوابة طاقم الطائرة", loginSub: "الوصول إلى المنهج المهني المعتمد من EASA/ICAO.",
                phoneLbl: "رقم الهاتف", passLbl: "كلمة المرور", loginBtn: "تسجيل الدخول للمحاكي",
                regNav: "إنشاء حساب", resetNav: "هل نسيت كلمة المرور؟",
                regTitle: "تسجيل المتدرب", regSub: "سجل ملف تدريب الطالب الرسمي الخاص بك.",
                regName: "الاسم الكامل", regPass: "كلمة المرور", regPin: "رمز الاسترداد (4-6 أرقام)", regBtn: "تهيئة الملف الشخصي", regBack: "لديك حساب بالفعل؟ تسجيل الدخول",
                resTitle: "إعادة تعيين الرمز", resSub: "أدخل هاتفك ورقم الرمز السري للاسترداد.", resNew: "كلمة المرور الجديدة", resBtn: "تحديث بيانات الاعتماد",
                tileYear1: "السنة الأولى", tileYear2: "السنة الثانية", tileTyping: "الكتابة الدقيقة", tileVoice: "تدريب الصوت",
                menuBtn: "← القائمة", logoutBtn: "تسجيل الخروج 🚪"
            }
        };

        window.onload = function() {
            setLanguage(activeLang);
            if(sessionUser) {
                document.getElementById('dash-name').innerText = sessionUser.full_name;
                document.getElementById('dash-xp').innerText = sessionUser.xp_points;
                document.getElementById('dash-hearts').innerText = sessionUser.hearts;
                document.getElementById('dash-streak').innerText = sessionUser.streak;
                navigateTo('screen-dashboard');
                fetchAcademyContent();
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
                document.getElementById('btn-logout').innerText = t.logoutBtn;
            }
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
                localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));
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
                <h3 style="font-size: 1.15rem; margin-bottom: 0.6rem; color: var(--accent); font-weight: 800;">EASA Professional Training Center</h3>
                <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6;">Select <b>First Year</b> or <b>Second Year</b> above to explore the official multi-paragraph curriculum library, or launch strict typing & voice drills.</p>
            `;
        }

        function launchYearPath(yearNum) {
            if(timerInterval) clearInterval(timerInterval);
            const box = document.getElementById('simulation-box');
            const yearMods = academyData.modules.filter(m => m.year_level === yearNum);

            box.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="font-size: 1.1rem; color: var(--accent); font-weight: 900;">Year ${yearNum} Curriculum Library</h3>
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
            let content = mod.content_en;
            if(activeLang === 'ar') { title = mod.title_ar; content = mod.content_ar; }
            if(activeLang === 'fr') { title = mod.title_fr; content = mod.content_fr; }

            const box = document.getElementById('simulation-box');
            box.innerHTML = `
                <span style="font-size: 0.72rem; font-weight: 800; background: rgba(56,189,248,0.15); color: var(--accent); padding: 4px 10px; border-radius: 6px;">EASA OFFICIAL MANUAL : ${mod.category}</span>
                <h3 style="font-size: 1.15rem; margin: 0.8rem 0; color: white; font-weight: 900; line-height: 1.4;">${title}</h3>
                <div style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 1.5rem; background: var(--bg-deep); padding: 1.2rem; border-radius: 16px; border: 1px solid var(--border-glow); max-height: 220px; overflow-y: auto; white-space: pre-line;">${content}</div>
                <button class="btn-action" onclick="launchYearPath(${mod.year_level})">← Back to Roadmap</button>
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
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.72rem; font-weight: 800; color: var(--warning);">VOICE PRONUNCIATION DRILL</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);" id="timer-text">30s remaining</span>
                    </div>
                    <div class="timer-bar"><div id="timer-fill" class="timer-progress"></div></div>
                    <div style="font-size: 1.3rem; font-weight: 900; color: white; margin-bottom: 4px;">Say: "${term.term_en}"</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.6rem;">Hint: ${hint}</div>
                    <button class="mic-circle" id="mic-trigger" onclick="startSpeechRecognition(${term.id})">
                        <span style="font-size: 1.9rem;">🎙️</span>
                    </button>
                    <div id="inline-msg" class="inline-feedback" style="color: var(--text-muted);">Click mic and speak clearly</div>
                    <div id="reveal-container" style="text-align: center; margin-top: 8px;"></div>
                `;
                start30SecTimer(() => {
                    document.getElementById('reveal-container').innerHTML = `<button onclick="revealAnswer('${term.term_en}')" style="background:none; border:1px solid var(--warning); color:var(--warning); padding:5px 14px; border-radius:8px; font-weight:800; font-size:0.8rem; cursor:pointer;">Reveal Answer 💡</button>`;
                });
            } else if(mode === 'typing') {
                let promptTerm = term.term_ar;
                if(activeLang === 'fr') promptTerm = term.term_fr;
                if(activeLang === 'en') promptTerm = term.hint_en;

                box.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.72rem; font-weight: 800; color: var(--success);">STRICT SPELLING & TYPING TEST</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);" id="timer-text">30s remaining</span>
                    </div>
                    <div class="timer-bar"><div id="timer-fill" class="timer-progress"></div></div>
                    <div style="font-size: 1.2rem; font-weight: 900; color: white; margin-bottom: 4px;">Translate: ${promptTerm}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">Type exact English EASA terminology:</div>
                    <input type="text" id="typing-input" placeholder="Type term exactly..." autocomplete="off" />
                    <button class="btn-action" onclick="verifyTypingInput(${term.id})" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); color: white; margin-bottom: 0.8rem;">Validate Spelling ✓</button>
                    <div id="inline-msg" class="inline-feedback" style="color: var(--text-muted);"></div>
                    <div id="reveal-container" style="text-align: center; margin-top: 6px;"></div>
                `;
                start30SecTimer(() => {
                    document.getElementById('reveal-container').innerHTML = `<button onclick="revealAnswer('${term.term_en}')" style="background:none; border:1px solid var(--warning); color:var(--warning); padding:5px 14px; border-radius:8px; font-weight:800; font-size:0.8rem; cursor:pointer;">Reveal Answer 💡</button>`;
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
                sessionUser.xp_points = data.xp;
                sessionUser.hearts = data.hearts;
                sessionUser.streak = data.streak;
                localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));

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
            sessionUser.xp_points = data.xp;
            sessionUser.hearts = data.hearts;
            sessionUser.streak = data.streak;
            localStorage.setItem('aerocrew_user', JSON.stringify(sessionUser));

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
