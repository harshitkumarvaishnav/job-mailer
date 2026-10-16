def write_email(jd, company=""):
    jd_lower = jd.lower()
    category = "Cybersecurity"
    if any(k in jd_lower for k in ["vapt", "penetration"]):
        category = "VAPT"
    elif any(k in jd_lower for k in ["grc", "governance", "compliance", "audit"]):
        category = "GRC"
    elif any(k in jd_lower for k in ["dfir", "forensic", "incident response", "malware"]):
        category = "Digital Forensics and Incident Response"
    elif any(k in jd_lower for k in ["soc", "siem", "splunk", "security operations"]):
        category = "SOC / Security Operations"
    elif any(k in jd_lower for k in ["cloud security", "aws", "azure", "iam"]):
        category = "Cloud Security"

    company_part = " at " + company if company else ""
    subject = "Application for " + category + " Opportunity" + company_part
    body = (
        "Dear Hiring Manager,\n\n"
        "I hope you are doing well.\n\n"
        "I came across the " + category + " opportunity" + company_part +
        " and would like to apply for the role. My background includes cybersecurity fundamentals, "
        "vulnerability assessment, security operations, and incident-response concepts. "
        "This role aligns well with my technical interests and career goals.\n\n"
        "I have attached my resume for your review. I would appreciate the opportunity to discuss "
        "how my skills can contribute to your team.\n\n"
        "Thank you for your time and consideration.\n\n"
        "Best regards,\n"
        "Harshit\n"
        "[Your Phone Number]\n"
        "[Your LinkedIn Profile]\n"
    )
    return {"subject": subject, "body": body}
