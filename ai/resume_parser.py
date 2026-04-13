import os
import re

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

COMMON_SKILLS = [
    "python", "flask", "django", "sql", "mysql", "sqlite", "javascript", "react",
    "html", "css", "machine learning", "nlp", "data structures", "algorithms", "api", "git",
]


def extract_text_from_resume(file_path):
    if not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf" and PyPDF2:
        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in reader.pages:
                text.append(p.extract_text() or "")
        return "\n".join(text)
    return ""


def find_skills(text):
    t = text.lower()
    out = []
    for skill in COMMON_SKILLS:
        if re.search(r"\\b" + re.escape(skill) + r"\\b", t):
            out.append(skill.title())
    return out
