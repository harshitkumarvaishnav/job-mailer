import os
from pdfminer.high_level import extract_text

CATEGORIES = {
    "vapt": ["vapt", "penetration testing", "penetration tester", "vulnerability assessment", "ethical hacking", "web application security"],
    "grc": ["grc", "governance", "risk", "compliance", "iso 27001", "audit", "policy"],
    "dfir": ["digital forensics", "dfir", "incident response", "malware analysis", "mobile forensics", "email forensics"],
    "soc": ["soc analyst", "siem", "splunk", "qradar", "security operations", "threat monitoring"],
    "cloud": ["cloud security", "aws security", "azure security", "iam", "cloud"],
}

def score_resume(jd, path):
    try:
        text = extract_text(path).lower() if path.lower().endswith(".pdf") else ""
    except Exception:
        text = ""
    jd_lower = jd.lower()
    score = 0
    for category, keywords in CATEGORIES.items():
        jd_hits = sum(k in jd_lower for k in keywords)
        resume_hits = sum(k in text for k in keywords)
        if jd_hits and resume_hits:
            score += jd_hits * 2 + resume_hits
        elif resume_hits:
            score += resume_hits * 0.5
        if category in os.path.basename(path).lower():
            score += 5
    return score

def choose_resume(jd, resume_files, upload_dir):
    best, best_score = "", -1
    for resume in resume_files:
        score = score_resume(jd, os.path.join(upload_dir, resume))
        if score > best_score:
            best, best_score = resume, score
    return best
