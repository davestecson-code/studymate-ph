from flask import Flask, render_template_string, send_from_directory, request, redirect, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import os, json, uuid, secrets, smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# === GLOBAL DARK MODE ===
# This is injected into every HTML page so the Dark Mode setting works
# across Dashboard, Profile, Notifications, Schedule, Deadlines, Notes,
# Group Projects, Login, and other rendered pages.
GLOBAL_THEME_CSS = r"""
<style id="studymate-global-theme">
.global-dark-toggle{position:fixed;top:16px;right:18px;z-index:2300;border:1px solid rgba(23,75,143,.14);border-radius:12px;background:rgba(255,255,255,.92);color:#2F6F9F;padding:11px 15px;font-weight:800;cursor:pointer;box-shadow:0 5px 16px rgba(23,75,143,.12);backdrop-filter:blur(8px)}
.global-dark-toggle:hover{transform:translateY(-1px)}
body.dark{background-color:#0b1726!important;color:#eaf2fb!important;background-image:linear-gradient(rgba(7,18,31,.84),rgba(7,18,31,.84)),url('/static/bg.jpg')!important;background-size:cover;background-position:center;background-attachment:fixed}
body.dark .global-dark-toggle{background:#F2C94C!important;color:#10243b!important;border-color:#F2C94C!important}
body.dark .card,body.dark .overlay,body.dark .panel,body.dark .stat-card,body.dark .quick-panel,body.dark .notification,body.dark .container>.card{background:rgba(17,35,54,.94)!important;color:#eaf2fb!important;border-color:rgba(242,201,76,.18)!important;box-shadow:0 8px 24px rgba(0,0,0,.30)!important}
body.dark h1,body.dark h2,body.dark h3,body.dark h4,body.dark .title,body.dark .subject,body.dark .day-date,body.dark label{color:#F2C94C!important}
body.dark p,body.dark .subtitle,body.dark .meta,body.dark .date,body.dark .empty,body.dark .time,body.dark .room,body.dark .comment{color:#b9c9da!important}
body.dark input,body.dark select,body.dark textarea{background:#0f2236!important;color:#eaf2fb!important;border-color:#35516d!important}
body.dark input::placeholder,body.dark textarea::placeholder{color:#8fa5bb!important}
body.dark hr{border-color:rgba(255,255,255,.14)!important}
body.dark .notification{background:#112336!important;border-left-color:#F2C94C!important}
body.dark .back,body.dark .back-link{color:#F2C94C!important}
body.dark .add-form,body.dark .filters,body.dark .schedule-item{background:rgba(15,34,54,.92)!important;color:#eaf2fb!important;border-color:rgba(242,201,76,.18)!important}
body.dark .page-sidebar{background:linear-gradient(180deg,#081f38 0%,#0b2c4d 70%,#071b30 100%)!important}
body.dark .page-menu-backdrop{background:rgba(0,0,0,.52)!important}
body.dark .delete-notification,body.dark .danger{background:#4a2024!important;color:#ffb4b4!important}
body.dark .secondary,body.dark .gray,body.dark .btn{background:#203a54!important;color:#eaf2fb!important}
body.dark .file-row{border-color:rgba(255,255,255,.12)!important}
body.dark .file-download{color:#10243b!important}
/* SAME DARK MODE ON ALL AUTHENTICATED PAGES (Profile, Settings, Schedule, Notes, etc.) */
html.dark-mode-active,html.dark-mode-active body{color-scheme:dark!important}
html.dark-mode-active body,body.dark{background-color:#0b1726!important;color:#eaf2fb!important;background-image:linear-gradient(rgba(7,18,31,.84),rgba(7,18,31,.84)),url('/static/bg.jpg')!important;background-repeat:no-repeat!important;background-size:cover!important;background-position:center center!important;background-attachment:fixed!important}
html.dark-mode-active body::before,html.dark-mode-active body::after{background:transparent!important}
html.dark-mode-active .card,html.dark-mode-active .overlay,html.dark-mode-active .panel,html.dark-mode-active .stat-card,html.dark-mode-active .quick-panel,html.dark-mode-active .notification,html.dark-mode-active .container>.card{background:rgba(17,35,54,.94)!important;color:#eaf2fb!important;border-color:rgba(242,201,76,.18)!important}
html.dark-mode-active .card p,html.dark-mode-active .overlay p,html.dark-mode-active .panel p,html.dark-mode-active .sub,html.dark-mode-active .small{color:#b9c9da!important}
html.dark-mode-active input,html.dark-mode-active select,html.dark-mode-active textarea{background:#0f2236!important;color:#eaf2fb!important;border-color:#35516d!important}
html.dark-mode-active input::placeholder,html.dark-mode-active textarea::placeholder{color:#8fa5bb!important}
html.dark-mode-active h1,html.dark-mode-active h2,html.dark-mode-active h3,html.dark-mode-active h4,html.dark-mode-active label{color:#F2C94C!important}
html.dark-mode-active .back,html.dark-mode-active .back-link{color:#F2C94C!important}
html.dark-mode-active .success{background:#163b25!important;color:#9ee2b0!important}
html.dark-mode-active .error{background:#4a2024!important;color:#ffb4b4!important}
html.dark-mode-active .page-sidebar{background:linear-gradient(180deg,#081f38 0%,#0b2c4d 70%,#071b30 100%)!important}
html.dark-mode-active .page-menu-backdrop{background:rgba(0,0,0,.52)!important}
html.dark-mode-active .studymate-global-header{background:linear-gradient(90deg,#071d35,#123e68)!important}
html.dark-mode-active .studymate-global-header .header-menu,html.dark-mode-active .studymate-global-header .header-bell{background:rgba(255,255,255,.10)!important}
@media(max-width:700px){.global-dark-toggle{top:12px;right:12px;padding:9px 12px;font-size:13px}}
</style>
"""

GLOBAL_FIXED_HEADER_CSS = r'''
<style id="studymate-fixed-header-css">
.studymate-global-header{position:fixed;top:0;left:0;right:0;height:70px;z-index:100001;display:flex;align-items:center;justify-content:space-between;padding:0 24px 0 18px;background:#174B7A;color:#fff;box-shadow:0 3px 12px rgba(0,0,0,.16)}
.studymate-global-header .header-left{display:flex;align-items:center;gap:14px;min-width:0}
.studymate-global-header .header-menu{position:relative;z-index:100002;pointer-events:auto!important;touch-action:manipulation;-webkit-tap-highlight-color:transparent;width:46px;height:46px;border:0;border-radius:10px;background:rgba(255,255,255,.12);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:5px;flex:none}
.studymate-global-header .header-menu span{display:block;width:23px;height:3px;border-radius:4px;background:#fff}
.studymate-global-header .header-menu span:nth-child(2){background:#F2C94C}
.studymate-global-header .header-brand{font-size:24px;font-weight:800;white-space:nowrap}
.studymate-global-header .header-brand span{color:#F2C94C}
.studymate-global-header .header-right{display:flex;align-items:center;gap:16px}
.studymate-global-header .header-bell{position:relative;width:46px;height:46px;border:0;border-radius:10px;background:rgba(255,255,255,.12);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center}
.studymate-global-header .header-bell svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.studymate-global-header .header-badge{position:absolute;right:-5px;top:-5px;min-width:20px;height:20px;padding:2px 5px;border-radius:20px;background:#F2C94C;color:#174B7A;font-size:11px;font-weight:900;display:flex;align-items:center;justify-content:center;border:2px solid #174B7A}
.studymate-global-header .header-page-title{font-size:16px;font-weight:700;opacity:.94}
body.studymate-global-header-page{
    padding-top:70px!important;
    background-image:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg')!important;
    background-repeat:no-repeat!important;
    background-size:cover!important;
    background-position:center center!important;
    background-attachment:fixed!important;
}
body.studymate-global-header-page .page-menu-toggle{display:none!important;pointer-events:none!important}
body.studymate-global-header-page .page-sidebar{z-index:4500!important}
body.studymate-global-header-page .page-menu-backdrop{z-index:4000!important}
body.dark .studymate-global-header{background:linear-gradient(90deg,#071d35,#123e68)!important}
body.dark .studymate-global-header .header-menu,body.dark .studymate-global-header .header-bell{background:rgba(255,255,255,.10)!important}
.studymate-global-header,.studymate-global-header *{pointer-events:auto!important}.studymate-global-header{isolation:isolate!important}.studymate-global-header .header-menu{cursor:pointer!important;user-select:none!important;-webkit-user-select:none!important}
@media(max-width:700px){.studymate-global-header{height:64px;padding:0 12px}.studymate-global-header .header-menu,.studymate-global-header .header-bell{width:42px;height:42px}.studymate-global-header .header-brand{font-size:21px}.studymate-global-header .header-page-title{display:none}body.studymate-global-header-page{padding-top:64px!important}}
</style>
'''

GLOBAL_PAGE_MENU_CSS = r'''
<style id="studymate-global-page-menu-css">
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99998;pointer-events:none}
.page-nav-open .page-menu-backdrop{display:block;pointer-events:auto}
.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:100000;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}
.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}
.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}
.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}
body.dark .page-sidebar{background:linear-gradient(180deg,#081f38 0%,#0b2c4d 70%,#071b30 100%)!important}
body.dark .page-sidebar-nav a:hover,body.dark .page-sidebar-nav a.active{background:#F2C94C;color:#123E68}
</style>
'''

GLOBAL_PAGE_MENU_HTML = r'''
<div class="page-menu-backdrop" onclick="closePageMenu(event)" aria-hidden="true"></div>
<aside class="page-sidebar" id="pageSidebar" aria-label="StudyMate navigation">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
'''

