import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_7aYbfrQdjcq6@ep-cold-lake-b1djlrzp-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

app = FastAPI(title="Aviation Cabin Crew Academy Hub", version="2.0.0")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crew_students_v2 (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) UNIQUE,
            full_name VARCHAR(100),
            password VARCHAR(100),
            recovery_pin VARCHAR(10),
            year_level INT DEFAULT 1,
            xp_points INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aviation_vocabulary_v2 (
            id SERIAL PRIMARY KEY,
            term_en VARCHAR(100),
            term_ar VARCHAR(100),
            term_fr VARCHAR(100),
            category VARCHAR(50),
            definition_en TEXT
        );
    """)
    # Seed robust aviation database
    cur.execute("""
        INSERT INTO aviation_vocabulary_v2 (term_en, term_ar, term_fr, category, definition_en) 
        VALUES 
        ('Altimeter', 'مقياس الارتفاع', 'Altimètre', 'Instruments', 'An instrument that measures the altitude of the aircraft above a fixed level.'),
        ('Bulkhead', 'الجدار الفاصل', 'Cloison', 'Cabin', 'An upright partition separating compartments inside the aircraft.'),
        ('Decompression', 'إزالة الضغط', 'Décompression', 'Emergency', 'A failure of the cabin pressurization system at high altitude.'),
        ('Turbulence', 'مطبات هوائية', 'Turbulence', 'Meteorology', 'Violent or unsteady movement of air or water.'),
        ('Evacuation', 'إخلاء الطائرة', 'Évacuation', 'Emergency', 'Rapid exit of passengers from an aircraft during an emergency.'),
        ('Galley', 'مطبخ الطائرة', 'Cuisine', 'Cabin', 'The kitchen area of an aircraft where meals and beverages are prepared.')
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
    year_level: int = 1

class LoginModel(BaseModel):
    phone_number: str
    password: str

class ResetPinModel(BaseModel):
    phone_number: str
    recovery_pin: str
    new_password: str

class SpellingAttemptModel(BaseModel):
    phone_number: str
    vocabulary_id: int
    user_spelling: str

