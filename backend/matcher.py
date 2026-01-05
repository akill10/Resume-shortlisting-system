# backend/matcher.py
import re

SKILLS_DB = [
    "python","sql","excel","power bi","tableau","pandas","numpy","machine learning",
    "deep learning","tensorflow","pytorch","data analysis","statistics","r","matlab",
    "html","css","javascript","react","node.js","java","c++","c#","django","flask","aws","azure","git"
]

def extract_job_skills(job_description, job_title=""):
    text = (job_description or "") + " " + (job_title or "")
    t = text.lower()
    found = []
    for s in SKILLS_DB:
        if re.search(rf"\b{re.escape(s)}\b", t):
            found.append(s)
    # fallback mapping by role
    if not found and job_title:
        role_map = {
            "data analyst": ["sql","excel","power bi","tableau","python"],
            "data scientist": ["python","pandas","machine learning","statistics"],
            "web developer": ["html","css","javascript","react","node.js"],
            "backend": ["python","django","flask","node.js"],
            "frontend": ["html","css","javascript","react"],
            "cloud": ["aws","azure"]
        }
        jt = job_title.lower()
        for k,v in role_map.items():
            if k in jt:
                found = v
                break
    return found

def compute_score(resume_skills, jd_skills):
    if not jd_skills:
        return 0.0
    rs = set([s.lower() for s in (resume_skills or [])])
    jd = set([s.lower() for s in (jd_skills or [])])
    matched = rs & jd
    score = (len(matched) / len(jd)) * 100.0
    return round(score,2)
