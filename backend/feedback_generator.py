# backend/feedback_generator.py
import re

SUGGESTED_BY_ROLE = {
    "data analyst": ["sql","power bi","tableau","python","statistics","excel"],
    "data scientist": ["python","pandas","machine learning","deep learning","statistics"],
    "web developer": ["html","css","javascript","react","node.js"],
    "software engineer": ["java","git","algorithms","system design"]
}

def generate_feedback(resume_skills, jd_skills, candidate_name, job_title):
    rs = set([s.lower() for s in (resume_skills or [])])
    jd = set([s.lower() for s in (jd_skills or [])])

    missing = []
    if jd:
        missing = sorted(list(jd - rs))
    else:
        # fallback suggestions from role
        suggested = []
        jt = (job_title or "").lower()
        for role, skills in SUGGESTED_BY_ROLE.items():
            if role in jt:
                suggested = skills
                break
        if not suggested:
            suggested = ["communication","teamwork","problem solving"]
        missing = suggested

    name = candidate_name or "Candidate"
    if jd:
        if not missing:
            summary = f"Good job {name}! Your resume covers the required skills for this role."
        else:
            summary = f"{name}, you are missing {len(missing)} key skill(s) for this role. Consider adding: {', '.join([m.title() for m in missing])}."
    else:
        summary = f"{name}, the JD had no explicit skills. Based on the role '{job_title}', consider adding: {', '.join([m.title() for m in missing])}."

    # Add tips
    tips = [
        "Add 2-3 relevant projects with links and quantify results.",
        "Use keywords from the JD in your summary and experience bullets.",
        "Place a concise skills section near the top of the resume."
    ]
    full = summary + " " + " ".join(tips)
    return {"missing_skills": missing, "summary": full}
