import re
import pytesseract
from PIL import Image

# Windows: uncomment and adjust if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
ROLES = [
    "vapt", "penetration testing", "penetration tester", "security analyst",
    "soc analyst", "grc", "governance risk compliance", "digital forensics",
    "dfir", "incident response", "cyber security", "cybersecurity",
    "cloud security", "application security", "security engineer",
]

def extract_job_data(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    jd = " ".join(text.split())
    emails = []
    for email in EMAIL_RE.findall(text):
        email = email.lower().strip(".,;")
        if email not in emails:
            emails.append(email)

    company = ""
    match = re.search(r"(?:at|company[:\-])\s+([A-Za-z0-9 &.,'-]{2,60})", text, re.I)
    if match:
        company = match.group(1).strip()

    role = ""
    lower = jd.lower()
    for keyword in ROLES:
        if keyword in lower:
            role = keyword.title()
            break

    return {"text": text, "jd": jd, "emails": emails, "company": company, "role": role}