GLOBAL_FIXED_HEADER_HTML = r'''
<header class="studymate-global-header" id="studymateGlobalHeader">
    <div class="header-left">
        <button class="header-menu" type="button" onclick="togglePageMenu(event); return false;" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
        <div class="header-brand">StudyMate <span>PH</span></div>
    </div>
    <div class="header-right">
        <button class="header-bell" type="button" onclick="window.location.href='/notifications'" aria-label="Notifications">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>__BADGE__
        </button>
        <div class="header-page-title">__TITLE__</div>
    </div>
</header>
<script id="studymate-fixed-header-js">
(function(){
    function setMenu(opened){
        var s=document.getElementById('pageSidebar');
        if(!s) return false;
        s.classList.toggle('open', !!opened);
        document.body.classList.toggle('page-nav-open', !!opened);
        var buttons=document.querySelectorAll('.studymate-global-header .header-menu, .page-menu-toggle');
        buttons.forEach(function(b){ b.setAttribute('aria-expanded', opened ? 'true' : 'false'); });
        var backdrop=document.querySelector('.page-menu-backdrop');
        if(backdrop){
            backdrop.style.display=opened ? 'block' : 'none';
            backdrop.style.pointerEvents=opened ? 'auto' : 'none';
        }
        return true;
    }
    window.togglePageMenu=function(e){
        if(e){ e.preventDefault(); e.stopPropagation(); }
        var s=document.getElementById('pageSidebar');
        if(!s) return false;
        return setMenu(!s.classList.contains('open'));
    };
    window.closePageMenu=function(e){
        if(e){ e.preventDefault(); e.stopPropagation(); }
        return setMenu(false);
    };
    window.__studyMateToggleMenu=window.togglePageMenu;
    window.openGlobalPageMenu=window.togglePageMenu;
    window.closeGlobalPageMenu=window.closePageMenu;
    // The header button already uses onclick=togglePageMenu(event).
    // Do NOT add another document-level click handler here: it would toggle
    // the menu twice (open, then immediately closed).
    document.addEventListener('DOMContentLoaded', function(){
        var b=document.querySelector('.studymate-global-header .header-menu');
        if(b){
            b.style.pointerEvents='auto';
            b.style.position='relative';
            b.style.zIndex='100000';
            b.setAttribute('aria-expanded','false');
        }
    });
})();
</script>
'''
GLOBAL_THEME_JS = r"""
<script id="studymate-global-theme-js">
(function(){
    const KEY='studymate_dark_mode';
    function applyTheme(){
        const dark=localStorage.getItem(KEY)==='1';
        document.documentElement.classList.toggle('dark-mode-active',dark);
        if(document.body) document.body.classList.toggle('dark',dark);
        document.querySelectorAll('.global-dark-toggle').forEach(function(btn){btn.textContent=dark?'☀️ Light Mode':'🌙 Dark Mode';});
        const existing=document.querySelector('.dark-mode');
        if(existing) existing.textContent=dark?'☀️ Light Mode':'🌙 Dark Mode';
    }
    window.toggleGlobalDarkMode=function(){
        localStorage.setItem(KEY,document.body.classList.contains('dark')?'0':'1');
        applyTheme();
    };
    // Apply immediately so Profile, Settings and every other page use the
    // same saved theme as Dashboard without a light-mode flash.
    applyTheme();
    window.addEventListener('DOMContentLoaded',applyTheme);
})();
</script>
"""

@app.after_request
def inject_global_theme(response):
    # Dark Mode is intentionally unavailable on the landing/Get Started page
    # and Login page. It is controlled only from the Dashboard.
    public_paths = {'/', '/login'}
    if request.path in public_paths:
        return response
    if response.content_type and response.content_type.startswith('text/html'):
        try:
            html=response.get_data(as_text=True)
            if 'id="studymate-global-theme"' not in html:
                html=html.replace('</head>', GLOBAL_THEME_CSS + '</head>', 1)
            if 'id="studymate-global-theme-js"' not in html:
                html=html.replace('</body>', GLOBAL_THEME_JS + '</body>', 1)

            # Dashboard already has its own fixed header. Every other
            # authenticated page gets the same fixed top header.
            if request.path != '/dashboard' and 'user_id' in session and 'id="studymateGlobalHeader"' not in html:
                notifications = load_notifications()
                uid = str(session.get('user_id', ''))
                unread = sum(1 for n in notifications.get(uid, []) if not n.get('read', False))
                title_map = {
                    '/schedule': 'Class Schedule',
                    '/deadlines': 'Deadlines',
                    '/group-projects': 'Group Projects',
                    '/notes': 'Notes',
                    '/notifications': 'Notifications',
                    '/profile': 'Profile',
                     '/settings': 'Settings'
                }
                header_title = next((v for k, v in title_map.items() if request.path.startswith(k)), 'Dashboard')
                badge = f'<span class="header-badge">{unread}</span>' if unread else ''
                header = GLOBAL_FIXED_HEADER_HTML.replace('__TITLE__', header_title).replace('__BADGE__', badge)
                html = html.replace('<body>', '<body class="studymate-global-header-page">', 1)
                if 'id="pageSidebar"' not in html:
                    html = html.replace('</head>', GLOBAL_PAGE_MENU_CSS + '</head>', 1)
                    html = html.replace('</body>', GLOBAL_PAGE_MENU_HTML + '</body>', 1)
                html = html.replace('</head>', GLOBAL_FIXED_HEADER_CSS + '</head>', 1)
                html = html.replace('</body>', header + '</body>', 1)
            response.set_data(html)
        except Exception:
            pass
    return response

app.secret_key = "studymate_ph_secure_key_2026"

DB_FILE = "users.json"
SCHEDULE_FILE = "schedules.json"
NOTIFICATION_FILE = "notifications.json"
DEADLINE_FILE = "deadlines.json"
GROUP_FILE = "group_projects.json"
NOTES_FILE = "notes.json"
RECOVERY_FILE = "password_resets.json"
UPLOAD_FOLDER = os.path.join("static", "group_uploads")
MAX_UPLOAD_SIZE = 100 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    "ppt", "pptx", "pps", "ppsx", "jpg", "jpeg", "png", "gif", "webp",
    "mp4", "mov", "avi", "mkv", "webm", "pdf", "doc", "docx",
    "xls", "xlsx", "txt", "zip", "rar"
}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

# Gmail recovery: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in your environment.
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip().replace(" ", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
except ValueError:
    SMTP_PORT = 465

# === Load & Save ===
def load_users():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)


