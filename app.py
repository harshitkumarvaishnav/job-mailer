import os, json, base64, uuid
from flask import Flask, request, render_template, redirect, url_for, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from ocr import extract_job_data
from matcher import choose_resume
from email_writer import write_email

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

BASE = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS = os.path.join(BASE, "uploads", "screenshots")
RESUMES = os.path.join(BASE, "uploads", "resumes")
SENT_DIR = os.path.join(BASE, "output_sent")
CLIENT_SECRET = os.path.join(BASE, "credentials.json")
TOKEN_FILE = os.path.join(BASE, "token.json")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]
REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"

for p in [SCREENSHOTS, RESUMES, SENT_DIR]:
    os.makedirs(p, exist_ok=True)

def gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        return None
    return build("gmail", "v1", credentials=creds)

def load_job(job_id):
    with open(os.path.join(SENT_DIR, job_id + ".json"), encoding="utf-8") as f:
        return json.load(f)

def save_job(job):
    with open(os.path.join(SENT_DIR, job["id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    resumes = sorted(os.listdir(RESUMES))
    jobs = []
    for fn in sorted(os.listdir(SENT_DIR)):
        if fn.endswith(".json"):
            jobs.append(load_job(fn[:-5]))
    return render_template("index.html", resumes=resumes, jobs=jobs, connected=gmail_service() is not None)

@app.route("/upload", methods=["POST"])
def upload():
    for file in request.files.getlist("screenshots"):
        if file.filename:
            file.save(os.path.join(SCREENSHOTS, uuid.uuid4().hex + "_" + file.filename))

    resumes = request.files.getlist("resumes")
    tags = [t.strip().lower() for t in request.form.get("resume_tags", "").split(",")]
    for i, file in enumerate(resumes):
        if file.filename:
            tag = tags[i] if i < len(tags) and tags[i] else ""
            name = (tag + "_" if tag else "") + file.filename
            file.save(os.path.join(RESUMES, name))
    return redirect(url_for("index"))

@app.route("/process", methods=["POST"])
def process():
    for fn in sorted(os.listdir(SCREENSHOTS)):
        path = os.path.join(SCREENSHOTS, fn)
        try:
            data = extract_job_data(path)
        except Exception as e:
            data = {"emails": [], "jd": "", "company": "", "role": "", "error": str(e)}

        resume = choose_resume(data.get("jd", ""), os.listdir(RESUMES), RESUMES)
        mail = write_email(data.get("jd", ""), data.get("company", ""))
        job = {
            "id": uuid.uuid4().hex,
            "screenshot": fn,
            "emails": data.get("emails", []),
            "company": data.get("company", ""),
            "role": data.get("role", ""),
            "jd": data.get("jd", ""),
            "resume": resume,
            "subject": mail["subject"],
            "body": mail["body"],
            "status": "pending",
        }
        save_job(job)
    return redirect(url_for("index"))

@app.route("/update/<job_id>", methods=["POST"])
def update(job_id):
    job = load_job(job_id)
    job["to"] = request.form.get("to", "")
    job["subject"] = request.form.get("subject", "")
    job["body"] = request.form.get("body", "")
    job["resume"] = request.form.get("resume", "")
    save_job(job)
    return redirect(url_for("index"))

@app.route("/send/<job_id>", methods=["POST"])
def send(job_id):
    service = gmail_service()
    if not service:
        return redirect(url_for("authorize"))

    job = load_job(job_id)
    to = job.get("to") or (job.get("emails") or [""])[0]
    if not to:
        job["status"] = "error: no recipient"
        save_job(job)
        return redirect(url_for("index"))

    boundary = "job_mailer_boundary"
    attachment = ""
    resume_path = os.path.join(RESUMES, job.get("resume", ""))
    if job.get("resume") and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            encoded = base64.urlsafe_b64encode(f.read()).decode()
        attachment = (
            "--" + boundary + "\r\n"
            'Content-Type: application/pdf; name="' + job["resume"] + '"\r\n'
            'Content-Disposition: attachment; filename="' + job["resume"] + '"\r\n'
            "Content-Transfer-Encoding: base64\r\n\r\n"
            + encoded + "\r\n"
        )

    raw = (
        "To: " + to + "\r\n"
        "Subject: " + job["subject"] + "\r\n"
        "MIME-Version: 1.0\r\n"
        'Content-Type: multipart/mixed; boundary="' + boundary + '"\r\n\r\n'
        "--" + boundary + "\r\n"
        'Content-Type: text/plain; charset="UTF-8"\r\n\r\n'
        + job["body"] + "\r\n"
        + attachment
        + "--" + boundary + "--"
    )

    try:
        service.users().messages().send(
            userId="me",
            body={"raw": base64.urlsafe_b64encode(raw.encode()).decode()},
        ).execute()
        job["status"] = "sent"
    except Exception as e:
        job["status"] = "error: " + str(e)
    save_job(job)
    return redirect(url_for("index"))

@app.route("/authorize")
def authorize():
    if not os.path.exists(CLIENT_SECRET):
        return "Add credentials.json (Google OAuth Desktop client) to the project folder."
    flow = Flow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    session["state"] = state
    return redirect(url)

@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET, scopes=SCOPES, state=session.get("state"), redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    with open(TOKEN_FILE, "w") as f:
        f.write(flow.credentials.to_json())
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
