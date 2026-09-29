import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Uses your Neon database connection (or defaults to environment variable)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aviation Cabin Crew Study & Training Hub", version="1.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Create tables for students, aviation vocabulary, and strict spelling progress
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crew_students (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            password VARCHAR(100),
            full_name VARCHAR(100),
            year_level INT DEFAULT 1,
            xp_points INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aviation_vocabulary (
            id SERIAL PRIMARY KEY,
            term_en VARCHAR(100),
            term_ar VARCHAR(100),
            category VARCHAR(50),
            definition_en TEXT
        );
    """)
    # Insert initial sample cabin crew terminology for spelling & translation drills
    cur.execute("""
        INSERT INTO aviation_vocabulary (term_en, term_ar, category, definition_en) 
        VALUES 
        ('Altimeter', 'مقياس الارتفاع', 'Instruments', 'An instrument that measures the altitude of the aircraft above a fixed level.'),
        ('Bulkhead', 'الجدار الفاصل', 'Cabin', 'An upright partition separating compartments inside the aircraft.'),
        ('Decompression', 'إزالة الضغط', 'Emergency', 'A failure of the cabin pressurization system at high altitude.'),
        ('Turbulence', 'مطبات هوائية', 'Meteorology', 'Violent or unsteady movement of air or water.')
        ON CONFLICT DO NOTHING;
    """)
    conn.commit()
    cur.close()
    conn.close()

class StudentRegister(BaseModel):
    phone_number: str
    password: str
    full_name: str
    year_level: int = 1

class StudentLogin(BaseModel):
    phone_number: str
    password: str

class SpellingTestAttempt(BaseModel):
    phone_number: str
    vocabulary_id: int
    user_spelling: str

@app.get("/api/health")
def health_check():
    return {"status": "online", "platform": "Aviation Cabin Crew Academy"}

@app.post("/api/student/register")
def register_student(data: StudentRegister):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM crew_students WHERE phone_number = %s;", (data.phone_number,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Student account already exists.")
        
        cur.execute(
            "INSERT INTO crew_students (phone_number, password, full_name, year_level) VALUES (%s, %s, %s, %s) RETURNING *;",
            (data.phone_number, data.password, data.full_name, data.year_level)
        )
        student = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "message": "Registered successfully!", "student": student}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/student/login")
def login_student(data: StudentLogin):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM crew_students WHERE phone_number = %s;", (data.phone_number,))
        student = cur.fetchone()
        cur.close()
        conn.close()

        if not student or student["password"] != data.password:
            raise HTTPException(status_code=401, detail="Invalid phone number or password.")
        
        return {"status": "success", "full_name": student["full_name"], "xp_points": student["xp_points"], "year_level": student["year_level"]}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vocabulary")
def get_vocabulary():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM aviation_vocabulary ORDER BY id ASC;")
        vocab = cur.fetchall()
        cur.close()
        conn.close()
        return vocab or []
    except Exception:
        return []

@app.post("/api/spelling/check")
def check_spelling(data: SpellingTestAttempt):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM aviation_vocabulary WHERE id = %s;", (data.vocabulary_id,))
        vocab = cur.fetchone()
        
        if not vocab:
            raise HTTPException(status_code=404, detail="Vocabulary term not found.")
        
        correct_term = vocab["term_en"].strip().lower()
        user_input = data.user_spelling.strip().lower()
        
        if user_input == correct_term:
            # Award XP points for correct spelling
            cur.execute("UPDATE crew_students SET xp_points = xp_points + 10 WHERE phone_number = %s RETURNING xp_points;", (data.phone_number,))
            res = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            return {"correct": True, "message": "Perfect spelling! +10 XP earned.", "new_xp": res["xp_points"] if res else 0}
        else:
            cur.close()
            conn.close()
            return {"correct": False, "message": f"Incorrect spelling. Try again! The correct spelling is '{vocab['term_en']}'."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviation Cabin Crew Academy Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #090d16;
            --surface: #131c31;
            --surface-card: #1a2642;
            --accent: #38bdf8;
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #2a3a5e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        .app-container { width: 100%; max-width: 480px; background: var(--surface); border-radius: 20px; padding: 1.5rem; border: 1px solid var(--border); box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
        .logo { text-align: center; font-size: 1.4rem; font-weight: 800; margin-bottom: 1rem; color: var(--accent); letter-spacing: -0.5px; }
        .card { background: var(--surface-card); border-radius: 14px; padding: 1.2rem; margin-bottom: 1rem; border: 1px solid var(--border); }
        label { display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-muted); margin-bottom: 0.3rem; text-transform: uppercase; }
        input { width: 100%; padding: 0.75rem; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-deep); color: white; font-size: 0.9rem; margin-bottom: 0.8rem; outline: none; }
        input:focus { border-color: var(--accent); }
        .btn { width: 100%; padding: 0.75rem; border-radius: 10px; border: none; background: var(--accent); color: #090d16; font-weight: 800; font-size: 0.9rem; cursor: pointer; }
        .vocab-item { background: var(--bg-deep); padding: 0.8rem; border-radius: 10px; margin-bottom: 0.6rem; border: 1px solid var(--border); }
        .hidden { display: none !important; }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; transition: transform 0.3s; }
        .toast.show { transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="toast" class="toast">Success!</div>

    <div class="app-container">
        <div class="logo">✈️ Cabin Crew Academy Hub</div>

        <!-- AUTH SECTION -->
        <div id="auth-section" class="card">
            <h3 style="margin-bottom: 0.8rem; font-size: 0.95rem;">Student Sign In</h3>
            <label>Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g., 0612345678" />
            <label>Password</label>
            <input type="password" id="login-pass" placeholder="Password" />
            <button class="btn" onclick="loginStudent()">Sign In</button>
        </div>

        <!-- DASHBOARD SECTION -->
        <div id="dashboard-section" class="card hidden">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h3 id="student-name-display" style="font-size: 1rem; color: var(--accent);">Student</h3>
                    <span style="font-size: 0.7rem; color: var(--text-muted);" id="student-level-display">Year 1</span>
                </div>
                <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid var(--accent); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; color: var(--accent);">
                    ⭐ <span id="student-xp">0</span> XP
                </div>
            </div>

            <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">Strict Aviation Spelling Drill</h4>
            <div id="drill-box" class="vocab-item" style="margin-bottom: 0.8rem;">
                <div id="drill-arabic" style="font-size: 1rem; font-weight: 700; margin-bottom: 3px; color: var(--accent);"></div>
                <div id="drill-def" style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 8px;"></div>
                <label>Type Correct English Spelling:</label>
                <input type="text" id="spelling-input" placeholder="Spell exactly..." />
                <button class="btn" onclick="submitSpelling()" style="background: var(--success); color: white; padding: 0.6rem;">Submit Spelling Test ✓</button>
            </div>

            <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">Aviation Glossary (AR / EN)</h4>
            <div id="vocab-list" style="max-height: 150px; overflow-y: auto;"></div>
        </div>
    </div>

    <script>
        let currentPhone = '';
        let currentVocabId = null;

        function showToast(text, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = text;
            t.style.background = isError ? 'var(--danger)' : 'var(--success)';
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }

        async function loginStudent() {
            const phone = document.getElementById('login-phone').value.trim();
            const password = document.getElementById('login-pass').value.trim();
            if(!phone || !password) { showToast('Enter phone and password', true); return; }
            currentPhone = phone;

            try {
                const res = await fetch('/api/student/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: phone, password: password })
                });
                const data = await res.json();
                if(res.ok) {
                    document.getElementById('student-name-display').innerText = data.full_name;
                    document.getElementById('student-level-display').innerText = 'Year ' + data.year_level + ' Cabin Crew';
                    document.getElementById('student-xp').innerText = data.xp_points;
                    document.getElementById('auth-section').classList.add('hidden');
                    document.getElementById('dashboard-section').classList.remove('hidden');
                    loadVocabulary();
                    showToast('Welcome back, future crew!');
                } else {
                    // Auto-register if not found for easy testing with classmates
                    registerAndLogin(phone, password);
                }
            } catch(e) {
                showToast('Connection error', true);
            }
        }

        async function registerAndLogin(phone, password) {
            const res = await fetch('/api/student/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: phone, password: password, full_name: 'Student ' + phone.slice(-4), year_level: 1 })
            });
            if(res.ok) { loginStudent(); }
        }

        async function loadVocabulary() {
            const res = await fetch('/api/vocabulary');
            const vocab = await res.json();
            const list = document.getElementById('vocab-list');
            if(vocab.length > 0) {
                // Set first item as active drill
                currentVocabId = vocab[0].id;
                document.getElementById('drill-arabic').innerText = vocab[0].term_ar + ' (' + vocab[0].category + ')';
                document.getElementById('drill-def').innerText = vocab[0].definition_en;

                list.innerHTML = vocab.map(v => `
                    <div style="font-size: 0.78rem; margin-bottom: 4px; display: flex; justify-content: space-between;">
                        <span><b>${v.term_en}</b></span>
                        <span style="color: var(--accent);">${v.term_ar}</span>
                    </div>
                `).join('');
            }
        }

        async function submitSpelling() {
            const val = document.getElementById('spelling-input').value.trim();
            if(!val) { showToast('Type a spelling', true); return; }

            const res = await fetch('/api/spelling/check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ phone_number: currentPhone, vocabulary_id: currentVocabId, user_spelling: val })
            });
            const data = await res.json();
            if(data.correct) {
                showToast(data.message);
                document.getElementById('student-xp').innerText = data.new_xp;
                document.getElementById('spelling-input').value = '';
            } else {
                showToast(data.message, true);
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
