# Job Mailer

Local Flask web app: upload LinkedIn/job screenshots and resumes, extract HR emails with OCR,
match a resume to the JD, generate a personalized email, then review and send through Gmail.

## Setup

1. Install Python 3.10+ and Tesseract OCR.
   - Windows installer: https://github.com/UB-Mannheim/tesseract/wiki
   - Default path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
2. Put Google OAuth Desktop credentials in this folder as `credentials.json`.
   - In Google Cloud Console: enable Gmail API, create OAuth Client ID (Desktop app), download JSON.
3. Install packages:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
python app.py
```

5. Open http://127.0.0.1:5000

## Usage

1. Upload job screenshots.
2. Upload resumes and enter tags in the same order, e.g. `vapt, grc, dfir`.
3. Click **Extract Emails, Match Resumes, Create Drafts**.
4. Review recipient, subject, body, and attachment.
5. Click **Send This Email** for each job.

## Notes

- The app sends one email at a time after your review; this reduces spam-filter risk.
- Add your phone number and LinkedIn URL in `email_writer.py`.
- If OCR cannot find an email, enter it manually in the review form.
- For Windows, if Tesseract is not in PATH, edit `ocr.py` and set `pytesseract.pytesseract.tesseract_cmd`.