@app.post("/api/register")
def register(data: RegisterModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crew_students_v2 WHERE phone_number = %s;", (data.phone_number,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered.")
    
    cur.execute(
        "INSERT INTO crew_students_v2 (phone_number, full_name, password, recovery_pin, year_level) VALUES (%s, %s, %s, %s, %s) RETURNING *;",
        (data.phone_number, data.full_name, data.password, data.recovery_pin, data.year_level)
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
    cur.execute("SELECT * FROM crew_students_v2 WHERE phone_number = %s AND password = %s;", (data.phone_number, data.password))
    student = cur.fetchone()
    cur.close()
    conn.close()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid phone number or password.")
    return {"status": "success", "student": student}

@app.post("/api/reset-password")
def reset_password(data: ResetPinModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM crew_students_v2 WHERE phone_number = %s AND recovery_pin = %s;", (data.phone_number, data.recovery_pin))
    student = cur.fetchone()
    if not student:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid phone number or recovery PIN.")
    
    cur.execute("UPDATE crew_students_v2 SET password = %s WHERE phone_number = %s;", (data.new_password, data.phone_number))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "message": "Password updated successfully!"}

@app.get("/api/vocabulary")
def get_vocabulary():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aviation_vocabulary_v2 ORDER BY id ASC;")
    vocab = cur.fetchall()
    cur.close()
    conn.close()
    return vocab

@app.post("/api/spelling/check")
def check_spelling(data: SpellingAttemptModel):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM aviation_vocabulary_v2 WHERE id = %s;", (data.vocabulary_id,))
    vocab = cur.fetchone()
    if not vocab:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Term not found.")
    
    correct_term = vocab["term_en"].strip().lower()
    user_input = data.user_spelling.strip().lower()
    
    if user_input == correct_term:
        # Check if student already answered this recently to prevent farming glitched XP
        cur.execute("UPDATE crew_students_v2 SET xp_points = xp_points + 15 WHERE phone_number = %s RETURNING xp_points;", (data.phone_number,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"correct": True, "message": "Fantastic! +15 XP earned.", "new_xp": res["xp_points"]}
    else:
        cur.close()
        conn.close()
        return {"correct": False, "message": f"Incorrect spelling! Correct spelling is '{vocab['term_en']}'."}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviation Cabin Crew Academy Hub</title>
    <!-- Professional Plane Favicon -->
    <link rel="icon" href="https://img.icons8.com/color/48/airplane-take-off.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #070b14;
            --surface: #0f172a;
            --surface-card: #1e293b;
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: var(--bg-deep); color: var(--text-main); display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 1rem; }
        .app-shell { width: 100%; max-width: 520px; background: var(--surface); border-radius: 24px; padding: 2rem; border: 1px solid var(--border); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }
        
        .header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
        .brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.1rem; color: var(--accent); }
        .brand img { width: 32px; height: 32px; }
        
        /* Language Selector Flags/Icons */
        .lang-selector { display: flex; gap: 8px; }
        .lang-btn { background: var(--surface-card); border: 1px solid var(--border); border-radius: 8px; padding: 4px 8px; font-size: 0.75rem; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
        .lang-btn.active, .lang-btn:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }

        h2 { font-size: 1.3rem; font-weight: 800; margin-bottom: 0.3rem; letter-spacing: -0.5px; }
        p.subtitle { font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1.5rem; }
        
        label { display: block; font-size: 0.72rem; font-weight: 700; color: var(--text-muted); margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.5px; }
        input { width: 100%; padding: 0.85rem 1rem; border-radius: 12px; border: 1px solid var(--border); background: var(--bg-deep); color: white; font-size: 0.95rem; margin-bottom: 1rem; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
        
        .btn { width: 100%; padding: 0.85rem; border-radius: 12px; border: none; background: var(--accent); color: #070b14; font-weight: 800; font-size: 0.95rem; cursor: pointer; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.9; }
        
        .nav-links { display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; font-size: 0.8rem; }
        .nav-links a { color: var(--accent); text-decoration: none; cursor: pointer; font-weight: 600; }
        .nav-links a:hover { text-decoration: underline; }

        .hidden { display: none !important; }
        
        /* Dashboard & Quiz Styles */
        .dash-card { background: var(--surface-card); border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem; border: 1px solid var(--border); }
        .xp-badge { background: rgba(56, 189, 248, 0.1); border: 1px solid var(--accent); padding: 6px 14px; border-radius: 30px; font-size: 0.8rem; font-weight: 800; color: var(--accent); display: flex; align-items: center; gap: 6px; }
        
        .toast { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(100px); background: var(--success); color: white; padding: 10px 20px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 1000; }
        .toast.show { transform: translateX(-50%) translateY(0); }

        .vocab-row { display: flex; justify-content: space-between; align-items: center; background: var(--bg-deep); padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 0.5rem; border: 1px solid var(--border); font-size: 0.85rem; }
    </style>
</head>
<body>
    <div id="toast" class="toast">Notification</div>

    <div class="app-shell">
        <!-- HEADER WITH LOGO & LANGUAGES -->
        <div class="header-top">
            <div class="brand">
                <img src="https://img.icons8.com/color/48/airplane-take-off.png" alt="Plane">
                <span>AeroCrew Academy</span>
            </div>
            <div class="lang-selector">
                <button class="lang-btn active" onclick="setLang('en')">🇬🇧 EN</button>
                <button class="lang-btn" onclick="setLang('fr')">🇫🇷 FR</button>
                <button class="lang-btn" onclick="setLang('ar')">🇲🇦 AR</button>
            </div>
        </div>

        <!-- 1. SIGN IN VIEW -->
        <div id="view-login">
            <h2>Welcome Back, Crew</h2>
            <p class="subtitle">Access your professional academy training hub.</p>
            
            <label>Phone Number</label>
            <input type="tel" id="login-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="login-pass" placeholder="••••••••" />
            
            <button class="btn" onclick="handleLogin()">Sign In</button>
            
            <div class="nav-links">
                <a onclick="switchView('view-register')">Create Account (Sign Up)</a>
                <a onclick="switchView('view-forgot')">Forgot Password?</a>
            </div>
        </div>

        <!-- 2. SIGN UP VIEW -->
        <div id="view-register" class="hidden">
            <h2>Create Account</h2>
            <p class="subtitle">Join the professional cabin crew study platform.</p>
            
            <label>Full Name</label>
            <input type="text" id="reg-name" placeholder="Captain John" />

            <label>Phone Number</label>
            <input type="tel" id="reg-phone" placeholder="e.g. 0612345678" />
            
            <label>Password</label>
            <input type="password" id="reg-pass" placeholder="Create password" />

            <label>Recovery PIN (4-6 digits for password reset)</label>
            <input type="password" id="reg-pin" placeholder="e.g. 1994" maxlength="6" />
            
            <button class="btn" onclick="handleRegister()" style="background: var(--success); color: white;">Complete Registration</button>
            
            <div class="nav-links">
                <a onclick="switchView('view-login')">Already have an account? Sign In</a>
            </div>
        </div>

        <!-- 3. FORGOT PASSWORD VIEW (PIN RECOVERY) -->
        <div id="view-forgot" class="hidden">
            <h2>Reset Password</h2>
            <p class="subtitle">Enter your phone and secret recovery PIN.</p>
            
            <label>Phone Number</label>
            <input type="tel" id="forgot-phone" placeholder="e.g. 0612345678" />

            <label>Secret Recovery PIN</label>
            <input type="password" id="forgot-pin" placeholder="Your secret PIN" />

            <label>New Password</label>
            <input type="password" id="forgot-newpass" placeholder="Enter new password" />
            
            <button class="btn" onclick="handleResetPassword()" style="background: #f59e0b; color: white;">Reset Password</button>
            
            <div class="nav-links">
                <a onclick="switchView('view-login')">Back to Sign In</a>
            </div>
        </div>

        <!-- 4. MAIN DASHBOARD & DUOLINGO-GRADE DRILLS -->
        <div id="view-dashboard" class="hidden">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;">
                <div>
                    <h3 id="dash-name" style="font-size: 1.1rem; color: var(--accent);">Student</h3>
                    <span style="font-size: 0.75rem; color: var(--text-muted);" id="dash-level">Year 1 Professional Track</span>
                </div>
                <div class="xp-badge">
                    ⭐ <span id="dash-xp">0</span> XP
                </div>
            </div>

            <!-- Quiz Drill Box -->
            <div class="dash-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span id="quiz-category" style="font-size: 0.68rem; font-weight: 800; text-transform: uppercase; color: var(--accent); background: rgba(56,189,248,0.1); padding: 2px 8px; border-radius: 4px;">Category</span>
                    <span id="quiz-progress" style="font-size: 0.72rem; color: var(--text-muted);">Question 1 of 6</span>
                </div>
                <div id="quiz-prompt-ar" style="font-size: 1.2rem; font-weight: 800; margin-bottom: 4px; color: white;">العربية</div>
                <div id="quiz-def" style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 1rem;">Definition goes here...</div>
                
                <label>Translate & Type Correct English Term:</label>
                <input type="text" id="quiz-input" placeholder="Type exact English spelling..." autocomplete="off" />
                <button class="btn" onclick="submitSpellingAnswer()" style="background: var(--success); color: white;">Submit Answer ✓</button>
            </div>

            <!-- Vocabulary Master List -->
            <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.6rem; letter-spacing: 0.5px;">Academy Terminology Vault</h4>
            <div id="vocab-vault" style="max-height: 160px; overflow-y: auto; padding-right: 4px;"></div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let vocabList = [];
        let currentQuizIndex = 0;
        let activeLang = 'en';

        function showToast(text, isError = false) {
            const t = document.getElementById('toast');
            t.innerText = text;
            t.style.background = isError ? 'var(--danger)' : 'var(--success)';
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }

        function switchView(viewId) {
            ['view-login', 'view-register', 'view-forgot', 'view-dashboard'].forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
            document.getElementById(viewId).classList.remove('hidden');
        }

        function setLang(lang) {
            activeLang = lang;
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            showToast('Language switched to ' + lang.toUpperCase());
        }

        async function handleRegister() {
            const full_name = document.getElementById('reg-name').value.trim();
            const phone_number = document.getElementById('reg-phone').value.trim();
            const password = document.getElementById('reg-pass').value.trim();
            const recovery_pin = document.getElementById('reg-pin').value.trim();

            if(!full_name || !phone_number || !password || !recovery_pin) {
                showToast('Please fill in all fields including recovery PIN.', true);
                return;
            }

            try {
                const res = await fetch('/api/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ full_name, phone_number, password, recovery_pin, year_level: 1 })
                });
                const data = await res.json();
                if(res.ok) {
                    showToast('Registration successful! Please sign in.');
                    switchView('view-login');
                } else {
                    showToast(data.detail || 'Registration failed', true);
                }
            } catch(e) {
                showToast('Network error', true);
            }
        }

        async function handleLogin() {
            const phone_number = document.getElementById('login-phone').value.trim();
            const password = document.getElementById('login-pass').value.trim();

            if(!phone_number || !password) {
                showToast('Enter phone number and password.', true);
                return;
            }

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number, password })
                });
                const data = await res.json();
                if(res.ok) {
                    currentUser = data.student;
                    document.getElementById('dash-name').innerText = currentUser.full_name;
                    document.getElementById('dash-xp').innerText = currentUser.xp_points;
                    switchView('view-dashboard');
                    loadVocabularyAndQuiz();
                    showToast('Welcome back, ' + currentUser.full_name + '!');
                } else {
                    showToast(data.detail || 'Invalid credentials', true);
                }
            } catch(e) {
                showToast('Network error', true);
            }
        }

        async function handleResetPassword() {
            const phone_number = document.getElementById('forgot-phone').value.trim();
            const recovery_pin = document.getElementById('forgot-pin').value.trim();
            const new_password = document.getElementById('forgot-newpass').value.trim();

            if(!phone_number || !recovery_pin || !new_password) {
                showToast('All fields required for reset.', true);
                return;
            }

            try {
                const res = await fetch('/api/reset-password', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number, recovery_pin, new_password })
                });
                const data = await res.json();
                if(res.ok) {
                    showToast('Password reset successful! Sign in now.');
                    switchView('view-login');
                } else {
                    showToast(data.detail || 'Reset failed', true);
                }
            } catch(e) {
                showToast('Network error', true);
            }
        }

        async function loadVocabularyAndQuiz() {
            const res = await fetch('/api/vocabulary');
            vocabList = await res.json();
            renderQuizCard();
            renderVault();
        }

        function renderQuizCard() {
            if(vocabList.length === 0) return;
            const item = vocabList[currentQuizIndex % vocabList.length];
            
            document.getElementById('quiz-category').innerText = item.category;
            document.getElementById('quiz-progress').innerText = `Question ${ (currentQuizIndex % vocabList.length) + 1 } of ${vocabList.length}`;
            
            let promptText = item.term_ar;
            if(activeLang === 'fr') promptText = item.term_fr;
            if(activeLang === 'en') promptText = item.definition_en;
            
            document.getElementById('quiz-prompt-ar').innerText = promptText;
            document.getElementById('quiz-def').innerText = `Category: ${item.category} | Hint length: ${item.term_en.length} letters`;
            document.getElementById('quiz-input').value = '';
            document.getElementById('quiz-input').dataset.targetId = item.id;
        }

        async function submitSpellingAnswer() {
            const inputField = document.getElementById('quiz-input');
            const userSpelling = inputField.value.trim();
            const vocabId = inputField.dataset.targetId;

            if(!userSpelling) {
                showToast('Please type your answer!', true);
                return;
            }

            try {
                const res = await fetch('/api/spelling/check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phone_number: currentUser.phone_number, vocabulary_id: parseInt(vocabId), user_spelling: userSpelling })
                });
                const data = await res.json();
                if(data.correct) {
                    showToast(data.message);
                    currentUser.xp_points = data.new_xp;
                    document.getElementById('dash-xp').innerText = currentUser.xp_points;
                    // Advance to next question automatically (Duolingo style rotation)
                    currentQuizIndex++;
                    renderQuizCard();
                } else {
                    showToast(data.message, true);
                }
            } catch(e) {
                showToast('Error validating answer', true);
            }
        }

        function renderVault() {
            const vault = document.getElementById('vocab-vault');
            vault.innerHTML = vocabList.map(v => `
                <div class="vocab-row">
                    <div><b>${v.term_en}</b> <span style="color: var(--text-muted); font-size: 0.75rem;">(${v.category})</span></div>
                    <div style="color: var(--accent); font-weight: 600;">${v.term_ar} / ${v.term_fr}</div>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