def load_recovery_tokens():
    if not os.path.exists(RECOVERY_FILE):
        return {}
    with open(RECOVERY_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_recovery_tokens(tokens):
    with open(RECOVERY_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def send_recovery_email(recipient, reset_link):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False, "Gmail recovery is not configured yet. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD."
    msg = EmailMessage()
    msg["Subject"] = "StudyMate PH - Password Recovery"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient
    msg.set_content(
        "Hello,\n\n"
        "We received a request to reset your StudyMate PH password.\n\n"
        f"Open this link to create a new password: {reset_link}\n\n"
        "This link expires in 30 minutes. If you did not request this, you can ignore this email.\n\n"
        "StudyMate PH"
    )
    try:
        # Gmail works reliably with SSL on port 465. The host/port can also be
        # overridden with SMTP_HOST and SMTP_PORT when deploying elsewhere.
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True, ""
    except Exception as exc:
        print("Recovery email error:", repr(exc))
        return False, f"Unable to send the recovery email: {exc}"

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
        body { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #F5F8FC; }
        .logo-row { display: flex; align-items: center; gap: 12px; margin-bottom: 30px; }
        .logo-icon-wrap { position: relative; width: 52px; height: 52px; }
        .logo-square { background-color: #174B7A; width: 52px; height: 52px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 32px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -6px; right: -6px; font-size: 34px; color: #F2C94C; }
        .brand-text { font-size: 44px; font-weight: 700; color: #174B7A; }
        .brand-text .ph { color: #F2C94C; }
        .main-title { font-size: 52px; font-weight: 800; color: #174B7A; margin-bottom: 50px; }
        .get-started-btn { background-color: #F2C94C; color: #222; border: none; padding: 16px 65px; font-size: 20px; font-weight: 700; border-radius: 50px; cursor: pointer; }
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
        .logo-square { background-color: #174B7A; width: 48px; height: 48px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 28px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -5px; right: -5px; font-size: 30px; color: #F2C94C; }
        .brand-text { font-size: 36px; font-weight: 700; color: #174B7A; }
        .brand-text .ph { color: #F2C94C; }
        form { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 18px; margin-top: 10px; }
        input { padding: 16px 20px; font-size: 16px; border: 1px solid #ccc; border-radius: 12px; }
        .password-wrap{position:relative;width:100%;}
        .password-wrap input{width:100%;padding-right:62px;}
        .toggle-password{position:absolute;right:10px;top:50%;transform:translateY(-50%);width:34px;height:34px;border:0;background:transparent;color:#2F6F9F;cursor:pointer;padding:6px;border-radius:8px;display:flex;align-items:center;justify-content:center}.toggle-password svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.toggle-password:hover{background:transparent;opacity:.72}
        .forgot-link{display:block;text-align:right;margin-top:-7px;color:#174B7A;text-decoration:none;font-weight:700;font-size:14px;}
        .login-btn { background-color: #F2C94C; border: none; padding: 16px; font-size: 18px; font-weight: 700; border-radius: 50px; cursor: pointer; }
        .error { color: #d32f2f; margin: 10px 0; font-weight: 600; }
        .register-link { margin: 15px 0; font-size: 16px; }
        .register-link a { color: #174B7A; font-weight: 600; text-decoration: none; }
        .back-link { margin-top: 25px; color: #174B7A; text-decoration: none; }
    </style>
</head>
<body>
    <div class="right-side">
        <div class="logo-row">
            <div class="logo-icon-wrap"><div class="logo-square"><span class="logo-letter-s">S</span><span class="logo-pencil">✏️</span></div></div>
            <span class="brand-text">studymate <span class="ph">ph</span></span>
        </div>
        {% if request.args.get('reset') == 'success' %}<p style="color:#237b35;background:#e8f7e8;padding:10px;border-radius:9px;font-weight:700;">✅ Password reset successful. You can now log in.</p>{% endif %}
        <form method="POST">
            <input type="text" name="email_or_id" placeholder="Email or Student ID" required>
            <div class="password-wrap">
                <input id="loginPassword" type="password" name="password" placeholder="Password" required>
                <button type="button" class="toggle-password icon-toggle" onclick="togglePassword('loginPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button>
            </div>
            <a class="forgot-link" href="/forgot-password">Forgot password?</a>
            <button type="submit" class="login-btn">Log In</button>
        </form>
        {% if error %}<p class="error">❌ Wrong Email/ID or Password!</p>{% endif %}
        <p class="register-link">No account? <a href="/register">Register here</a></p>
        <a href="/" class="back-link">← Back to Home</a>
    </div>
<script>function eyeIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>';} function eyeOffIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-3.2 3.9M6.2 6.2C3.5 8.1 2 12 2 12s3.5 7 10 7a10.7 10.7 0 0 0 4.1-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';} function togglePassword(id,btn){const input=document.getElementById(id);if(!input||!btn)return;const show=input.type==='password';input.type=show?'text':'password';btn.innerHTML=show?eyeOffIcon():eyeIcon();btn.setAttribute('aria-label',show?'Hide password':'Show password');btn.setAttribute('title',show?'Hide password':'Show password');}</script>
<script src="/static/alarm.js"></script>

</body>
</html>'''

# === PASSWORD RECOVERY ===
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = ""
    error = ""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        users = load_users()
        target_uid = next((uid for uid, u in users.items() if u.get('email', '').strip().lower() == email), None)
        message = "If an account uses that email, a recovery link has been sent."
        if target_uid:
            token = secrets.token_urlsafe(32)
            tokens = load_recovery_tokens()
            now = datetime.now()
            cleaned = {}
            for key, value in tokens.items():
                try:
                    if datetime.fromisoformat(value.get('expires_at', '2000-01-01T00:00:00')) > now:
                        cleaned[key] = value
                except Exception:
                    pass
            tokens = cleaned
            tokens[token] = {'user_id': str(target_uid), 'expires_at': (now + timedelta(minutes=30)).isoformat()}
            save_recovery_tokens(tokens)
            reset_link = url_for('reset_password', token=token, _external=True, _scheme='https') if request.headers.get('X-Forwarded-Proto', request.scheme) == 'https' else url_for('reset_password', token=token, _external=True)
            ok, err = send_recovery_email(email, reset_link)
            if not ok:
                error = err
                message = ""
    return render_template_string(FORGOT_PASSWORD_HTML, message=message, error=error)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    tokens = load_recovery_tokens()
    item = tokens.get(token)
    if not item:
        return render_template_string(RESET_PASSWORD_HTML, invalid=True, error='This recovery link is invalid or has expired.')
    try:
        expired = datetime.fromisoformat(item.get('expires_at', '2000-01-01T00:00:00')) <= datetime.now()
    except Exception:
        expired = True
    if expired:
        tokens.pop(token, None)
        save_recovery_tokens(tokens)
        return render_template_string(RESET_PASSWORD_HTML, invalid=True, error='This recovery link is invalid or has expired.')

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not password:
            return render_template_string(RESET_PASSWORD_HTML, invalid=False, error='Please enter a new password.')
        if password != confirm:
            return render_template_string(RESET_PASSWORD_HTML, invalid=False, error='Passwords do not match.')
        users = load_users()
        user_id = str(item.get('user_id'))
        if user_id not in users:
            return render_template_string(RESET_PASSWORD_HTML, invalid=True, error='Account not found.')
        users[user_id]['password'] = password
        save_users(users)
        tokens.pop(token, None)
        save_recovery_tokens(tokens)
        return redirect('/login?reset=success')

    return render_template_string(RESET_PASSWORD_HTML, invalid=False, error='')


FORGOT_PASSWORD_HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Recover Password - StudyMate PH</title>
<style>
*{box-sizing:border-box;font-family:'Segoe UI',sans-serif} body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;background:linear-gradient(rgba(10,52,114,.55),rgba(10,52,114,.55)),url('/static/bg.jpg') center/cover fixed}.card{width:100%;max-width:520px;background:rgba(255,255,255,.97);padding:38px;border-radius:24px;box-shadow:0 12px 35px rgba(0,0,0,.2)}h1{color:#174B7A;margin:0 0 8px}.sub{color:#667085;margin:0 0 22px}.field{width:100%;padding:15px 17px;border:1px solid #ccc;border-radius:12px;font-size:16px;margin-bottom:14px}.btn{width:100%;border:0;border-radius:50px;padding:15px;background:#F2C94C;color:#222;font-weight:800;font-size:17px;cursor:pointer}.back{display:block;text-align:center;margin-top:20px;color:#174B7A;text-decoration:none;font-weight:700}.success{padding:12px;border-radius:10px;background:#e8f7e8;color:#237b35;margin-bottom:15px}.error{padding:12px;border-radius:10px;background:#ffebee;color:#c62828;margin-bottom:15px}
</style></head><body><div class="card"><h1>🔐 Recover Password</h1><p class="sub">Enter your Gmail address and we will send a secure password reset link.</p>{% if message %}<div class="success">{{ message }}</div>{% endif %}{% if error %}<div class="error">{{ error }}</div>{% endif %}<form method="POST"><input class="field" type="email" name="email" placeholder="Gmail / Email Address" required><button class="btn" type="submit">Send Recovery Link</button></form><a class="back" href="/login">← Back to Log In</a></div>
</body></html>'''

RESET_PASSWORD_HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Reset Password - StudyMate PH</title>
<style>
*{box-sizing:border-box;font-family:'Segoe UI',sans-serif} body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;background:#F5F8FC}.card{width:100%;max-width:520px;background:white;padding:38px;border-radius:24px;box-shadow:0 8px 25px rgba(0,0,0,.1)}h1{color:#174B7A;margin:0 0 20px}.field-wrap{position:relative;margin-bottom:14px}.field{width:100%;padding:15px 62px 15px 17px;border:1px solid #ccc;border-radius:12px;font-size:16px}.toggle{position:absolute;right:10px;top:50%;transform:translateY(-50%);width:34px;height:34px;border:0;background:transparent;color:#2F6F9F;cursor:pointer;padding:6px;border-radius:8px;display:flex;align-items:center;justify-content:center}.toggle svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.toggle:hover{background:transparent;opacity:.72}.btn{width:100%;border:0;border-radius:50px;padding:15px;background:#F2C94C;font-weight:800;font-size:17px;cursor:pointer}.error{padding:12px;border-radius:10px;background:#ffebee;color:#c62828;margin-bottom:15px}.back{display:block;text-align:center;margin-top:20px;color:#174B7A;text-decoration:none;font-weight:700}
</style></head><body><div class="card"><h1>🔑 Create New Password</h1>{% if error %}<div class="error">{{ error }}</div>{% endif %}{% if not invalid %}<form method="POST"><div class="field-wrap"><input id="resetPassword" class="field" type="password" name="password" placeholder="New Password" required><button type="button" class="toggle icon-toggle" onclick="togglePassword('resetPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div><div class="field-wrap"><input id="resetConfirm" class="field" type="password" name="confirm_password" placeholder="Confirm New Password" required><button type="button" class="toggle icon-toggle" onclick="togglePassword('resetConfirm',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div><button class="btn" type="submit">Reset Password</button></form>{% endif %}<a class="back" href="/login">← Back to Log In</a></div><script>function eyeIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>';} function eyeOffIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-3.2 3.9M6.2 6.2C3.5 8.1 2 12 2 12s3.5 7 10 7a10.7 10.7 0 0 0 4.1-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';} function togglePassword(id,btn){const input=document.getElementById(id);if(!input||!btn)return;const show=input.type==='password';input.type=show?'text':'password';btn.innerHTML=show?eyeOffIcon():eyeIcon();btn.setAttribute('aria-label',show?'Hide password':'Show password');btn.setAttribute('title',show?'Hide password':'Show password');}</script>
</body></html>'''


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
        .right-side { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #F5F8FC; padding: 40px; }
        .logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; }
        .logo-icon-wrap { position: relative; width: 48px; height: 48px; }
        .logo-square { background-color: #174B7A; width: 48px; height: 48px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
        .logo-letter-s { color: white; font-size: 28px; font-weight: 800; }
        .logo-pencil { position: absolute; top: -5px; right: -5px; font-size: 30px; color: #F2C94C; }
        .brand-text { font-size: 36px; font-weight: 700; color: #174B7A; }
        .brand-text .ph { color: #F2C94C; }
        h2 { color: #174B7A; margin-bottom: 20px; }
        form { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 15px; }
        input { padding: 14px 18px; font-size: 15px; border: 1px solid #ccc; border-radius: 10px; }
        .password-wrap{position:relative;width:100%;}
        .password-wrap input{width:100%;padding-right:62px;}
        .toggle-password{position:absolute;right:10px;top:50%;transform:translateY(-50%);width:34px;height:34px;border:0;background:transparent;color:#2F6F9F;cursor:pointer;padding:6px;border-radius:8px;display:flex;align-items:center;justify-content:center}.toggle-password svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.toggle-password:hover{background:transparent;opacity:.72}
        .register-btn { background-color: #F2C94C; border: none; padding: 14px; font-size: 17px; font-weight: 700; border-radius: 50px; cursor: pointer; margin-top: 10px; }
        .back-link { margin-top: 25px; color: #174B7A; text-decoration: none; }
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
            <div class="password-wrap"><input id="registerPassword" type="password" name="password" placeholder="Password" required><button type="button" class="toggle-password icon-toggle" onclick="togglePassword('registerPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>
            <div class="password-wrap"><input id="registerConfirm" type="password" name="confirm_password" placeholder="Confirm Password" required><button type="button" class="toggle-password icon-toggle" onclick="togglePassword('registerConfirm',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>
            <button type="submit" class="register-btn">Register</button>
        </form>
        <a href="/login" class="back-link">← Back to Log In</a>
    </div>
<script>function eyeIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>';} function eyeOffIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-3.2 3.9M6.2 6.2C3.5 8.1 2 12 2 12s3.5 7 10 7a10.7 10.7 0 0 0 4.1-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';} function togglePassword(id,btn){const input=document.getElementById(id);if(!input||!btn)return;const show=input.type==='password';input.type=show?'text':'password';btn.innerHTML=show?eyeOffIcon():eyeIcon();btn.setAttribute('aria-label',show?'Hide password':'Show password');btn.setAttribute('title',show?'Hide password':'Show password');}</script>
<script src="/static/alarm.js"></script>

</body>
</html>''')

# === DASHBOARD ===
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    users = load_users()
    user_id = str(session["user_id"])
    u = users.get(user_id, session.get("user", {}))
    session["user"] = u

    notifications = load_notifications()
    user_notifications = notifications.get(user_id, [])
    unread_count = sum(1 for n in user_notifications if not n.get("read", False))
    recent_notifications = list(reversed(user_notifications[-5:]))

    # Dashboard statistics
    schedules = load_schedules().get(user_id, [])
    deadlines = load_deadlines().get(user_id, [])
    groups = load_groups()

    today = datetime.now().date()
    upcoming_classes = 0
    for item in schedules:
        try:
            class_date = datetime.strptime(item.get("date", ""), "%Y-%m-%d").date()
            if class_date >= today:
                upcoming_classes += 1
        except:
            pass

    pending_deadlines = sum(
        1 for d in deadlines
        if not d.get("completed", False)
    )

    my_groups = [
        g for g in groups.values()
        if user_id in [str(x) for x in g.get("members", [])]
    ]

    completed_tasks = sum(
        1 for d in deadlines if d.get("completed", False)
    )
    for group in my_groups:
        completed_tasks += sum(
            1 for task in group.get("tasks", [])
            if task.get("completed", False)
        )

    return render_template_string(
        DASHBOARD_HTML,
        user_name=u.get("name", "Student"),
        user_id=u.get("student_id", ""),
        username=u.get("email", "").split("@")[0] if u.get("email") else "",
        unread_count=unread_count,
        recent_notifications=recent_notifications,
        upcoming_classes=upcoming_classes,
        pending_deadlines=pending_deadlines,
        group_projects=len(my_groups),
        completed_tasks=completed_tasks
    )


DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard - StudyMate PH</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}

body.dashboard-page{min-height:100vh;background-color:#eef5fb;background-image:linear-gradient(rgba(226,239,250,.74),rgba(242,247,252,.88)),url('/static/bg.jpg');background-repeat:no-repeat;background-size:cover;background-position:center center;background-attachment:fixed;color:#20354d}

/* TOP HEADER */
.top-header{
    height:70px;background:#174B7A;color:white;display:flex;
    align-items:center;justify-content:space-between;padding:0 28px 0 24px;
    position:fixed;top:0;left:0;right:0;z-index:1000;
    box-shadow:0 3px 12px rgba(0,0,0,.12)
}
.header-left{display:flex;align-items:center;gap:14px}
.menu-toggle{
    width:42px;height:42px;border:0;border-radius:10px;
    background:rgba(255,255,255,.12);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;flex:none
}
.menu-toggle span{display:block;width:21px;height:2.5px;background:#fff;border-radius:3px;transition:none}
.menu-toggle:hover{background:rgba(255,255,255,.20)}
.header-brand{font-size:24px;font-weight:800}
.header-brand span{color:#F2C94C}
.header-title{font-size:16px;font-weight:700;opacity:.92}
.header-right{display:flex;align-items:center;gap:16px}
.notification-menu{position:relative}
.bell-btn{position:relative;width:42px;height:42px;border:0;border-radius:10px;background:rgba(255,255,255,.12);color:white;cursor:pointer;display:flex;align-items:center;justify-content:center}.bell-btn svg{width:21px;height:21px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.header-badge{position:absolute;right:-5px;top:-6px;min-width:20px;height:20px;padding:2px 5px;border-radius:20px;background:#F2C94C;color:#174B7A;font-size:11px;font-weight:900;display:flex;align-items:center;justify-content:center;border:2px solid #174B7A}
.notification-dropdown{display:none;position:absolute;right:0;top:52px;width:350px;max-width:calc(100vw - 28px);background:white;color:#222;border-radius:14px;box-shadow:0 12px 35px rgba(0,0,0,.18);overflow:hidden;border:1px solid rgba(10,52,114,.12)}
.notification-dropdown.show{display:block}
.notification-dropdown-head{display:flex;align-items:center;justify-content:space-between;padding:15px 16px;border-bottom:1px solid #edf0f4;color:#174B7A}
.notification-dropdown-head a{color:#174B7A;text-decoration:none;font-size:13px;font-weight:800}
.notification-item{display:flex;flex-direction:column;gap:4px;padding:13px 16px;text-decoration:none;color:#26354a;border-bottom:1px solid #f0f2f5}
.notification-item:hover{background:#F5F8FC}
.notification-item.unread{border-left:4px solid #F2C94C;background:#fffdf3}
.notification-item strong{color:#174B7A;font-size:14px}
.notification-item span{font-size:13px;line-height:1.35;color:#5f6b7a}
.notification-item small{font-size:11px;color:#8a93a0}
.notification-empty{padding:28px 16px;text-align:center;color:#718096}

/* SIDEBAR */
.sidebar{
    position:fixed;top:70px;left:0;bottom:0;width:285px;
    background:#174B7A;color:white;padding:24px 16px 18px;z-index:900;
    display:flex;flex-direction:column;transition:transform .25s ease;transform:translateX(-100%);
    box-shadow:4px 0 18px rgba(0,0,0,.12)
}
.sidebar-brand{
    padding:0 10px 20px;border-bottom:1px solid rgba(255,255,255,.18);
    margin-bottom:16px
}
.sidebar-brand h2{font-size:29px;font-weight:800}
.sidebar-brand h2 span{color:#F2C94C}
.sidebar-brand p{font-size:13px;opacity:.78;margin-top:2px}
.nav{display:flex;flex-direction:column;gap:7px}
.nav a{
    display:flex;align-items:center;gap:14px;color:white;text-decoration:none;
    padding:14px 15px;border-radius:11px;font-size:16px;font-weight:700;transition:.2s
}
.nav a:hover,.nav a.active{background:#F2C94C;color:#123e75}
.nav-icon{width:25px;text-align:center;font-size:21px}
.sidebar-bottom{margin-top:auto;border-top:1px solid rgba(255,255,255,.18);padding-top:16px}
.profile-card{background:rgba(255,255,255,.10);border-radius:13px;padding:13px 14px;margin-bottom:10px}
.profile-link{color:white;text-decoration:none;display:flex;align-items:center;gap:11px}
.profile-avatar{
    width:39px;height:39px;border-radius:50%;background:#F2C94C;color:#174B7A;
    display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;flex:none
}
.profile-info{min-width:0}
.profile-name{font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.profile-id{font-size:12px;opacity:.78;margin-top:2px}
.user-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.user-actions a{
    text-decoration:none;display:flex;justify-content:center;align-items:center;
    gap:7px;padding:11px 8px;border-radius:9px;font-weight:800;font-size:13px
}
.profile-action{background:white;color:#174B7A}
.logout-action{background:#d32f2f;color:white}
.logout-action:hover{background:#b71c1c}

/* MAIN */
.main{margin-left:0;padding:100px 34px 35px;min-height:100vh;transition:margin-left .25s ease, padding .25s ease;background:transparent}
body.sidebar-open .sidebar{transform:translateX(0)}
body.sidebar-open .main{margin-left:285px}
.content{max-width:1180px;margin:0 auto}
.welcome-row{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:22px}
.welcome-title{font-size:34px;font-weight:800;color:#174B7A}
.welcome-sub{color:#667085;margin-top:5px}
.dark-mode{background:rgba(255,255,255,.88);border:1px solid rgba(23,75,143,.12);border-radius:12px;padding:12px 16px;color:#2F6F9F;font-weight:800;box-shadow:0 4px 14px rgba(23,75,143,.10);cursor:pointer}

/* DARK MODE */
body.dark{background:#0b1726 !important;color:#eaf2fb !important;background-image:linear-gradient(rgba(7,18,31,.82),rgba(7,18,31,.82)),url('/static/bg.jpg') !important;background-repeat:no-repeat !important;background-size:cover !important;background-position:center center !important;background-attachment:fixed !important}
body.dark .top-header{background:linear-gradient(90deg,#071d35,#123e68) !important;border-bottom-color:rgba(242,201,76,.35)}
body.dark .sidebar{background:linear-gradient(180deg,#081f38 0%,#0b2c4d 70%,#071b30 100%) !important}
body.dark .main{background:rgba(7,18,31,.28) !important}
body.dark .welcome-title,body.dark .panel-title,body.dark .quick-title,body.dark .stat-number{color:#F2C94C !important}
body.dark .welcome-sub,body.dark .stat-label,body.dark .empty{color:#b9c9da !important}
body.dark .stat-card,body.dark .panel,body.dark .quick-panel{background:rgba(17,35,54,.88) !important;border-color:rgba(242,201,76,.18) !important;box-shadow:0 8px 24px rgba(0,0,0,.28) !important}
body.dark .panel-link,body.dark .quick-btn{background:#174B7A !important;color:#fff !important}
body.dark .quick-btn.yellow{background:#F2C94C !important;color:#10243b !important}
body.dark .dark-mode{background:#F2C94C !important;color:#10243b !important;border-color:#F2C94C !important}
body.dark .notification-dropdown{background:#112336 !important;color:#eaf2fb !important;border-color:rgba(242,201,76,.2) !important}
body.dark .notification-dropdown-head,body.dark .notification-item{border-color:rgba(255,255,255,.10) !important}
body.dark .notification-item strong{color:#F2C94C !important}
body.dark .notification-item span,body.dark .notification-item small{color:#b9c9da !important}
body.dark .menu-toggle{background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%) !important}
.profile-divider{height:1px;background:linear-gradient(90deg,transparent,rgba(242,201,76,.75),rgba(255,255,255,.22),transparent);margin:16px 0 14px}


/* STATS */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin-bottom:22px}
.stat-card{background:rgba(255,255,255,.90);border-radius:16px;padding:21px 22px;border:1px solid rgba(23,75,143,.10);box-shadow:0 6px 20px rgba(23,75,143,.10);backdrop-filter:blur(6px)}
.stat-icon{font-size:24px;margin-bottom:9px}
.stat-number{font-size:30px;line-height:1;font-weight:800;color:#174B7A}
.stat-label{color:#667085;margin-top:7px;font-size:14px;font-weight:600}

/* PANELS */
.panel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px;margin-bottom:20px}
.panel{background:rgba(255,255,255,.90);border-radius:17px;padding:22px;box-shadow:0 6px 20px rgba(23,75,143,.10);backdrop-filter:blur(6px)}
.panel-head{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:14px}
.panel-title{font-size:21px;font-weight:800;color:#174B7A}
.panel-link{
    background:#174B7A;color:white;text-decoration:none;padding:9px 13px;
    border-radius:9px;font-size:13px;font-weight:800
}
.empty{color:#718096;padding:15px 0 3px}

/* QUICK ACTIONS */
.quick-panel{background:rgba(255,255,255,.92);border-radius:17px;padding:22px;box-shadow:0 6px 20px rgba(23,75,143,.10);backdrop-filter:blur(6px)}
.quick-title{color:#174B7A;font-size:21px;font-weight:800;margin-bottom:15px}
.quick-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:13px}
.quick-btn{
    display:flex;align-items:center;justify-content:center;min-height:50px;
    padding:12px;border-radius:10px;background:#174B7A;color:white;
    text-decoration:none;font-weight:800;transition:.2s
}
.quick-btn:hover{background:#08295c;transform:translateY(-1px)}
.quick-btn.yellow{background:#F2C94C;color:#222}
.quick-btn.yellow:hover{background:#DDB43A}
.badge-wrap{position:relative}
.badge{
    position:absolute;top:-8px;right:-8px;min-width:21px;height:21px;padding:2px 6px;
    border-radius:20px;background:#d32f2f;color:white;font-size:11px;
    display:flex;align-items:center;justify-content:center;border:2px solid white
}

/* MOBILE */
@media(max-width:900px){
    body{background-attachment:scroll}
    body.sidebar-open .main{margin-left:285px}
    .panel-grid{grid-template-columns:1fr}
}
@media(max-width:760px){
    body.sidebar-open .main{margin-left:0}
    .main{padding:92px 16px 25px}
    .top-header{padding:0 14px}
    .header-title{display:none}
    .welcome-row{align-items:flex-start;flex-direction:column}
    .welcome-title{font-size:29px}
    .stats{grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
    .stat-card{padding:17px}
    .quick-grid{grid-template-columns:1fr}
}
@media(max-width:480px){
    .stats{grid-template-columns:1fr}
    .welcome-title{font-size:26px}
    .content{width:100%}
}
</style>
</head>

<body class="dashboard-page">
<header class="top-header">
    <div class="header-left">
        <button class="menu-toggle" onclick="toggleSidebar()" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
        <div class="header-brand">StudyMate <span>PH</span></div>
    </div>
    <div class="header-right">
        <div class="notification-menu">
            <button class="bell-btn" type="button" onclick="toggleNotificationMenu()" aria-label="Notifications"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>{% if unread_count > 0 %}<span class="header-badge">{{ unread_count }}</span>{% endif %}</button>
            <div class="notification-dropdown" id="notificationDropdown">
                <div class="notification-dropdown-head"><strong>Notifications</strong><a href="/notifications">View All</a></div>
                {% if recent_notifications %}
                    {% for n in recent_notifications %}
                    <a class="notification-item {% if not n.get('read',False) %}unread{% endif %}" href="/notifications">
                        <strong>{{ n.get('title','Notification') }}</strong>
                        <span>{{ n.get('message','') }}</span>
                        <small>{{ n.get('date','') }}</small>
                    </a>
                    {% endfor %}
                {% else %}
                    <div class="notification-empty">🔕 No notifications yet.</div>
                {% endif %}
            </div>
        </div>
        <div class="header-title">Dashboard</div>
    </div>
</header>

<aside class="sidebar" id="sidebar">
    <div class="sidebar-brand">
        <h2>StudyMate <span>PH</span></h2>
        <p>Student Hub</p>
    </div>

    <nav class="nav">
        <a href="/dashboard" class="active"><span class="nav-icon">🏠</span><span>Dashboard</span></a>
        <a href="/schedule"><span class="nav-icon">📅</span><span>Class Schedule</span></a>
        <a href="/deadlines"><span class="nav-icon">📝</span><span>Deadlines</span></a>
        <a href="/group-projects"><span class="nav-icon">👥</span><span>Group Projects</span></a>
        <a href="/profile"><span class="nav-icon">⚙️</span><span>Settings</span></a>
        <a href="/notes"><span class="nav-icon">📚</span><span>Notes</span></a>
        <a href="/notifications" class="badge-wrap">
            <span class="nav-icon">🔔</span><span>Notifications</span>
            {% if unread_count > 0 %}<span class="badge">{{ unread_count }}</span>{% endif %}
        </a>
    </nav>

    <div class="sidebar-bottom">
        <div class="profile-divider"></div>
        <div class="profile-card">
            <a href="/profile" class="profile-link">
                <div class="profile-avatar">👤</div>
                <div class="profile-info">
                    <div class="profile-name">{{ user_name }}</div>
                    <div class="profile-id">ID: {{ user_id }}</div>
                </div>
            </a>
        </div>

        <div class="user-actions">
            <a href="/profile" class="profile-action">👤 Profile</a>
            <a href="/logout" class="logout-action">↪ Logout</a>
        </div>
    </div>
</aside>

<main class="main">
<div class="content">

    <div class="welcome-row">
        <div>
            <h1 class="welcome-title">Welcome, {{ user_name }}! 👋</h1>
            <p class="welcome-sub">Keep going! You're doing great!</p>
        </div>
        <button class="dark-mode" onclick="toggleDarkMode()">🌙 Dark Mode</button>
    </div>

    <section class="stats">
        <div class="stat-card">
            <div class="stat-icon">📅</div>
            <div class="stat-number">{{ upcoming_classes }}</div>
            <div class="stat-label">Upcoming Classes</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-number">{{ pending_deadlines }}</div>
            <div class="stat-label">Pending Deadlines</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-number">{{ group_projects }}</div>
            <div class="stat-label">Group Projects</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-number">{{ completed_tasks }}</div>
            <div class="stat-label">Completed Tasks</div>
        </div>
    </section>

    <section class="panel-grid">
        <div class="panel">
            <div class="panel-head">
                <h2 class="panel-title">📝 Upcoming Deadlines</h2>
                <a href="/deadlines" class="panel-link">View All</a>
            </div>
            {% if pending_deadlines > 0 %}
            <p class="empty">You have {{ pending_deadlines }} pending deadline{{ 's' if pending_deadlines != 1 else '' }}. Check Deadlines to view the details.</p>
            {% else %}
            <p class="empty">No pending deadlines. You're all caught up! 🎉</p>
            {% endif %}
        </div>

        <div class="panel">
            <div class="panel-head">
                <h2 class="panel-title">👥 My Group Projects</h2>
                <a href="/group-projects" class="panel-link">Open</a>
            </div>
            {% if group_projects > 0 %}
            <p class="empty">You are currently part of {{ group_projects }} group project{{ 's' if group_projects != 1 else '' }}.</p>
            {% else %}
            <p class="empty">No group projects yet.</p>
            {% endif %}
        </div>
    </section>

    <section class="quick-panel">
        <h2 class="quick-title">⚡ Quick Actions</h2>
        <div class="quick-grid">
            <a href="/schedule" class="quick-btn">📅 Class Schedule</a>
            <a href="/deadlines" class="quick-btn">+ Add Deadline</a>
            <a href="/group-projects" class="quick-btn">+ Group Project</a>
            <a href="/notes" class="quick-btn yellow">📝 Notes</a>
            <a href="/notifications" class="quick-btn">🔔 Notifications{% if unread_count > 0 %} ({{ unread_count }}){% endif %}</a>
            <a href="/profile" class="quick-btn">⚙️ Settings</a>
        </div>
    </section>

</div>
</main>

<script>
function toggleNotificationMenu(){
    const dropdown=document.getElementById('notificationDropdown');
    if(dropdown) dropdown.classList.toggle('show');
}
document.addEventListener('click',function(e){
    const menu=document.querySelector('.notification-menu');
    const dropdown=document.getElementById('notificationDropdown');
    if(menu && dropdown && !menu.contains(e.target)) dropdown.classList.remove('show');
});

function toggleSidebar(){
    document.body.classList.toggle('sidebar-open');
    const btn = document.querySelector('.menu-toggle');
    const opened = document.body.classList.contains('sidebar-open');
    if(btn){
        btn.setAttribute('aria-expanded', opened ? 'true' : 'false');
        btn.setAttribute('aria-label', opened ? 'Close menu' : 'Open menu');
    }
}

function toggleDarkMode(){
    const dark = document.body.classList.toggle('dark');
    localStorage.setItem('studymate_dark_mode', dark ? '1' : '0');
    const btn = document.querySelector('.dark-mode');
    if(btn) btn.textContent = dark ? '☀️ Light Mode' : '🌙 Dark Mode';
}
(function(){
    const dark = localStorage.getItem('studymate_dark_mode') === '1';
    if(dark) document.body.classList.add('dark');
    const btn = document.querySelector('.dark-mode');
    if(btn) btn.textContent = dark ? '☀️ Light Mode' : '🌙 Dark Mode';
})();

document.querySelectorAll('.sidebar a').forEach(function(link){
    link.addEventListener('click', function(){
        if(window.innerWidth <= 760){
            document.body.classList.remove('sidebar-open');
        }
    });
});
</script>

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
body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center/cover fixed;color:#20354d}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.back{color:#174B7A;text-decoration:none;font-weight:600}
h1{margin:0 0 5px;font-size:32px}.subtitle{color:#718096;margin:0}
.add-btn,.primary{background:#2F6F9F;color:white;border:0;border-radius:10px;padding:12px 18px;cursor:pointer;font-weight:700}
.card{background:rgba(255,255,255,.91);border-radius:16px;padding:20px;margin-bottom:18px;box-shadow:0 6px 20px rgba(23,75,143,.10);backdrop-filter:blur(6px)}
.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
input,select,textarea{width:100%;padding:11px 12px;border:1px solid #d9e0ea;border-radius:9px;font:inherit}
textarea{min-height:85px;resize:vertical}.full{grid-column:1/-1}
.form-actions,.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.secondary,.btn{border:0;border-radius:8px;padding:9px 12px;cursor:pointer;font-weight:600}
.secondary{background:#EAF3FA;color:#294765}
.filters{display:grid;grid-template-columns:1.5fr 1fr 1fr auto;gap:10px}
.deadline{border-left:6px solid #5A8DB5;padding:17px 18px}
.deadline.overdue{border-left-color:#d9534f}.deadline.soon{border-left-color:#e69a27}
.deadline.completed{border-left-color:#45a66b;opacity:.82}
.deadline-head{display:flex;justify-content:space-between;gap:15px}
.subject{font-size:14px;color:#718096;font-weight:700;text-transform:uppercase}
.title{font-size:21px;font-weight:800;margin:4px 0}.meta{color:#667085;margin:7px 0}
.badge{display:inline-block;padding:5px 9px;border-radius:20px;background:#edf2f7;font-size:12px;font-weight:700}
.status-overdue{background:#fde7e7;color:#b42318}.status-soon{background:#fff0d7;color:#9a6700}
.status-completed{background:#e6f7ec;color:#147a3e}.status-upcoming{background:#e4effa;color:#245d9c}
.done{background:#e7f7ed;color:#18713c}.edit{background:#eaf1fb;color:#285c96}.delete{background:#fde8e8;color:#b42318}
.empty{text-align:center;padding:40px 15px;color:#718096}
@media(max-width:750px){.top{align-items:flex-start;gap:15px;flex-direction:column}.form-grid,.filters{grid-template-columns:1fr}.full{grid-column:auto}}

/* SHARED THREE-LINE MENU */
.page-menu-toggle{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.page-menu-toggle span{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}.page-menu-toggle span:nth-child(2){background:#F2C94C}.page-menu-toggle:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}.page-sidebar .menu-close-note{font-size:11px;opacity:.68;margin-top:12px}.page-nav-open .page-menu-backdrop{display:block}@media(max-width:700px){.page-menu-toggle{top:10px;left:10px;width:42px;height:42px}.page-sidebar{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')})})();
function togglePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}
function closePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePageMenu()});
</script>

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
<label style="grid-column:1/-1;font-weight:700;color:#174B7A;">⏰ Alarm / Reminder (Optional)</label>
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
button{padding:11px 18px;border:0;border-radius:9px;background:#174B7A;color:white;font-weight:700;cursor:pointer}
a{color:#174B7A;text-decoration:none}
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
body{margin:0;background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center/cover fixed;color:#20354d;padding:30px}
.container{max-width:1100px;margin:auto}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.back{color:#174B7A;text-decoration:none;font-weight:700}
h1{color:#174B7A;margin:8px 0}.sub{color:#718096}
.grid{display:grid;grid-template-columns:330px 1fr;gap:20px}
.card{background:white;border-radius:18px;padding:22px;box-shadow:0 4px 18px rgba(0,0,0,.07);margin-bottom:18px}
input,select,textarea{width:100%;padding:11px;border:1px solid #d6dce5;border-radius:9px;margin:7px 0;font-size:15px}
textarea{min-height:150px;resize:vertical}
button,.btn{border:0;border-radius:9px;padding:10px 14px;cursor:pointer;font-weight:700;text-decoration:none;display:inline-block}
.primary{background:#174B7A;color:white}.yellow{background:#F2C94C;color:#222}.danger{background:#fde8e8;color:#b42318}.gray{background:#eef2f7;color:#344054}
.note{border-left:5px solid #2F6F9F}.note.pinned{border-left-color:#F2C94C}
.note h2{margin:0 0 5px;color:#174B7A}.meta{color:#718096;font-size:13px;margin:5px 0}
.content{white-space:pre-wrap;line-height:1.55;margin:14px 0}
.actions{display:flex;gap:7px;flex-wrap:wrap}
.empty{text-align:center;color:#718096;padding:35px}
@media(max-width:800px){.grid{grid-template-columns:1fr}body{padding:15px}}

/* SHARED THREE-LINE MENU */
.page-menu-toggle{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.page-menu-toggle span{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}.page-menu-toggle span:nth-child(2){background:#F2C94C}.page-menu-toggle:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}.page-sidebar .menu-close-note{font-size:11px;opacity:.68;margin-top:12px}.page-nav-open .page-menu-backdrop{display:block}@media(max-width:700px){.page-menu-toggle{top:10px;left:10px;width:42px;height:42px}.page-sidebar{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')})})();
function togglePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}
function closePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePageMenu()});
</script>

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
body{margin:0;background:linear-gradient(rgba(226,239,250,.78),rgba(242,247,252,.90)),url('/static/bg.jpg') center/cover fixed;padding:30px}
.card{max-width:700px;margin:30px auto;background:white;padding:30px;border-radius:18px;box-shadow:0 4px 18px rgba(0,0,0,.08)}
input,select,textarea{width:100%;padding:12px;border:1px solid #d6dce5;border-radius:9px;margin:7px 0 15px;font-size:15px}
textarea{min-height:220px}
button{padding:12px 18px;border:0;border-radius:25px;background:#F2C94C;font-weight:800;cursor:pointer}
a{color:#174B7A;font-weight:700;text-decoration:none;margin-left:12px}
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
body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center/cover fixed;color:#20354d}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.back{color:#174B7A;text-decoration:none;font-weight:600}
h1{margin:10px 0 5px;font-size:32px}.subtitle{color:#718096;margin:0 0 22px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:rgba(255,255,255,.91);border-radius:16px;padding:22px;box-shadow:0 6px 20px rgba(23,75,143,.10);margin-bottom:18px;backdrop-filter:blur(6px)}
.card h2{margin-top:0;color:#174B7A}
input,select,textarea{width:100%;padding:11px 12px;border:1px solid #d9e0ea;border-radius:9px;font:inherit;margin-bottom:10px}
textarea{min-height:85px;resize:vertical}
button,.btn{border:0;border-radius:9px;padding:10px 15px;cursor:pointer;font-weight:700;text-decoration:none;display:inline-block}
.primary{background:#2F6F9F;color:white}.join{background:#F2C94C;color:#20354d}
.project{border-left:6px solid #2F6F9F}
.project h3{margin:0 0 5px;font-size:21px}
.meta{color:#667085;margin:6px 0}
.code{font-weight:800;letter-spacing:2px;background:#EDF5FB;padding:5px 9px;border-radius:7px}
.progress{height:10px;background:#EAF1F7;border-radius:10px;overflow:hidden;margin:10px 0}
.progress-bar{height:100%;background:#2F6F9F}
.empty{text-align:center;color:#718096;padding:30px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}

/* SHARED THREE-LINE MENU */
.page-menu-toggle{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.page-menu-toggle span{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}.page-menu-toggle span:nth-child(2){background:#F2C94C}.page-menu-toggle:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}.page-sidebar .menu-close-note{font-size:11px;opacity:.68;margin-top:12px}.page-nav-open .page-menu-backdrop{display:block}@media(max-width:700px){.page-menu-toggle{top:10px;left:10px;width:42px;height:42px}.page-sidebar{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')})})();
function togglePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}
function closePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePageMenu()});
</script>

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
<label style="font-weight:700;color:#174B7A;">⏰ Alarm / Reminder (Optional)</label>
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
        "files": [],
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
body{margin:0;font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center/cover fixed;color:#20354d}
.container{max-width:1100px;margin:30px auto;padding:0 20px}
.back{color:#174B7A;text-decoration:none;font-weight:600}
.hero{background:linear-gradient(135deg,#174B7A,#2F6F9F);color:white;padding:25px;border-radius:18px;margin:15px 0 20px}
.hero h1{margin:0 0 7px}.hero p{margin:5px 0}
.code{background:white;color:#174B7A;padding:5px 10px;border-radius:7px;font-weight:800;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:rgba(255,255,255,.91);border-radius:16px;padding:20px;box-shadow:0 6px 20px rgba(23,75,143,.10);margin-bottom:18px;backdrop-filter:blur(6px)}
.card h2{margin-top:0;color:#174B7A}
input,select,textarea{width:100%;padding:10px;border:1px solid #d9e0ea;border-radius:8px;font:inherit;margin-bottom:9px}
textarea{min-height:80px}
button{border:0;border-radius:8px;padding:9px 13px;background:#174B7A;color:white;font-weight:700;cursor:pointer}
.task{padding:12px;border:1px solid #e2e8f0;border-radius:10px;margin:8px 0}
.task.done{background:#eef9f1;text-decoration:line-through;opacity:.8}
.small{font-size:13px;color:#718096}
.progress{height:12px;background:#EAF1F7;border-radius:10px;overflow:hidden}
.bar{height:100%;background:#2F6F9F}
.note,.meeting{padding:10px;border-bottom:1px solid #e5e7eb}
.member{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #edf0f4}
.danger{background:#fde8e8;color:#b42318}
.upload-form{display:flex;gap:9px;align-items:center;flex-wrap:wrap}
.upload-form input[type=file]{flex:1;min-width:220px;margin-bottom:0}
.file-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #e5e7eb}
.file-actions{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.file-download{display:inline-block;padding:9px 12px;border-radius:8px;background:#F2C94C;color:#222;text-decoration:none;font-weight:800}
@media(max-width:800px){.grid{grid-template-columns:1fr}.file-row{align-items:flex-start;flex-direction:column}.file-actions{width:100%}}

/* SHARED THREE-LINE MENU */
.page-menu-toggle{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.page-menu-toggle span{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}.page-menu-toggle span:nth-child(2){background:#F2C94C}.page-menu-toggle:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}.page-sidebar .menu-close-note{font-size:11px;opacity:.68;margin-top:12px}.page-nav-open .page-menu-backdrop{display:block}@media(max-width:700px){.page-menu-toggle{top:10px;left:10px;width:42px;height:42px}.page-sidebar{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')})})();
function togglePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}
function closePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePageMenu()});
</script>

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
<h2>📎 Group Files</h2>
<p class="small">Send PowerPoint, pictures, videos, PDFs, documents, spreadsheets, ZIP/RAR and other supported files (up to 100 MB each).</p>
<form method="POST" action="/group-projects/{{ group.id }}/files/upload" enctype="multipart/form-data" class="upload-form">
<input type="file" name="file" accept=".ppt,.pptx,.pps,.ppsx,.jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.mkv,.webm,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar" required>
<button type="submit">📤 Send File</button>
</form>
{% for f in group_files %}
<div class="file-row">
<div><b>📄 {{ f.original_name }}</b><div class="small">Uploaded by {{ f.uploader_name }} · {{ f.date }} · {{ (f.size / 1024 / 1024)|round(2) }} MB</div></div>
<div class="file-actions"><a class="file-download" href="/group-projects/{{ group.id }}/files/{{ f.id }}/download">⬇ Download</a>{% if user_id == f.uploader_id or user_id == group.leader_id %}<form method="POST" action="/group-projects/{{ group.id }}/files/{{ f.id }}/delete" onsubmit="return confirm('Delete this file?');"><button class="danger" type="submit">🗑 Delete</button></form>{% endif %}</div>
</div>
{% else %}
<div class="empty">No files shared yet.</div>
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
<p style="font-size:24px;font-weight:800;letter-spacing:4px;color:#174B7A">{{ group.code }}</p>
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
    ], progress=progress, user_id=user_id, group_files=group.get('files', []))


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


@app.route('/group-projects/<group_id>/files/upload', methods=['POST'])
def upload_group_file(group_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result
    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        return "No file selected.", 400

    original_name = secure_filename(uploaded.filename)
    if not original_name or '.' not in original_name:
        return "Invalid file.", 400
    extension = original_name.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return "File type is not allowed.", 400

    group_dir = os.path.join(UPLOAD_FOLDER, str(group_id))
    os.makedirs(group_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    saved_path = os.path.join(group_dir, stored_name)
    uploaded.save(saved_path)
    size = os.path.getsize(saved_path)
    if size > MAX_UPLOAD_SIZE:
        os.remove(saved_path)
        return "File is too large. Maximum size is 100 MB.", 413

    group.setdefault('files', []).append({
        'id': str(uuid.uuid4())[:8],
        'original_name': original_name,
        'stored_name': stored_name,
        'size': size,
        'uploader_id': user_id,
        'uploader_name': get_user_name(user_id),
        'date': datetime.now().strftime('%B %d, %Y %I:%M %p')
    })
    save_groups(groups)
    notify_group_members(group, 'New Group File', f"{get_user_name(user_id)} uploaded '{original_name}' to '{group.get('name','Group Project')}'.", exclude_user_id=user_id)
    return redirect(url_for('group_project_detail', group_id=group_id))


@app.route('/group-projects/<group_id>/files/<file_id>/download')
def download_group_file(group_id, file_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result
    target = next((f for f in group.get('files', []) if str(f.get('id')) == str(file_id)), None)
    if not target:
        return "File not found.", 404
    return send_from_directory(
        os.path.join(UPLOAD_FOLDER, str(group_id)),
        target.get('stored_name'),
        as_attachment=True,
        download_name=target.get('original_name', target.get('stored_name'))
    )


@app.route('/group-projects/<group_id>/files/<file_id>/delete', methods=['POST'])
def delete_group_file(group_id, file_id):
    result, error = require_group_member(group_id)
    if error:
        return error
    groups, group, user_id = result
    target = next((f for f in group.get('files', []) if str(f.get('id')) == str(file_id)), None)
    if not target:
        return "File not found.", 404
    if str(target.get('uploader_id')) != user_id and str(group.get('leader_id')) != user_id:
        return "Only the uploader or group leader can delete this file.", 403

    path = os.path.join(UPLOAD_FOLDER, str(group_id), target.get('stored_name', ''))
    if os.path.exists(path):
        os.remove(path)
    group['files'] = [f for f in group.get('files', []) if str(f.get('id')) != str(file_id)]
    save_groups(groups)
    notify_group_members(group, 'Group File Deleted', f"{target.get('original_name','A file')} was removed from '{group.get('name','Group Project')}'.", exclude_user_id=user_id)
    return redirect(url_for('group_project_detail', group_id=group_id))


@app.route('/settings')
def settings_page():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/profile")


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
body { margin:0; background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center center/cover no-repeat fixed; padding:105px 35px 35px; color:#20354d; }
.profile-top { max-width:650px; margin:0 auto 16px; display:flex; align-items:center; justify-content:space-between; min-height:42px; }
.profile-top .back { margin:0; }
.card { max-width:650px; margin:auto; background:white; padding:35px; border-radius:18px; box-shadow:0 4px 20px rgba(0,0,0,.08); }
h1 { color:#174B7A; }
form { display:flex; flex-direction:column; gap:12px; }
label { font-weight:700; }
input { padding:13px; border:1px solid #ccc; border-radius:10px; font-size:15px; }
body { margin:0; background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center center/cover no-repeat fixed; padding:35px; color:#20354d; }
.card { background:rgba(255,255,255,.91); box-shadow:0 6px 20px rgba(23,75,143,.10); backdrop-filter:blur(6px); }
.password-wrap{position:relative}.password-wrap input{width:100%;padding-right:62px}.toggle-password{position:absolute;right:10px;top:50%;transform:translateY(-50%);width:34px;height:34px;border:0;background:transparent;color:#2F6F9F;cursor:pointer;padding:6px;border-radius:8px;display:flex;align-items:center;justify-content:center}.toggle-password svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.toggle-password:hover{background:transparent;opacity:.72}
.save { margin-top:10px; padding:14px; border:0; border-radius:30px; background:#F2C94C; font-weight:800; cursor:pointer; }
.success { padding:12px; background:#e8f7e8; color:#237b35; border-radius:8px; margin-bottom:15px; }
.error { padding:12px; background:#ffebee; color:#c62828; border-radius:8px; margin-bottom:15px; }
.back { display:inline-block; margin-top:20px; color:#174B7A; font-weight:700; text-decoration:none; }

body{background-repeat:no-repeat!important;background-size:cover!important;background-position:center center!important;background-attachment:fixed!important;}

body.dark .profile-top .back{color:#F2C94C!important}
body.dark .card{background:rgba(17,35,54,.94)!important;color:#eaf2fb!important;border-color:rgba(242,201,76,.18)!important}
body.dark h1,body.dark h3,body.dark label{color:#F2C94C!important}
body.dark input{background:#0f2236!important;color:#eaf2fb!important;border-color:#35516d!important}
</style>
</head>
<body>
<div class="profile-top">
<a class="back" href="/dashboard">← Back to Dashboard</a>
</div>
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
<div class="password-wrap"><input id="oldPassword" type="password" name="old_password"><button type="button" class="toggle-password" onclick="togglePassword('oldPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>

<label>New Password</label>
<div class="password-wrap"><input id="newPassword" type="password" name="new_password"><button type="button" class="toggle-password" onclick="togglePassword('newPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>

<label>Confirm New Password</label>
<div class="password-wrap"><input id="confirmPassword" type="password" name="confirm_password"><button type="button" class="toggle-password" onclick="togglePassword('confirmPassword',this)" aria-label="Show password" title="Show password"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg></button></div>

<button class="save" type="submit">💾 Save Changes</button>
</form>

</div>
<script>function eyeIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>';} function eyeOffIcon(){return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18 18 0 0 1-3.2 3.9M6.2 6.2C3.5 8.1 2 12 2 12s3.5 7 10 7a10.7 10.7 0 0 0 4.1-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';} function togglePassword(id,btn){const input=document.getElementById(id);if(!input||!btn)return;const show=input.type==='password';input.type=show?'text':'password';btn.innerHTML=show?eyeOffIcon():eyeIcon();btn.setAttribute('aria-label',show?'Hide password':'Show password');btn.setAttribute('title',show?'Hide password':'Show password');}</script>
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
body { margin:0; background:linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)),url('/static/bg.jpg') center/cover fixed; padding:35px; color:#20354d; }
.card { max-width:800px; margin:auto; background:white; padding:35px; border-radius:18px; box-shadow:0 4px 20px rgba(0,0,0,.08); }
h1 { color:#174B7A; }
.notification { padding:18px; margin:12px 0; background:#f7f9fc; border-left:5px solid #174B7A; border-radius:10px; }
.date { font-size:12px; color:#888; margin-top:8px; }
.empty { text-align:center; color:#777; padding:40px; }
.delete-notification { border:0; background:#fde8e8; color:#b42318; padding:8px 12px; border-radius:8px; cursor:pointer; font-weight:700; }
.back { display:inline-block; margin-top:20px; color:#174B7A; font-weight:700; text-decoration:none; }

/* SHARED THREE-LINE MENU */
.page-menu-toggle{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}
.page-menu-toggle span{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}.page-menu-toggle span:nth-child(2){background:#F2C94C}.page-menu-toggle:hover{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}
.page-menu-backdrop{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}.page-sidebar{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto;pointer-events:auto}.page-sidebar.open{transform:translateX(0)}
.page-sidebar-brand{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}.page-sidebar-brand h2{margin:0;font-size:27px;font-weight:800}.page-sidebar-brand h2 span{color:#F2C94C}.page-sidebar-brand p{margin:3px 0 0;font-size:12px;opacity:.78}.page-sidebar-nav{display:flex;flex-direction:column;gap:7px}.page-sidebar-nav a{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}.page-sidebar-nav .icon{width:24px;text-align:center;font-size:19px}.page-sidebar-bottom{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}.page-sidebar-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}.page-sidebar-actions a{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}.page-sidebar-actions a:last-child{background:#F2C94C;color:#20354d}.page-sidebar .menu-close-note{font-size:11px;opacity:.68;margin-top:12px}.page-nav-open .page-menu-backdrop{display:block}@media(max-width:700px){.page-menu-toggle{top:10px;left:10px;width:42px;height:42px}.page-sidebar{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')})})();
function togglePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}
function closePageMenu(){const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closePageMenu()});
</script>

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
        body {{ min-height: 100vh; background: linear-gradient(rgba(228,239,249,.80),rgba(239,246,252,.90)), url('/static/bg.jpg') center/cover fixed; padding: 40px; }}
        .overlay {{ background: rgba(255,255,255,0.88); padding: 40px; border-radius: 18px; max-width: 1000px; margin: 0 auto; box-shadow: 0 8px 28px rgba(23,75,143,.12); backdrop-filter: blur(6px); }}
        h1 {{ font-size: 32px; font-weight: 800; margin-bottom: 25px; }}
        .add-form {{ background: rgba(234,243,250,.82); padding: 25px; border-radius: 12px; margin-bottom: 35px; }}
        .add-form h3 {{ margin-bottom: 18px; font-size: 20px; }}
        .form-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; }}
        .time-field {{ display:flex; flex-direction:column; gap:6px; }}
        .time-field label {{ font-weight:700; color:#174B7A; font-size:14px; }}
        .full-width {{ grid-column: 1 / -1; }}
        .add-form input, .add-form textarea {{ padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; width: 100%; }}
        .add-btn {{ background: #2F6F9F; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: 600; margin-top: 15px; font-size: 16px; }}
        .schedule-list {{ display: flex; flex-direction: column; gap: 16px; margin-top: 20px; }}
        .schedule-item {{ display: flex; gap: 18px; align-items: flex-start; padding: 20px; border-left: 5px solid #5A8DB5; border-radius: 12px; background: rgba(245,249,253,.88); justify-content: space-between; box-shadow: 0 3px 12px rgba(23,75,143,.06); }}
        .time-col {{ min-width: 160px; }}
        .day-date {{ font-weight: 700; font-size: 20px; color: #222; margin-bottom: 8px; }}
        .time {{ font-size: 16px; color: #444; }}
        .subject {{ font-size: 22px; font-weight: 700; margin-bottom: 6px; color: #111; }}
        .room {{ color: #555; font-size: 15px; margin-bottom: 8px; }}
        .comment {{ color: #4f6680; font-size: 14px; font-style: italic; background: #EAF3FA; padding: 8px 12px; border-radius: 6px; margin-top: 6px; }}
        .no-sched {{ color: #777; font-style: italic; padding: 30px 0; text-align: center; }}
        .back-link {{ display: inline-block; margin-top: 30px; color: #174B7A; text-decoration: none; font-weight: 600; }}
        .delete-btn {{ background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }}
        .delete-btn:hover {{ background: #dc2626; }}
    
/* SHARED THREE-LINE MENU */
.page-menu-toggle{{position:fixed;top:14px;left:18px;z-index:2200;width:46px;height:46px;border:1px solid rgba(255,255,255,.28);border-radius:12px;background:linear-gradient(135deg,#174B7A 0%,#174B7A 58%,#F2C94C 58%,#F2C94C 100%);box-shadow:0 6px 18px rgba(23,75,122,.28);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}}
.page-menu-toggle span{{display:block;width:22px;height:3px;border-radius:4px;background:#fff;transition:.2s}}.page-menu-toggle span:nth-child(2){{background:#F2C94C}}.page-menu-toggle:hover{{transform:translateY(-1px);box-shadow:0 8px 22px rgba(23,75,122,.34)}}
.page-menu-backdrop{{display:none;position:fixed;inset:0;background:rgba(9,31,55,.28);backdrop-filter:blur(2px);z-index:99980}}.page-sidebar{{position:fixed;top:0;left:0;bottom:0;width:285px;padding:84px 16px 18px;background:linear-gradient(180deg,#174B7A 0%,#123E68 72%,#0F355A 100%);color:#fff;z-index:2100;transform:translateX(-105%);transition:transform .24s ease;box-shadow:8px 0 26px rgba(0,0,0,.18);overflow:auto}}.page-sidebar.open{{transform:translateX(0)}}
.page-sidebar-brand{{padding:0 10px 18px;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:14px}}.page-sidebar-brand h2{{margin:0;font-size:27px;font-weight:800}}.page-sidebar-brand h2 span{{color:#F2C94C}}.page-sidebar-brand p{{margin:3px 0 0;font-size:12px;opacity:.78}}.page-sidebar-nav{{display:flex;flex-direction:column;gap:7px}}.page-sidebar-nav a{{display:flex;align-items:center;gap:12px;padding:13px 14px;border-radius:11px;color:#fff;text-decoration:none;font-weight:700;transition:.18s}}.page-sidebar-nav a:hover,.page-sidebar-nav a.active{{background:linear-gradient(90deg,#F2C94C,#f7d56d);color:#123E68}}.page-sidebar-nav .icon{{width:24px;text-align:center;font-size:19px}}.page-sidebar-bottom{{margin-top:22px;border-top:1px solid rgba(255,255,255,.16);padding:15px 10px 0;font-size:13px}}.page-sidebar-actions{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}}.page-sidebar-actions a{{padding:10px 6px;text-align:center;border-radius:9px;text-decoration:none;font-weight:800;background:#fff;color:#174B7A}}.page-sidebar-actions a:last-child{{background:#F2C94C;color:#20354d}}.page-sidebar .menu-close-note{{font-size:11px;opacity:.68;margin-top:12px}}.page-nav-open .page-menu-backdrop{{display:block}}@media(max-width:700px){{.page-menu-toggle{{top:10px;left:10px;width:42px;height:42px}}.page-sidebar{{width:min(285px,86vw)}}
</style>
</head>
<body>

<button class="page-menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" onclick="togglePageMenu()"><span></span><span></span><span></span></button>
<div class="page-menu-backdrop" onclick="closePageMenu()"></div>
<aside class="page-sidebar" id="pageSidebar">
<div class="page-sidebar-brand"><h2>StudyMate <span>PH</span></h2><p>Student Hub</p></div>
<nav class="page-sidebar-nav">
<a data-page="dashboard" href="/dashboard"><span class="icon">🏠</span>Dashboard</a>
<a data-page="schedule" href="/schedule"><span class="icon">📅</span>Class Schedule</a>
<a data-page="deadlines" href="/deadlines"><span class="icon">📝</span>Deadlines</a>
<a data-page="group-projects" href="/group-projects"><span class="icon">👥</span>Group Projects</a>
<a data-page="notes" href="/notes"><span class="icon">📚</span>Notes</a>
<a data-page="notifications" href="/notifications"><span class="icon">🔔</span>Notifications</a>
<a data-page="settings" href="/settings"><span class="icon">⚙️</span>Settings</a>
</nav>
<div class="page-sidebar-bottom">StudyMate PH Student Hub<div class="page-sidebar-actions"><a href="/profile">👤 Profile</a><a href="/logout">↪ Logout</a></div></div>
</aside>
<script>
(function(){{const p=window.location.pathname;document.querySelectorAll('.page-sidebar-nav a[data-page]').forEach(function(a){{const k=a.dataset.page;if((k==='dashboard'&&p==='/dashboard')||(k==='schedule'&&p.startsWith('/schedule'))||(k==='deadlines'&&p.startsWith('/deadlines'))||(k==='group-projects'&&p.startsWith('/group-projects'))||(k==='notes'&&p.startsWith('/notes'))||(k==='notifications'&&p.startsWith('/notifications'))||(k==='profile'&&p.startsWith('/profile'))||(k==='settings'&&p.startsWith('/settings')))a.classList.add('active')}})}})();
function togglePageMenu(){{const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle'),o=s.classList.toggle('open');document.body.classList.toggle('page-nav-open',o);b.setAttribute('aria-expanded',o?'true':'false')}}
function closePageMenu(){{const s=document.getElementById('pageSidebar'),b=document.querySelector('.page-menu-toggle');s.classList.remove('open');document.body.classList.remove('page-nav-open');if(b)b.setAttribute('aria-expanded','false')}}
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closePageMenu()}});
</script>

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
                    <div class="time-field"><label for="scheduleTimeIn">🕐 Time In</label><input id="scheduleTimeIn" type="time" name="time_in" required></div>
                    <div class="time-field"><label for="scheduleTimeOut">🕐 Time Out</label><input id="scheduleTimeOut" type="time" name="time_out" required></div>
                    <label style="grid-column:1/-1;font-weight:700;color:#174B7A;">⏰ Alarm / Reminder (Optional)</label>
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