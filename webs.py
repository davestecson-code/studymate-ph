from flask import Flask, render_template_string, send_from_directory, request, redirect, session, url_for
import os, json, uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "studymate_ph_secure_key_2026"

DB_FILE = "users.json"
SCHEDULE_FILE = "schedules.json"
NOTIFICATION_FILE = "notifications.json"
DEADLINE_FILE = "deadlines.json"
GROUP_FILE = "group_projects.json"
NOTES_FILE = "notes.json"

# === Load & Save ===
def load_users():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_schedules():
    if not os.path.exists(SCHEDULE_FILE): return {}
    with open(SCHEDULE_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_schedules(schedules):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedules, f, indent=2)

def load_notifications():
    if not os.path.exists(NOTIFICATION_FILE):
        return {}
    with open(NOTIFICATION_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_notifications(notifications):
    with open(NOTIFICATION_FILE, "w") as f:
        json.dump(notifications, f, indent=2)


def load_deadlines():
    if not os.path.exists(DEADLINE_FILE):
        return {}
    with open(DEADLINE_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_deadlines(deadlines):
    with open(DEADLINE_FILE, "w") as f:
        json.dump(deadlines, f, indent=2)


def get_deadline_status(deadline):
    if deadline.get("completed", False):
        return "completed"
    try:
        due = datetime.strptime(
            deadline["due_date"] + " " + deadline["due_time"],
            "%Y-%m-%d %H:%M"
        )
        now = datetime.now()
        if due < now:
            return "overdue"
        days_left = (due.date() - now.date()).days
        if days_left <= 2:
            return "soon"
        return "upcoming"
    except:
        return "upcoming"


def deadline_status_text(status):
    return {
        "overdue": "Overdue",
        "soon": "Due Soon",
        "completed": "Completed",
        "upcoming": "Upcoming"
    }.get(status, "Upcoming")


def deadline_icon(status):
    return {
        "overdue": "🔴",
        "soon": "🟠",
        "completed": "🟢",
        "upcoming": "🔵"
    }.get(status, "🔵")


def deadline_days_left(deadline):
    if deadline.get("completed", False):
        return "Completed"
    try:
        due = datetime.strptime(
            deadline["due_date"] + " " + deadline["due_time"],
            "%Y-%m-%d %H:%M"
        )
        seconds = (due - datetime.now()).total_seconds()
        if seconds < 0:
            return "Overdue"
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        if days > 0:
            return f"{days} day{'s' if days != 1 else ''} left"
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} left"
        return "Due soon"
    except:
        return ""




def load_notes():
    if not os.path.exists(NOTES_FILE):
        return {}
    with open(NOTES_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


def load_groups():
    if not os.path.exists(GROUP_FILE):
        return {}
    with open(GROUP_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_groups(groups):
    with open(GROUP_FILE, "w") as f:
        json.dump(groups, f, indent=2)


def get_user_name(user_id):
    users = load_users()
    return users.get(str(user_id), {}).get("name", "Student")


def notify_group_members(group, title, message, exclude_user_id=None):
    for member_id in group.get("members", []):
        if str(member_id) != str(exclude_user_id):
            add_notification(str(member_id), title, message)


def find_group(groups, group_id):
    return groups.get(str(group_id))


def group_progress(group):
    tasks = group.get("tasks", [])
    if not tasks:
        return 0
    completed = sum(1 for task in tasks if task.get("completed", False))
    return int((completed / len(tasks)) * 100)


def add_notification(user_id, title, message):
    notifications = load_notifications()
    notifications.setdefault(user_id, [])
    notifications[user_id].append({
        "id": str(uuid.uuid4()),
        "title": title,
        "message": message,
        "date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "read": False
    })
    save_notifications(notifications)

def get_day_name(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    except:
        return ""

# === HOME ===
@app.route('/')
def home():
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StudyMate PH</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #fcf9f0; }
        .logo-row { display: flex; align-items: center; gap: 12px; margin-bottom: 30px; }
        .logo-icon-wrap { position: relative; width: 52px; height: 52px; }
        .logo-square { background-color: #0a3472; width: 52px; height: 52px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 32px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -6px; right: -6px; font-size: 34px; color: #f9c80e; }
        .brand-text { font-size: 44px; font-weight: 700; color: #0a3472; }
        .brand-text .ph { color: #f9c80e; }
        .main-title { font-size: 52px; font-weight: 800; color: #0a3472; margin-bottom: 50px; }
        .get-started-btn { background-color: #f9c80e; color: #222; border: none; padding: 16px 65px; font-size: 20px; font-weight: 700; border-radius: 50px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="logo-row">
        <div class="logo-icon-wrap"><div class="logo-square"><span class="logo-letter-s">S</span><span class="logo-pencil">✏️</span></div></div>
        <span class="brand-text">studymate <span class="ph">ph</span></span>
    </div>
    <h1 class="main-title">StudyMate PH</h1>
    <button class="get-started-btn" onclick="window.location.href='/login'">Get Started</button>
<script src="/static/alarm.js"></script>
</body>
</html>''')

# === LOGIN ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if "user" in session: return redirect("/dashboard")
    if request.method == 'POST':
        email_or_id = request.form.get("email_or_id", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        for uid, user in users.items():
            if (user.get("email") == email_or_id or user.get("student_id") == email_or_id) and user.get("password") == password:
                session["user_id"] = uid
                session["user"] = user
                return redirect("/dashboard")
        return render_template_string(LOGIN_HTML, error=True)
    return render_template_string(LOGIN_HTML, error=False)

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log In</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body {
        min-height:100vh;
        display:flex;
        align-items:center;
        justify-content:center;
        background:
            linear-gradient(rgba(10,52,114,.55), rgba(10,52,114,.55)),
            url('/static/bg.jpg') center/cover no-repeat fixed;
        padding:25px;
    }
        .right-side {
        width:100%;
        max-width:520px;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        background:rgba(255,255,255,.96);
        padding:40px;
        border-radius:24px;
        box-shadow:0 12px 35px rgba(0,0,0,.20);
    }
        .logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; }
        .logo-icon-wrap { position: relative; width: 48px; height: 48px; }
        .logo-square { background-color: #0a3472; width: 48px; height: 48px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 28px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -5px; right: -5px; font-size: 30px; color: #f9c80e; }
        .brand-text { font-size: 36px; font-weight: 700; color: #0a3472; }
        .brand-text .ph { color: #f9c80e; }
        form { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 18px; margin-top: 10px; }
        input { padding: 16px 20px; font-size: 16px; border: 1px solid #ccc; border-radius: 12px; }
        .login-btn { background-color: #f9c80e; border: none; padding: 16px; font-size: 18px; font-weight: 700; border-radius: 50px; cursor: pointer; }
        .error { color: #d32f2f; margin: 10px 0; font-weight: 600; }
        .register-link { margin: 15px 0; font-size: 16px; }
        .register-link a { color: #0a3472; font-weight: 600; text-decoration: none; }
        .back-link { margin-top: 25px; color: #0a3472; text-decoration: none; }
    </style>
</head>
<body>
    <div class="right-side">
        <div class="logo-row">
            <div class="logo-icon-wrap"><div class="logo-square"><span class="logo-letter-s">S</span><span class="logo-pencil">✏️</span></div></div>
            <span class="brand-text">studymate <span class="ph">ph</span></span>
        </div>
        <form method="POST">
            <input type="text" name="email_or_id" placeholder="Email or Student ID" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="login-btn">Log In</button>
        </form>
        {% if error %}<p class="error">❌ Wrong Email/ID or Password!</p>{% endif %}
        <p class="register-link">No account? <a href="/register">Register here</a></p>
        <a href="/" class="back-link">← Back to Home</a>
    </div>
<script src="/static/alarm.js"></script>
</body>
</html>'''

# === REGISTER ===
@app.route('/register', methods=['GET', 'POST'])
def register():
    if "user" in session: return redirect("/dashboard")
    if request.method == 'POST':
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        users = load_users()
        for uid, u in users.items():
            if u.get("email") == email: return "❌ Email already used! <a href='/register'>Go back</a>"
            if u.get("student_id") == student_id: return "❌ Student ID already used! <a href='/register'>Go back</a>"
        if password != confirm: return "❌ Passwords do not match! <a href='/register'>Go back</a>"
        uid = str(uuid.uuid4())[:8]
        users[uid] = {"name": name, "email": email, "student_id": student_id, "password": password}
        save_users(users)
        return redirect("/login")
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { min-height: 100vh; display: flex; }
        .right-side { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #fcf9f0; padding: 40px; }
        .logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; }
        .logo-icon-wrap { position: relative; width: 48px; height: 48px; }
        .logo-square { background-color: #0a3472; width: 48px; height: 48px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 28px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -5px; right: -5px; font-size: 30px; color: #f9c80e; }
        .brand-text { font-size: 36px; font-weight: 700; color: #0a3472; }
        .brand-text .ph { color: #f9c80e; }
        h2 { color: #0a3472; margin-bottom: 20px; }
        form { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 15px; }
        input { padding: 14px 18px; font-size: 15px; border: 1px solid #ccc; border-radius: 10px; }
        .register-btn { background-color: #f9c80e; border: none; padding: 14px; font-size: 17px; font-weight: 700; border-radius: 50px; cursor: pointer; margin-top: 10px; }
        .back-link { margin-top: 25px; color: #0a3472; text-decoration: none; }
    </style>
</head>
<body>
    <div class="right-side">
        <div class="logo-row">
            <div class="logo-icon-wrap"><div class="logo-square"><span class="logo-letter-s">S</span><span class="logo-pencil">✏️</span></div></div>
            <span class="brand-text">studymate <span class="ph">ph</span></span>
        </div>
        <h2>Create Account</h2>
        <form method="POST">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="email" name="email" placeholder="Email Address" required>
            <input type="text" name="student_id" placeholder="Student ID" required>
            <input type="password" name="password" placeholder="Password" required>
            <input type="password" name="confirm_password" placeholder="Confirm Password" required>
            <button type="submit" class="register-btn">Register</button>
        </form>
        <a href="/login" class="back-link">← Back to Log In</a>
    </div>
<script src="/static/alarm.js"></script>
</body>
</html>''')

# === DASHBOARD ===
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    users = load_users()
    user_id = session["user_id"]
    u = users.get(user_id, session.get("user", {}))
    session["user"] = u

    notifications = load_notifications()
    user_notifications = notifications.get(user_id, [])
    unread_count = sum(1 for n in user_notifications if not n.get("read", False))

    return render_template_string(DASHBOARD_HTML,
        user_name=u.get("name", "Student"),
        unread_count=unread_count
    )


DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard - StudyMate PH</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
body { min-height:100vh; background:#fcf9f0; padding:30px; }

.topbar {
    max-width:1000px;
    margin:0 auto 20px;
    display:flex;
    justify-content:flex-end;
    gap:12px;
}

.top-btn {
    position:relative;
    text-decoration:none;
    color:#0a3472;
    background:white;
    padding:12px 16px;
    border-radius:12px;
    font-weight:700;
    box-shadow:0 2px 8px rgba(0,0,0,.08);
}

.logout-btn {
    background:#d32f2f;
    color:white;
}

.logout-btn:hover {
    background:#b71c1c;
}

.badge {
    position:absolute;
    top:-7px;
    right:-7px;
    min-width:22px;
    height:22px;
    padding:2px 6px;
    border-radius:20px;
    background:#ef4444;
    color:white;
    font-size:12px;
    display:flex;
    align-items:center;
    justify-content:center;
}

.welcome-section {
    max-width:1000px;
    min-height:230px;
    margin:0 auto 22px;
    background-image:
        linear-gradient(rgba(10,52,114,.55), rgba(10,52,114,.55)),
        url('/static/bg.jpg');
    background-size:cover;
    background-position:center;
    background-repeat:no-repeat;
    border-radius:20px;
    padding:35px 45px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    color:white;
    box-shadow:0 5px 20px rgba(0,0,0,.12);
}

.welcome {
    font-size:38px;
    font-weight:800;
    line-height:1.15;
    margin-bottom:12px;
}

.encourage { font-size:20px; color:white; }

.menu-grid {
    max-width:1000px;
    margin:0 auto;
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    gap:15px;
}

.menu-item {
    font-size:18px;
    padding:17px 16px;
    display:flex;
    align-items:center;
    gap:12px;
    color:#111;
    text-decoration:none;
    background:white;
    border-radius:14px;
    transition:.2s;
    box-shadow:0 2px 10px rgba(0,0,0,.06);
}

.menu-item:hover {
    color:#0a3472;
    transform:translateY(-2px);
}

.icon { font-size:28px; }

.logout {
    display:block;
    max-width:1000px;
    margin:35px auto 0;
    font-size:16px;
    color:#d32f2f;
    text-decoration:none;
    font-weight:600;
}

@media(max-width:900px) {
    .menu-grid { grid-template-columns:repeat(2, 1fr); }
}

@media(max-width:600px) {
    body { padding:15px; }
    .welcome-section { padding:28px; min-height:210px; }
    .welcome { font-size:32px; }
    .encourage { font-size:16px; }
    .menu-grid { grid-template-columns:1fr 1fr; gap:10px; }
    .menu-item { font-size:16px; padding:14px 12px; }
    .icon { font-size:23px; }
}
</style>
</head>
<body>

<div class="topbar">
    <a href="/dashboard" class="top-btn">🏠 Dashboard</a>

    <a href="/notifications" class="top-btn">
        🔔 Notifications
        {% if unread_count > 0 %}
        <span class="badge">{{ unread_count }}</span>
        {% endif %}
    </a>

    <a href="/profile" class="top-btn">👤 Profile</a>

    <a href="/logout" class="top-btn logout-btn">↪ Logout</a>
</div>

<div class="welcome-section">
    <h1 class="welcome">Welcome,<br>{{ user_name }}!</h1>
    <p class="encourage">Keep going! You're doing great!</p>
</div>

<div class="menu-grid">
    <a href="/schedule" class="menu-item"><span class="icon">📅</span> Schedule</a>
    <a href="/deadlines" class="menu-item"><span class="icon">⏰</span> Deadlines</a>
    <a href="/group-projects" class="menu-item"><span class="icon">👥</span> Group Projects</a>
    <a href="/notes" class="menu-item"><span class="icon">📝</span> Notes</a>
</div>

<script src="/static/alarm.js"></script>
</body>
</html>'''



# === PROFILE ===

@app.route('/deadlines')
def deadlines():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    user_deadlines = all_deadlines.get(user_id, [])

    for item in user_deadlines:
        item["status"] = get_deadline_status(item)

    all_deadlines[user_id] = user_deadlines
    save_deadlines(all_deadlines)

    category = request.args.get("category", "All")
    status_filter = request.args.get("status", "All")
    search = request.args.get("search", "").strip().lower()

    filtered = user_deadlines[:]

    if category != "All":
        filtered = [d for d in filtered if d.get("category", "Other") == category]

    if status_filter != "All":
        wanted = {
            "Pending": ["upcoming", "soon"],
            "Overdue": ["overdue"],
            "Due Soon": ["soon"],
            "Completed": ["completed"]
        }.get(status_filter, [])
        filtered = [d for d in filtered if d.get("status") in wanted]

    if search:
        filtered = [
            d for d in filtered
            if search in d.get("subject", "").lower()
            or search in d.get("title", "").lower()
            or search in d.get("description", "").lower()
        ]

    filtered.sort(key=lambda d: (
        d.get("completed", False),
        d.get("due_date", "9999-12-31"),
        d.get("due_time", "23:59")
    ))

    categories = [
        "Assignment", "Project", "Exam", "Research",
        "Paper", "Presentation", "Quiz", "Other"
    ]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Deadlines - StudyMate PH</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#26354a}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.back{color:#315f9e;text-decoration:none;font-weight:600}
h1{margin:0 0 5px;font-size:32px}.subtitle{color:#718096;margin:0}
.add-btn,.primary{background:#315f9e;color:white;border:0;border-radius:10px;padding:12px 18px;cursor:pointer;font-weight:700}
.card{background:white;border-radius:16px;padding:20px;margin-bottom:18px;box-shadow:0 4px 18px rgba(0,0,0,.07)}
.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
input,select,textarea{width:100%;padding:11px 12px;border:1px solid #d9e0ea;border-radius:9px;font:inherit}
textarea{min-height:85px;resize:vertical}.full{grid-column:1/-1}
.form-actions,.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.secondary,.btn{border:0;border-radius:8px;padding:9px 12px;cursor:pointer;font-weight:600}
.secondary{background:#edf2f7;color:#334155}
.filters{display:grid;grid-template-columns:1.5fr 1fr 1fr auto;gap:10px}
.deadline{border-left:6px solid #5790cf;padding:17px 18px}
.deadline.overdue{border-left-color:#d9534f}.deadline.soon{border-left-color:#e69a27}
.deadline.completed{border-left-color:#45a66b;opacity:.82}
.deadline-head{display:flex;justify-content:space-between;gap:15px}
.subject{font-size:14px;color:#718096;font-weight:700;text-transform:uppercase}
.title{font-size:21px;font-weight:800;margin:4px 0}.meta{color:#667085;margin:7px 0}
.badge{display:inline-block;padding:5px 9px;border-radius:20px;background:#edf2f7;font-size:12px;font-weight:700}
.status-overdue{background:#fde7e7;color:#b42318}.status-soon{background:#fff0d7;color:#9a6700}
.status-completed{background:#e6f7ec;color:#147a3e}.status-upcoming{background:#e8f1fc;color:#245d9c}
.done{background:#e7f7ed;color:#18713c}.edit{background:#eaf1fb;color:#285c96}.delete{background:#fde8e8;color:#b42318}
.empty{text-align:center;padding:40px 15px;color:#718096}
@media(max-width:750px){.top{align-items:flex-start;gap:15px;flex-direction:column}.form-grid,.filters{grid-template-columns:1fr}.full{grid-column:auto}}
</style>
</head>
<body>
<div class="container">
<a href="/dashboard" class="back">← Back to Dashboard</a>
<div class="top">
<div><h1>📅 Deadlines</h1><p class="subtitle">Track your assignments, projects, exams and other school tasks.</p></div>
<button class="add-btn" onclick="document.getElementById('addForm').scrollIntoView({behavior:'smooth'})">+ Add Deadline</button>
</div>

<div class="card" id="addForm">
<h2 style="margin-top:0;">Add Deadline</h2>
<form method="POST" action="/deadlines/add">
<div class="form-grid">
<input name="subject" placeholder="Subject" required>
<input name="title" placeholder="Assignment / Project title" required>
<select name="category" required>{% for c in categories %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select>
<input type="date" name="due_date" required>
<input type="time" name="due_time" required>
<label style="grid-column:1/-1;font-weight:700;color:#315f9e;">⏰ Alarm / Reminder (Optional)</label>
<input type="date" name="alarm_date" title="Alarm Date">
<input type="time" name="alarm_time" title="Alarm Time">
<textarea class="full" name="description" placeholder="Description / notes (optional)"></textarea>
</div>
<div class="form-actions"><button class="primary" type="submit">Save Deadline</button><button class="secondary" type="reset">Clear</button></div>
</form>
</div>

<div class="card">
<form method="GET" class="filters">
<input name="search" value="{{ search }}" placeholder="🔍 Search deadline...">
<select name="category"><option>All</option>{% for c in categories %}<option value="{{ c }}" {% if category == c %}selected{% endif %}>{{ c }}</option>{% endfor %}</select>
<select name="status">
<option>All</option><option value="Pending" {% if status_filter == "Pending" %}selected{% endif %}>Pending</option>
<option value="Overdue" {% if status_filter == "Overdue" %}selected{% endif %}>Overdue</option>
<option value="Due Soon" {% if status_filter == "Due Soon" %}selected{% endif %}>Due Soon</option>
<option value="Completed" {% if status_filter == "Completed" %}selected{% endif %}>Completed</option>
</select>
<button class="primary" type="submit">Filter</button>
</form>
</div>

{% if filtered %}
{% for d in filtered %}
<div class="card deadline {{ d.status }}">
<div class="deadline-head"><div>
<div class="subject">{{ d.category }} • {{ d.subject }}</div>
<div class="title">{{ d.title }}</div>
{% if d.description %}<div class="meta">{{ d.description }}</div>{% endif %}
<div class="meta">📅 {{ d.due_date }} &nbsp; ⏰ {{ d.due_time }} &nbsp; • &nbsp; {{ deadline_days_left(d) }}</div>
</div>
<div><span class="badge status-{{ d.status }}">{{ deadline_icon(d.status) }} {{ deadline_status_text(d.status) }}</span></div>
</div>
<div class="actions">
{% if not d.completed %}
<form method="POST" action="/deadlines/{{ d.id }}/complete"><button class="btn done" type="submit">✓ Mark as Completed</button></form>
{% else %}
<form method="POST" action="/deadlines/{{ d.id }}/pending"><button class="btn done" type="submit">↩ Mark as Pending</button></form>
{% endif %}
<a class="btn edit" href="/deadlines/{{ d.id }}/edit">✏ Edit</a>
<form method="POST" action="/deadlines/{{ d.id }}/delete" onsubmit="return confirm('Delete this deadline?');"><button class="btn delete" type="submit">🗑 Delete</button></form>
</div>
</div>
{% endfor %}
{% else %}
<div class="card empty"><h2>No deadlines found</h2><p>Add your first assignment, project, exam or school task.</p></div>
{% endif %}
</div>
<script src="/static/alarm.js"></script>
</body>
</html>
""", categories=categories, filtered=filtered, category=category,
category_filter=category, status_filter=status_filter, search=search,
deadline_days_left=deadline_days_left, deadline_icon=deadline_icon,
deadline_status_text=deadline_status_text)


@app.route('/deadlines/add', methods=['POST'])
def add_deadline():
    if "user_id" not in session:
        return redirect(url_for("login"))
    try:
        datetime.strptime(request.form["due_date"] + " " + request.form["due_time"], "%Y-%m-%d %H:%M")
    except:
        return "Invalid date or time.", 400

    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    all_deadlines.setdefault(user_id, [])

    d = {
        "id": str(int(datetime.now().timestamp() * 1000000)),
        "subject": request.form.get("subject", "").strip(),
        "title": request.form.get("title", "").strip(),
        "category": request.form.get("category", "Other"),
        "due_date": request.form.get("due_date", ""),
        "due_time": request.form.get("due_time", ""),
        "alarm_date": request.form.get("alarm_date", ""),
        "alarm_time": request.form.get("alarm_time", ""),
        "description": request.form.get("description", "").strip(),
        "completed": False
    }
    all_deadlines[user_id].append(d)
    save_deadlines(all_deadlines)
    add_notification(user_id, "New Deadline Added", f"{d['title']} is due on {d['due_date']} at {d['due_time']}.")
    return redirect(url_for("deadlines"))


@app.route('/deadlines/<deadline_id>/complete', methods=['POST'])
def complete_deadline(deadline_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    for d in all_deadlines.get(user_id, []):
        if str(d.get("id")) == str(deadline_id):
            d["completed"] = True
            add_notification(user_id, "Deadline Completed", f"You completed: {d.get('title', 'deadline')}.")
            break
    save_deadlines(all_deadlines)
    return redirect(url_for("deadlines"))


@app.route('/deadlines/<deadline_id>/pending', methods=['POST'])
def pending_deadline(deadline_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    for d in all_deadlines.get(user_id, []):
        if str(d.get("id")) == str(deadline_id):
            d["completed"] = False
            break
    save_deadlines(all_deadlines)
    return redirect(url_for("deadlines"))


@app.route('/deadlines/<deadline_id>/delete', methods=['POST'])
def delete_deadline(deadline_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    items = all_deadlines.get(user_id, [])
    for d in items:
        if str(d.get("id")) == str(deadline_id):
            title = d.get("title", "deadline")
            all_deadlines[user_id] = [x for x in items if str(x.get("id")) != str(deadline_id)]
            save_deadlines(all_deadlines)
            add_notification(user_id, "Deadline Deleted", f"{title} was removed from your deadlines.")
            break
    return redirect(url_for("deadlines"))


@app.route('/deadlines/<deadline_id>/edit', methods=['GET', 'POST'])
def edit_deadline(deadline_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = str(session["user_id"])
    all_deadlines = load_deadlines()
    target = next((d for d in all_deadlines.get(user_id, []) if str(d.get("id")) == str(deadline_id)), None)
    if target is None:
        return "Deadline not found.", 404

    categories = ["Assignment", "Project", "Exam", "Research", "Paper", "Presentation", "Quiz", "Other"]

    if request.method == "POST":
        try:
            datetime.strptime(request.form["due_date"] + " " + request.form["due_time"], "%Y-%m-%d %H:%M")
        except:
            return "Invalid date or time.", 400
        target.update({
            "subject": request.form.get("subject", "").strip(),
            "title": request.form.get("title", "").strip(),
            "category": request.form.get("category", "Other"),
            "due_date": request.form.get("due_date", ""),
            "due_time": request.form.get("due_time", ""),
            "alarm_date": request.form.get("alarm_date", ""),
            "alarm_time": request.form.get("alarm_time", ""),
            "description": request.form.get("description", "").strip()
        })
        save_deadlines(all_deadlines)
        add_notification(user_id, "Deadline Updated", f"{target['title']} was updated.")
        return redirect(url_for("deadlines"))

    return render_template_string("""
<!DOCTYPE html>
<html><head><title>Edit Deadline - StudyMate PH</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;color:#26354a}
.box{max-width:700px;margin:45px auto;background:white;padding:28px;border-radius:16px;box-shadow:0 4px 18px rgba(0,0,0,.08)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
input,select,textarea{width:100%;box-sizing:border-box;padding:11px;border:1px solid #d9e0ea;border-radius:9px;font:inherit}
textarea{min-height:100px;grid-column:1/-1}
button{padding:11px 18px;border:0;border-radius:9px;background:#315f9e;color:white;font-weight:700;cursor:pointer}
a{color:#315f9e;text-decoration:none}
@media(max-width:650px){.grid{grid-template-columns:1fr}textarea{grid-column:auto}}
</style></head>
<body><div class="box"><a href="/deadlines">← Back to Deadlines</a>
<h1>✏ Edit Deadline</h1><form method="POST"><div class="grid">
<input name="subject" value="{{ d.subject }}" placeholder="Subject" required>
<input name="title" value="{{ d.title }}" placeholder="Title" required>
<select name="category">{% for c in categories %}<option value="{{ c }}" {% if d.category == c %}selected{% endif %}>{{ c }}</option>{% endfor %}</select>
<input type="date" name="due_date" value="{{ d.due_date }}" required>
<input type="time" name="due_time" value="{{ d.due_time }}" required>
<label>⏰ Alarm / Reminder (Optional)</label>
<input type="date" name="alarm_date" value="{{ d.get('alarm_date','') }}">
<input type="time" name="alarm_time" value="{{ d.get('alarm_time','') }}">
<textarea name="description" placeholder="Description / notes">{{ d.description }}</textarea>
</div><br><button type="submit">Save Changes</button></form></div><script src="/static/alarm.js"></script>
</body></html>
""", d=target, categories=categories)




@app.route('/notes')
def notes_page():
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    all_notes = load_notes()
    notes = all_notes.get(user_id, [])

    category = request.args.get("category", "All")
    search = request.args.get("search", "").strip().lower()
    categories = ["All", "Subject", "Reminder", "Review", "Ideas", "Other"]

    filtered = []
    for note in notes:
        if category != "All" and note.get("category") != category:
            continue
        text = " ".join([
            note.get("title", ""),
            note.get("subject", ""),
            note.get("content", ""),
            note.get("category", "")
        ]).lower()
        if search and search not in text:
            continue
        filtered.append(note)

    filtered.sort(key=lambda x: (not x.get("pinned", False), x.get("created_at", "")))

    return render_template_string(
        NOTES_HTML,
        notes=filtered,
        categories=categories,
        selected_category=category,
        search=request.args.get("search", "")
    )


@app.route('/notes/add', methods=['POST'])
def add_note():
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    all_notes = load_notes()
    all_notes.setdefault(user_id, [])

    all_notes[user_id].append({
        "id": str(uuid.uuid4())[:8],
        "title": request.form.get("title", "").strip(),
        "subject": request.form.get("subject", "").strip(),
        "category": request.form.get("category", "Other").strip(),
        "content": request.form.get("content", "").strip(),
        "pinned": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "display_date": datetime.now().strftime("%B %d, %Y %I:%M %p")
    })

    save_notes(all_notes)
    return redirect("/notes")


@app.route('/notes/<note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    all_notes = load_notes()
    notes = all_notes.get(user_id, [])
    note = next((n for n in notes if str(n.get("id")) == str(note_id)), None)

    if not note:
        return "Note not found.", 404

    if request.method == "POST":
        note["title"] = request.form.get("title", "").strip()
        note["subject"] = request.form.get("subject", "").strip()
        note["category"] = request.form.get("category", "Other").strip()
        note["content"] = request.form.get("content", "").strip()
        save_notes(all_notes)
        return redirect("/notes")

    return render_template_string(NOTE_EDIT_HTML, note=note)


@app.route('/notes/<note_id>/delete', methods=['POST'])
def delete_note(note_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    all_notes = load_notes()
    notes = all_notes.get(user_id, [])

    all_notes[user_id] = [n for n in notes if str(n.get("id")) != str(note_id)]
    save_notes(all_notes)
    return redirect("/notes")


@app.route('/notes/<note_id>/pin', methods=['POST'])
def pin_note(note_id):
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    all_notes = load_notes()
    notes = all_notes.get(user_id, [])

    for note in notes:
        if str(note.get("id")) == str(note_id):
            note["pinned"] = not note.get("pinned", False)
            break

    save_notes(all_notes)
    return redirect("/notes")


NOTES_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Notes - StudyMate PH</title>
<style>
*{box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{margin:0;background:#f7f8fc;color:#26354a;padding:30px}
.container{max-width:1100px;margin:auto}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.back{color:#0a3472;text-decoration:none;font-weight:700}
h1{color:#0a3472;margin:8px 0}.sub{color:#718096}
.grid{display:grid;grid-template-columns:330px 1fr;gap:20px}
.card{background:white;border-radius:18px;padding:22px;box-shadow:0 4px 18px rgba(0,0,0,.07);margin-bottom:18px}
input,select,textarea{width:100%;padding:11px;border:1px solid #d6dce5;border-radius:9px;margin:7px 0;font-size:15px}
textarea{min-height:150px;resize:vertical}
button,.btn{border:0;border-radius:9px;padding:10px 14px;cursor:pointer;font-weight:700;text-decoration:none;display:inline-block}
.primary{background:#315f9e;color:white}.yellow{background:#f9c80e;color:#222}.danger{background:#fde8e8;color:#b42318}.gray{background:#eef2f7;color:#344054}
.note{border-left:5px solid #315f9e}.note.pinned{border-left-color:#f9c80e}
.note h2{margin:0 0 5px;color:#0a3472}.meta{color:#718096;font-size:13px;margin:5px 0}
.content{white-space:pre-wrap;line-height:1.55;margin:14px 0}
.actions{display:flex;gap:7px;flex-wrap:wrap}
.empty{text-align:center;color:#718096;padding:35px}
@media(max-width:800px){.grid{grid-template-columns:1fr}body{padding:15px}}
</style>
</head>
<body>
<div class="container">
<div class="top">
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:20px;">
<a class="back" href="/dashboard">← Back to Dashboard</a>
</div>
<a class="back" href="/profile">👤 Profile</a>
</div>

<h1>📝 Notes</h1>
<p class="sub">Keep your personal study notes, reminders, reviews, and ideas in one place.</p>

<div class="grid">
<div>
<div class="card">
<h2>➕ Add Note</h2>
<form method="POST" action="/notes/add">
<input name="title" placeholder="Note title" required>
<input name="subject" placeholder="Subject (optional)">
<select name="category">
{% for c in categories if c != "All" %}<option value="{{ c }}">{{ c }}</option>{% endfor %}
</select>
<textarea name="content" placeholder="Write your notes here..." required></textarea>
<button class="primary" type="submit">Save Note</button>
</form>
</div>

<div class="card">
<h3>🔍 Search & Filter</h3>
<form method="GET">
<input name="search" value="{{ search }}" placeholder="Search notes...">
<select name="category">
{% for c in categories %}
<option value="{{ c }}" {% if selected_category == c %}selected{% endif %}>{{ c }}</option>
{% endfor %}
</select>
<button class="gray" type="submit">Apply</button>
</form>
</div>
</div>

<div>
{% if notes %}
{% for note in notes %}
<div class="card note {% if note.pinned %}pinned{% endif %}">
<h2>{% if note.pinned %}📌 {% endif %}{{ note.title }}</h2>
<div class="meta">📚 {{ note.subject or "No subject" }} · 🏷️ {{ note.category }} · {{ note.display_date }}</div>
<div class="content">{{ note.content }}</div>
<div class="actions">
<form method="POST" action="/notes/{{ note.id }}/pin"><button class="yellow" type="submit">{% if note.pinned %}Unpin{% else %}📌 Pin{% endif %}</button></form>
<a class="btn gray" href="/notes/{{ note.id }}/edit">✏️ Edit</a>
<form method="POST" action="/notes/{{ note.id }}/delete" onsubmit="return confirm('Delete this note?')"><button class="danger" type="submit">🗑️ Delete</button></form>
</div>
</div>
{% endfor %}
{% else %}
<div class="card empty"><h2>No notes yet.</h2><p>Create your first note using the Add Note form.</p></div>
{% endif %}
</div>
</div>
</div>
<script src="/static/alarm.js"></script>
</body>
</html>'''


NOTE_EDIT_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Edit Note - StudyMate PH</title>
<style>
*{box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{margin:0;background:#f7f8fc;padding:30px}
.card{max-width:700px;margin:30px auto;background:white;padding:30px;border-radius:18px;box-shadow:0 4px 18px rgba(0,0,0,.08)}
input,select,textarea{width:100%;padding:12px;border:1px solid #d6dce5;border-radius:9px;margin:7px 0 15px;font-size:15px}
textarea{min-height:220px}
button{padding:12px 18px;border:0;border-radius:25px;background:#f9c80e;font-weight:800;cursor:pointer}
a{color:#0a3472;font-weight:700;text-decoration:none;margin-left:12px}
</style>
</head>
<body>
<div class="card">
<h1>✏️ Edit Note</h1>
<form method="POST">
<label>Title</label>
<input name="title" value="{{ note.title }}" required>
<label>Subject</label>
<input name="subject" value="{{ note.subject }}">
<label>Category</label>
<select name="category">
{% for c in ["Subject","Reminder","Review","Ideas","Other"] %}
<option value="{{ c }}" {% if note.category == c %}selected{% endif %}>{{ c }}</option>
{% endfor %}
</select>
<label>Content</label>
<textarea name="content" required>{{ note.content }}</textarea>
<button type="submit">💾 Save Changes</button>
<a href="/notes">Cancel</a>
</form>
</div>
<script src="/static/alarm.js"></script>
</body>
</html>'''


@app.route('/group-projects')
def group_projects():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str(session["user_id"])
    groups = load_groups()

    my_groups = []
    for group in groups.values():
        if user_id in [str(x) for x in group.get("members", [])]:
            group_copy = dict(group)
            group_copy["progress"] = group_progress(group)
            group_copy["leader_name"] = get_user_name(group.get("leader_id"))
            my_groups.append(group_copy)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Group Projects - StudyMate PH</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#26354a}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.back{color:#315f9e;text-decoration:none;font-weight:600}
h1{margin:10px 0 5px;font-size:32px}.subtitle{color:#718096;margin:0 0 22px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:white;border-radius:16px;padding:22px;box-shadow:0 4px 18px rgba(0,0,0,.07);margin-bottom:18px}
.card h2{margin-top:0;color:#0a3472}
input,select,textarea{width:100%;padding:11px 12px;border:1px solid #d9e0ea;border-radius:9px;font:inherit;margin-bottom:10px}
textarea{min-height:85px;resize:vertical}
button,.btn{border:0;border-radius:9px;padding:10px 15px;cursor:pointer;font-weight:700;text-decoration:none;display:inline-block}
.primary{background:#315f9e;color:white}.join{background:#f0b90b;color:#26354a}
.project{border-left:6px solid #315f9e}
.project h3{margin:0 0 5px;font-size:21px}
.meta{color:#667085;margin:6px 0}
.code{font-weight:800;letter-spacing:2px;background:#edf3fb;padding:5px 9px;border-radius:7px}
.progress{height:10px;background:#e7edf5;border-radius:10px;overflow:hidden;margin:10px 0}
.progress-bar{height:100%;background:#315f9e}
.empty{text-align:center;color:#718096;padding:30px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<a href="/dashboard" class="back">← Back to Dashboard</a>
<h1>👥 Group Projects</h1>
<p class="subtitle">Create a project for your group or join one using the group name and private code.</p>

<div class="grid">
<div class="card">
<h2>➕ Create Group Project</h2>
<form method="POST" action="/group-projects/create">
<input name="name" placeholder="Group Project Name" required>
<input name="subject" placeholder="Subject" required>
<input type="date" name="deadline">
<label style="font-weight:700;color:#315f9e;">⏰ Alarm / Reminder (Optional)</label>
<input type="date" name="alarm_date">
<input type="time" name="alarm_time">
<textarea name="description" placeholder="Project description"></textarea>
<button class="primary" type="submit">Create Group</button>
</form>
</div>

<div class="card">
<h2>🔑 Join Group Project</h2>
<p style="color:#667085;">The leader should give you the exact group name and private code.</p>
<form method="POST" action="/group-projects/join">
<input name="name" placeholder="Group Name" required>
<input name="code" placeholder="Group Code" required>
<button class="join" type="submit">Join Group</button>
</form>
</div>
</div>

<h2>My Group Projects</h2>

{% if my_groups %}
{% for g in my_groups %}
<div class="card project">
<h3>👥 {{ g.name }}</h3>
<div class="meta">📚 {{ g.subject }} &nbsp; • &nbsp; 👤 Leader: {{ g.leader_name }}</div>
{% if g.deadline %}<div class="meta">📅 Deadline: {{ g.deadline }}</div>{% endif %}
{% if g.get('alarm_date') and g.get('alarm_time') %}<div class="meta">⏰ Alarm: {{ g.alarm_date }} at {{ g.alarm_time }}</div>{% endif %}
<div class="meta">🔐 Code: <span class="code">{{ g.code }}</span> &nbsp; • &nbsp; 👥 {{ g.members|length }} members</div>
{% if g.description %}<p>{{ g.description }}</p>{% endif %}
<div class="meta">Progress: {{ g.progress }}%</div>
<div class="progress"><div class="progress-bar" style="width:{{ g.progress }}%"></div></div>
<a class="btn primary" href="/group-projects/{{ g.id }}">View Project</a>
</div>
{% endfor %}
{% else %}
<div class="card empty">
<h3>No group projects yet.</h3>
<p>Create a group project or join one using the group name and code.</p>
</div>
{% endif %}
</div>
<script src="/static/alarm.js"></script>
</body>
</html>
""", my_groups=my_groups)


@app.route('/group-projects/create', methods=['POST'])
def create_group_project():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str(session["user_id"])
    groups = load_groups()

    # Generate a short private code. The leader can share it only with selected classmates.
    code_value = uuid.uuid4().hex[:6].upper()

    while any(g.get("code") == code_value for g in groups.values()):
        code_value = uuid.uuid4().hex[:6].upper()

    group_id = str(uuid.uuid4())[:8]
    group = {
        "id": group_id,
        "name": request.form.get("name", "").strip(),
        "subject": request.form.get("subject", "").strip(),
        "description": request.form.get("description", "").strip(),
        "deadline": request.form.get("deadline", ""),
        "alarm_date": request.form.get("alarm_date", ""),
        "alarm_time": request.form.get("alarm_time", ""),
        "code": code_value,
        "leader_id": user_id,
        "members": [user_id],
        "tasks": [],
        "notes": [],
        "meetings": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    groups[group_id] = group
    save_groups(groups)

    add_notification(
        user_id,
        "Group Project Created",
        f"You created '{group['name']}'. Group code: {group['code']}."
    )

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/join', methods=['POST'])
def join_group_project():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str(session["user_id"])
    group_name = request.form.get("name", "").strip().lower()
    group_code = request.form.get("code", "").strip().upper()

    groups = load_groups()
    target = None

    for group in groups.values():
        if (
            group.get("name", "").strip().lower() == group_name
            and group.get("code", "").strip().upper() == group_code
        ):
            target = group
            break

    if target is None:
        return """
        <div style="font-family:Arial;padding:40px">
        ❌ Invalid Group Name or Code.<br><br>
        <a href="/group-projects">← Go back</a>
        </div>
        """, 400

    if user_id in [str(x) for x in target.get("members", [])]:
        return redirect(url_for("group_project_detail", group_id=target["id"]))

    target.setdefault("members", []).append(user_id)
    save_groups(groups)

    student_name = get_user_name(user_id)
    leader_id = str(target["leader_id"])

    # Notify the leader that the selected student used the shared code and joined.
    add_notification(
        leader_id,
        "New Group Member",
        f"{student_name} joined your group project '{target['name']}'."
    )

    # Notify the student who joined.
    add_notification(
        user_id,
        "Joined Group Project",
        f"You joined '{target['name']}' successfully."
    )

    # Notify existing members about the new member.
    notify_group_members(
        target,
        "New Group Member",
        f"{student_name} joined '{target['name']}'.",
        exclude_user_id=user_id
    )

    return redirect(url_for("group_project_detail", group_id=target["id"]))


@app.route('/group-projects/<group_id>')
def group_project_detail(group_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = str(session["user_id"])
    groups = load_groups()
    group = find_group(groups, group_id)

    if not group:
        return "Group project not found.", 404

    member_ids = [str(x) for x in group.get("members", [])]
    if user_id not in member_ids:
        return "You are not a member of this group.", 403

    members = [
        {
            "id": mid,
            "name": get_user_name(mid),
            "is_leader": str(mid) == str(group.get("leader_id"))
        }
        for mid in member_ids
    ]

    tasks = group.get("tasks", [])
    progress = group_progress(group)

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>{{ group.name }} - Group Project</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#26354a}
.container{max-width:1100px;margin:30px auto;padding:0 20px}
.back{color:#315f9e;text-decoration:none;font-weight:600}
.hero{background:#315f9e;color:white;padding:25px;border-radius:18px;margin:15px 0 20px}
.hero h1{margin:0 0 7px}.hero p{margin:5px 0}
.code{background:white;color:#315f9e;padding:5px 10px;border-radius:7px;font-weight:800;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:white;border-radius:16px;padding:20px;box-shadow:0 4px 18px rgba(0,0,0,.07);margin-bottom:18px}
.card h2{margin-top:0;color:#0a3472}
input,select,textarea{width:100%;padding:10px;border:1px solid #d9e0ea;border-radius:8px;font:inherit;margin-bottom:9px}
textarea{min-height:80px}
button{border:0;border-radius:8px;padding:9px 13px;background:#315f9e;color:white;font-weight:700;cursor:pointer}
.task{padding:12px;border:1px solid #e2e8f0;border-radius:10px;margin:8px 0}
.task.done{background:#eef9f1;text-decoration:line-through;opacity:.8}
.small{font-size:13px;color:#718096}
.progress{height:12px;background:#e7edf5;border-radius:10px;overflow:hidden}
.bar{height:100%;background:#315f9e}
.note,.meeting{padding:10px;border-bottom:1px solid #e5e7eb}
.member{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #edf0f4}
.danger{background:#fde8e8;color:#b42318}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<a class="back" href="/group-projects">← Back to Group Projects</a>

<div class="hero">
<h1>👥 {{ group.name }}</h1>
<p>📚 {{ group.subject }}</p>
{% if group.description %}<p>{{ group.description }}</p>{% endif %}
<p>📅 Deadline: {{ group.deadline or "No deadline set" }}</p>
{% if group.get('alarm_date') and group.get('alarm_time') %}
<p>⏰ Alarm: {{ group.alarm_date }} at {{ group.alarm_time }}</p>
{% endif %}
<p>🔐 Share this code only with classmates you want to join:
<span class="code">{{ group.code }}</span></p>
</div>

<div class="grid">
<div>
<div class="card">
<h2>📊 Project Progress</h2>
<strong>{{ progress }}%</strong>
<div class="progress" style="margin:10px 0 15px"><div class="bar" style="width:{{ progress }}%"></div></div>
<p class="small">{{ tasks|selectattr("completed")|list|length }} of {{ tasks|length }} tasks completed.</p>
</div>

<div class="card">
<h2>👤 Group Members</h2>
{% for m in members %}
<div class="member"><span>👤 {{ m.name }}</span>{% if m.is_leader %}<b>Leader</b>{% endif %}</div>
{% endfor %}
</div>

<div class="card">
<h2>📋 Tasks</h2>
<form method="POST" action="/group-projects/{{ group.id }}/tasks/add">
<input name="title" placeholder="Task title" required>
<select name="assigned_to" required>
{% for m in members %}<option value="{{ m.id }}">{{ m.name }}</option>{% endfor %}
</select>
<button type="submit">+ Add Task</button>
</form>

{% for task in tasks %}
<div class="task {% if task.completed %}done{% endif %}">
<b>{{ "☑" if task.completed else "☐" }} {{ task.title }}</b>
<div class="small">Assigned to: {{ task.assigned_name }}</div>
<div style="margin-top:7px">
{% if not task.completed %}
<form method="POST" action="/group-projects/{{ group.id }}/tasks/{{ task.id }}/complete" style="display:inline">
<button type="submit">Mark Done</button>
</form>
{% else %}
<form method="POST" action="/group-projects/{{ group.id }}/tasks/{{ task.id }}/pending" style="display:inline">
<button type="submit">Mark Pending</button>
</form>
{% endif %}
<form method="POST" action="/group-projects/{{ group.id }}/tasks/{{ task.id }}/delete" style="display:inline">
<button class="danger" type="submit">Delete</button>
</form>
</div>
</div>
{% endfor %}
</div>
</div>

<div>
<div class="card">
<h2>📝 Group Notes</h2>
<form method="POST" action="/group-projects/{{ group.id }}/notes/add">
<textarea name="note" placeholder="Add a group note..." required></textarea>
<button type="submit">Add Note</button>
</form>
{% for n in group.notes %}
<div class="note"><b>{{ n.author_name }}</b><br>{{ n.text }}<div class="small">{{ n.date }}</div></div>
{% endfor %}
</div>

<div class="card">
<h2>📅 Meetings</h2>
<form method="POST" action="/group-projects/{{ group.id }}/meetings/add">
<input name="title" placeholder="Meeting title" required>
<input type="date" name="date" required>
<input type="time" name="time" required>
<input name="location" placeholder="Location / online meeting">
<button type="submit">Add Meeting</button>
</form>
{% for m in group.meetings %}
<div class="meeting"><b>{{ m.title }}</b><br>📅 {{ m.date }} ⏰ {{ m.time }}<br>📍 {{ m.location or "Not specified" }}<div class="small">Added by {{ m.author_name }}</div></div>
{% endfor %}
</div>

{% if user_id == group.leader_id %}
<div class="card">
<h2>🔐 Group Code</h2>
<p>Only students who know both the exact group name and this code can join through the Join Group form.</p>
<p style="font-size:24px;font-weight:800;letter-spacing:4px;color:#315f9e">{{ group.code }}</p>
</div>
{% endif %}
</div>
</div>
</div>
<script src="/static/alarm.js"></script>
</body>
</html>
""", group=group, members=members, tasks=[
        dict(t, assigned_name=get_user_name(t.get("assigned_to")))
        for t in tasks
    ], progress=progress, user_id=user_id)


def require_group_member(group_id):
    if "user_id" not in session:
        return None, redirect(url_for("login"))

    user_id = str(session["user_id"])
    groups = load_groups()
    group = find_group(groups, group_id)

    if not group:
        return None, ("Group project not found.", 404)

    if user_id not in [str(x) for x in group.get("members", [])]:
        return None, ("You are not a member of this group.", 403)

    return (groups, group, user_id), None


@app.route('/group-projects/<group_id>/tasks/add', methods=['POST'])
def add_group_task(group_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    assigned_to = str(request.form.get("assigned_to", ""))
    if assigned_to not in [str(x) for x in group.get("members", [])]:
        return "Invalid group member.", 400

    task = {
        "id": str(uuid.uuid4())[:8],
        "title": request.form.get("title", "").strip(),
        "assigned_to": assigned_to,
        "completed": False
    }
    group.setdefault("tasks", []).append(task)
    save_groups(groups)

    notify_group_members(
        group,
        "New Group Task",
        f"{get_user_name(user_id)} added task '{task['title']}' to '{group['name']}'."
    )
    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/<group_id>/tasks/<task_id>/complete', methods=['POST'])
def complete_group_task(group_id, task_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    for task in group.get("tasks", []):
        if str(task.get("id")) == str(task_id):
            task["completed"] = True
            save_groups(groups)
            notify_group_members(
                group,
                "Group Task Completed",
                f"{get_user_name(user_id)} completed '{task['title']}' in '{group['name']}'.",
                exclude_user_id=user_id
            )
            break

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/<group_id>/tasks/<task_id>/pending', methods=['POST'])
def pending_group_task(group_id, task_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    for task in group.get("tasks", []):
        if str(task.get("id")) == str(task_id):
            task["completed"] = False
            save_groups(groups)
            break

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/<group_id>/tasks/<task_id>/delete', methods=['POST'])
def delete_group_task(group_id, task_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    for task in group.get("tasks", []):
        if str(task.get("id")) == str(task_id):
            title = task.get("title", "task")
            group["tasks"] = [
                x for x in group.get("tasks", [])
                if str(x.get("id")) != str(task_id)
            ]
            save_groups(groups)
            notify_group_members(
                group,
                "Group Task Deleted",
                f"{get_user_name(user_id)} deleted task '{title}' from '{group['name']}'.",
                exclude_user_id=user_id
            )
            break

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/<group_id>/notes/add', methods=['POST'])
def add_group_note(group_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    text_value = request.form.get("note", "").strip()
    if text_value:
        group.setdefault("notes", []).append({
            "text": text_value,
            "author_id": user_id,
            "author_name": get_user_name(user_id),
            "date": datetime.now().strftime("%B %d, %Y %I:%M %p")
        })
        save_groups(groups)
        notify_group_members(
            group,
            "New Group Note",
            f"{get_user_name(user_id)} added a note in '{group['name']}'.",
            exclude_user_id=user_id
        )

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/group-projects/<group_id>/meetings/add', methods=['POST'])
def add_group_meeting(group_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result

    meeting = {
        "title": request.form.get("title", "").strip(),
        "date": request.form.get("date", ""),
        "time": request.form.get("time", ""),
        "location": request.form.get("location", "").strip(),
        "author_name": get_user_name(user_id)
    }

    group.setdefault("meetings", []).append(meeting)
    save_groups(groups)

    notify_group_members(
        group,
        "New Group Meeting",
        f"{meeting['title']} is scheduled for {meeting['date']} at {meeting['time']}.",
        exclude_user_id=user_id
    )

    return redirect(url_for("group_project_detail", group_id=group_id))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    users = load_users()
    user = users.get(user_id)

    if not user:
        session.clear()
        return redirect("/login")

    message = ""
    error = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        student_id = request.form.get("student_id", "").strip()
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not name or not email or not student_id:
            error = "Please fill in all required fields."

        if not error:
            for uid, other in users.items():
                if uid != user_id and other.get("email") == email:
                    error = "Email already used by another account."
                    break
                if uid != user_id and other.get("student_id") == student_id:
                    error = "Student ID already used by another account."
                    break

        if not error and new_password:
            if old_password != user.get("password"):
                error = "Current password is incorrect."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                user["password"] = new_password

        if not error:
            user["name"] = name
            user["email"] = email
            user["student_id"] = student_id
            users[user_id] = user
            save_users(users)
            session["user"] = user
            message = "Profile updated successfully!"

    return render_template_string(PROFILE_HTML,
                                  user=user,
                                  message=message,
                                  error=error)


PROFILE_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Profile - StudyMate PH</title>
<style>
* { box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
body { margin:0; background:#fcf9f0; padding:35px; }
.card { max-width:650px; margin:auto; background:white; padding:35px; border-radius:18px; box-shadow:0 4px 20px rgba(0,0,0,.08); }
h1 { color:#0a3472; }
form { display:flex; flex-direction:column; gap:12px; }
label { font-weight:700; }
input { padding:13px; border:1px solid #ccc; border-radius:10px; font-size:15px; }
.save { margin-top:10px; padding:14px; border:0; border-radius:30px; background:#f9c80e; font-weight:800; cursor:pointer; }
.success { padding:12px; background:#e8f7e8; color:#237b35; border-radius:8px; margin-bottom:15px; }
.error { padding:12px; background:#ffebee; color:#c62828; border-radius:8px; margin-bottom:15px; }
.back { display:inline-block; margin-top:20px; color:#0a3472; font-weight:700; text-decoration:none; }
</style>
</head>
<body>
<div class="card">
<h1>👤 My Profile</h1>
<p>Edit your StudyMate PH account information.</p>

{% if message %}<div class="success">✅ {{ message }}</div>{% endif %}
{% if error %}<div class="error">❌ {{ error }}</div>{% endif %}

<form method="POST">
<label>Full Name</label>
<input type="text" name="name" value="{{ user.get('name','') }}" required>

<label>Email Address</label>
<input type="email" name="email" value="{{ user.get('email','') }}" required>

<label>Student ID</label>
<input type="text" name="student_id" value="{{ user.get('student_id','') }}" required>

<hr>

<h3>🔐 Change Password</h3>
<p>Leave the password fields blank if you don't want to change it.</p>

<label>Current Password</label>
<input type="password" name="old_password">

<label>New Password</label>
<input type="password" name="new_password">

<label>Confirm New Password</label>
<input type="password" name="confirm_password">

<button class="save" type="submit">💾 Save Changes</button>
</form>

<a class="back" href="/dashboard">← Back to Dashboard</a>
</div>
<script src="/static/alarm.js"></script>
</body>
</html>'''


# === NOTIFICATIONS ===
@app.route('/notifications')
def notifications_page():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    notifications = load_notifications()
    user_notifications = notifications.get(user_id, [])

    for n in user_notifications:
        n["read"] = True

    notifications[user_id] = user_notifications
    save_notifications(notifications)

    return render_template_string(NOTIFICATIONS_HTML,
                                  user_notifications=user_notifications)


NOTIFICATIONS_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Notifications - StudyMate PH</title>
<style>
* { box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
body { margin:0; background:#fcf9f0; padding:35px; }
.card { max-width:800px; margin:auto; background:white; padding:35px; border-radius:18px; box-shadow:0 4px 20px rgba(0,0,0,.08); }
h1 { color:#0a3472; }
.notification { padding:18px; margin:12px 0; background:#f7f9fc; border-left:5px solid #0a3472; border-radius:10px; }
.date { font-size:12px; color:#888; margin-top:8px; }
.empty { text-align:center; color:#777; padding:40px; }
.delete-notification { border:0; background:#fde8e8; color:#b42318; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:700; }
.back { display:inline-block; margin-top:20px; color:#0a3472; font-weight:700; text-decoration:none; }
</style>
</head>
<body>
<div class="card">
<h1>🔔 Notifications</h1>
<p>Your latest StudyMate PH updates.</p>

{% if user_notifications %}
    {% for n in user_notifications|reverse %}
    <div class="notification">
        <h3>{{ n.get('title','Notification') }}</h3>
        <p>{{ n.get('message','') }}</p>
        <div class="date">{{ n.get('date','') }}</div>
        <form method="POST" action="/notifications/delete/{{ loop.index0 }}" style="margin-top:10px;"
              onsubmit="return confirm('Delete this notification?');">
            <button type="submit" class="delete-notification">🗑️ Delete</button>
        </form>
    </div>
    {% endfor %}
{% else %}
    <div class="empty">🔕 No notifications yet.</div>
{% endif %}

<a class="back" href="/dashboard">← Back to Dashboard</a>
</div>
<script src="/static/alarm.js"></script>
</body>
</html>'''



@app.route('/notifications/delete/<int:index>', methods=['POST'])
def delete_notification(index):
    if "user_id" not in session:
        return redirect("/login")

    user_id = str(session["user_id"])
    notifications = load_notifications()
    items = notifications.get(user_id, [])

    # Notifications are displayed newest-first, so convert the displayed
    # index back to the original list index.
    real_index = len(items) - 1 - index
    if 0 <= real_index < len(items):
        items.pop(real_index)
        notifications[user_id] = items
        save_notifications(notifications)

    return redirect("/notifications")


# === SCHEDULE PAGE WITH DELETE ===
@app.route('/schedule', methods=['GET', 'POST'])
def schedule_page():
    if "user_id" not in session: return redirect("/login")
    user_id = session["user_id"]
    schedules = load_schedules()

    if request.method == 'POST':
        date = request.form.get("date", "")
        schedules.setdefault(user_id, [])
        schedules[user_id].append({
            "date": date,
            "day": get_day_name(date),
            "subject": request.form.get("subject", "").strip(),
            "room": request.form.get("room", "").strip(),
            "time_in": request.form.get("time_in", ""),
            "time_out": request.form.get("time_out", ""),
            "alarm_date": request.form.get("alarm_date", ""),
            "alarm_time": request.form.get("alarm_time", ""),
            "comment": request.form.get("comment", "").strip()
        })
        save_schedules(schedules)
        add_notification(
            user_id,
            "Schedule Added",
            f"Your {request.form.get('subject', '').strip()} schedule was added successfully."
        )
        return redirect("/schedule")

    user_schedules = schedules.get(user_id, [])
    user_schedules.sort(key=lambda x: (x.get("date", ""), x.get("time_in", "")))

    return render_template_string(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Class Schedule — StudyMate PH</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
        body {{ min-height: 100vh; background-color: #fcf9f0; padding: 40px; }}
        .overlay {{ background: rgba(255,255,255,0.92); padding: 40px; border-radius: 16px; max-width: 850px; margin: 0 auto; }}
        h1 {{ font-size: 32px; font-weight: 800; margin-bottom: 25px; }}
        .add-form {{ background: #f9f9f9; padding: 25px; border-radius: 12px; margin-bottom: 35px; }}
        .add-form h3 {{ margin-bottom: 18px; font-size: 20px; }}
        .form-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; }}
        .full-width {{ grid-column: 1 / -1; }}
        .add-form input, .add-form textarea {{ padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; width: 100%; }}
        .add-btn {{ background: #0a3472; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: 600; margin-top: 15px; font-size: 16px; }}
        .schedule-list {{ display: flex; flex-direction: column; gap: 16px; margin-top: 20px; }}
        .schedule-item {{ display: flex; gap: 18px; align-items: flex-start; padding: 20px; border-left: 5px solid #64B5F6; border-radius: 10px; background: #f0f7ff; justify-content: space-between; }}
        .time-col {{ min-width: 160px; }}
        .day-date {{ font-weight: 700; font-size: 20px; color: #222; margin-bottom: 8px; }}
        .time {{ font-size: 16px; color: #444; }}
        .subject {{ font-size: 22px; font-weight: 700; margin-bottom: 6px; color: #111; }}
        .room {{ color: #555; font-size: 15px; margin-bottom: 8px; }}
        .comment {{ color: #666; font-size: 14px; font-style: italic; background: #e8f0fe; padding: 8px 12px; border-radius: 6px; margin-top: 6px; }}
        .no-sched {{ color: #777; font-style: italic; padding: 30px 0; text-align: center; }}
        .back-link {{ display: inline-block; margin-top: 30px; color: #0a3472; text-decoration: none; font-weight: 600; }}
        .delete-btn {{ background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }}
        .delete-btn:hover {{ background: #dc2626; }}
    </style>
</head>
<body>
    <div class="overlay">
        <a href="/dashboard" class="back-link" style="margin-top:0;margin-bottom:20px;">← Back to Dashboard</a>
        <h1>📅 Class Schedule</h1>

        <!-- Form Add Schedule -->
        <div class="add-form">
            <h3>➕ Add New Schedule</h3>
            <form method="POST">
                <div class="form-grid">
                    <input type="date" name="date" required>
                    <input type="text" name="subject" placeholder="Subject Name" required>
                    <input type="text" name="room" placeholder="Room No." required>
                    <input type="time" name="time_in" required>
                    <input type="time" name="time_out" required>
                    <label style="grid-column:1/-1;font-weight:700;color:#0a3472;">⏰ Alarm / Reminder (Optional)</label>
                    <input type="date" name="alarm_date" title="Alarm Date">
                    <input type="time" name="alarm_time" title="Alarm Time">
                    <textarea name="comment" class="full-width" rows="2" placeholder="Add Comment (Optional)"></textarea>
                </div>
                <button type="submit" class="add-btn">Save Schedule</button>
            </form>
        </div>

        <!-- Schedule List with Delete -->
        <h3>📋 Your Schedule</h3>
        <div class="schedule-list">
            {'' if user_schedules else '<p class="no-sched">No schedule yet. Add your first class above!</p>'}
            {''.join([f'''
            <div class="schedule-item">
                <div class="time-col">
                    <div class="day-date">{s.get('day', '')} — {s.get('date', '')}</div>
                    <div class="time">⏰ Time In: {s.get('time_in', '')}</div>
                    <div class="time">⏰ Time Out: {s.get('time_out', '')}</div>
                </div>
                <div>
                    <div class="subject">{s.get('subject', '')}</div>
                    <div class="room">📍 {s.get('room', '')}</div>
                    {f'<div class="comment">💬 {s.get("comment", "")}</div>' if s.get('comment') else ''}
                </div>
                <form method="POST" action="/schedule/delete/{i}">
                    <button type="submit" class="delete-btn" onclick="return confirm('Delete this schedule?')">🗑️ Delete</button>
                </form>
            </div>
            ''' for i, s in enumerate(user_schedules)])}
        </div>

    </div>
<script src="/static/alarm.js"></script>
</body>
</html>""")

# === DELETE SCHEDULE ROUTE ===
@app.route('/schedule/delete/<int:index>', methods=['POST'])
def delete_schedule(index):
    if "user_id" not in session: return redirect("/login")
    user_id = session["user_id"]
    schedules = load_schedules()
    if user_id in schedules and 0 <= index < len(schedules[user_id]):
        deleted = schedules[user_id].pop(index)
        save_schedules(schedules)
        add_notification(
            user_id,
            "Schedule Deleted",
            f"Your {deleted.get('subject', 'class')} schedule was deleted."
        )
    return redirect("/schedule")


@app.route('/api/alarms')
def api_alarms():
    if "user_id" not in session:
        return {"alarms": []}

    user_id = str(session["user_id"])
    alarms = []

    # Schedule alarms
    schedules = load_schedules().get(user_id, [])
    for s in schedules:
        if s.get("alarm_date") and s.get("alarm_time"):
            alarms.append({
                "id": "schedule-" + str(s.get("date","")) + "-" + str(s.get("subject","")) + "-" + str(s.get("alarm_date")) + "-" + str(s.get("alarm_time")),
                "date": s.get("alarm_date"),
                "time": s.get("alarm_time"),
                "title": "📅 Schedule Reminder",
                "message": f"{s.get('subject','Class')} — {s.get('room','')}".strip()
            })

    # Deadline alarms
    deadlines = load_deadlines().get(user_id, [])
    for d in deadlines:
        if d.get("completed"):
            continue
        if d.get("alarm_date") and d.get("alarm_time"):
            alarms.append({
                "id": "deadline-" + str(d.get("id")),
                "date": d.get("alarm_date"),
                "time": d.get("alarm_time"),
                "title": "⏰ Deadline Reminder",
                "message": f"{d.get('title','Deadline')} is due {d.get('due_date','')} at {d.get('due_time','')}."
            })

    # Group project alarms
    groups = load_groups()
    for g in groups.values():
        if user_id in [str(x) for x in g.get("members", [])]:
            if g.get("alarm_date") and g.get("alarm_time"):
                alarms.append({
                    "id": "group-" + str(g.get("id")),
                    "date": g.get("alarm_date"),
                    "time": g.get("alarm_time"),
                    "title": "👥 Group Project Reminder",
                    "message": f"{g.get('name','Group Project')} reminder."
                })

    return {"alarms": alarms}


# === LOGOUT ===
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)