import json
import os
import random

from ai.company_questions import get_company_questions_for_profession

PROFESSION_TAG_MAP = {
    "software engineer": ["python", "api", "backend", "data structures", "algorithms"],
    "backend developer": ["python", "api", "sql", "database", "backend"],
    "frontend developer": ["javascript", "html", "css", "react", "ui/ux"],
    "full stack developer": ["javascript", "python", "api", "sql", "html", "css"],
    "devops engineer": ["docker", "api", "cloud", "automation"],
    "qa engineer": ["testing", "api", "quality"],
    "data analyst": ["sql", "analytics", "data"],
    "data scientist": ["machine learning", "nlp", "python", "data"],
    "machine learning engineer": ["machine learning", "nlp", "python", "api"],
    "cybersecurity analyst": ["security", "network", "risk"],
    "product manager": ["communication", "stakeholders", "planning", "impact"],
    "business analyst": ["communication", "stakeholders", "analysis"],
    "ui/ux designer": ["ui/ux", "communication", "design"],
    "hr recruiter": ["communication", "teamwork", "self awareness"],
    "hr manager": ["communication", "leadership", "teamwork"],
    "sales executive": ["communication", "growth mindset", "ownership"],
    "marketing specialist": ["communication", "growth mindset", "impact"],
}

PROFESSION_FOCUS_MAP = {
    "software engineer": ["scalable", "api", "debug", "performance", "architecture"],
    "backend developer": ["api", "database", "sql", "performance", "microservices"],
    "frontend developer": ["ui", "javascript", "accessibility", "react", "browser"],
    "full stack developer": ["api", "frontend", "database", "integration", "deployment"],
    "devops engineer": ["deployment", "automation", "cloud", "ci/cd", "monitoring"],
    "qa engineer": ["testing", "quality", "bug", "automation", "regression"],
    "data analyst": ["sql", "dashboard", "insights", "analytics", "data quality"],
    "data scientist": ["machine learning", "model", "metrics", "features", "experiments"],
    "machine learning engineer": ["model", "serving", "mlops", "latency", "pipeline"],
    "cybersecurity analyst": ["security", "risk", "incident", "threat", "compliance"],
    "product manager": ["stakeholders", "roadmap", "impact", "prioritization", "metrics"],
    "business analyst": ["requirements", "stakeholders", "analysis", "kpi", "process"],
    "ui/ux designer": ["users", "design", "research", "accessibility", "journey"],
    "hr recruiter": ["hiring", "candidate", "communication", "culture", "fit"],
    "hr manager": ["people", "leadership", "conflict", "policy", "engagement"],
    "sales executive": ["targets", "negotiation", "customer", "pipeline", "growth"],
    "marketing specialist": ["campaign", "audience", "brand", "conversion", "analytics"],
}

PROFESSION_PENALTY_TERMS = {
    "data analyst": ["flask", "endpoint", "url shortener", "browser", "microservices"],
    "data scientist": ["flask", "endpoint", "url shortener", "browser", "microservices"],
    "hr recruiter": ["cap theorem", "url shortener", "rest api", "sql indexing"],
    "hr manager": ["cap theorem", "url shortener", "rest api", "sql indexing"],
    "marketing specialist": ["cap theorem", "url shortener", "rest api"],
    "sales executive": ["cap theorem", "url shortener", "rest api"],
}

PROFESSION_BOOST_TERMS = {
    "data analyst": ["sql", "analytics", "dashboard", "data"],
    "data scientist": ["model", "machine learning", "experiment", "features"],
    "backend developer": ["api", "database", "performance", "scalable"],
    "frontend developer": ["ui", "javascript", "browser", "accessibility"],
}


def load_questions():
    path = os.path.join("data", "question_bank.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def infer_profession_tags(profession):
    if not profession:
        return []

    p = profession.lower().strip()
    if p in PROFESSION_TAG_MAP:
        return PROFESSION_TAG_MAP[p]

    tags = []
    if any(k in p for k in ["engineer", "developer", "qa", "devops", "software", "programmer"]):
        tags += ["python", "api", "backend", "data structures", "algorithms"]
    if any(k in p for k in ["data", "analyst", "scientist", "ml", "ai"]):
        tags += ["sql", "python", "machine learning", "nlp", "data"]
    if any(k in p for k in ["hr", "recruit", "people", "talent"]):
        tags += ["communication", "teamwork", "self awareness"]
    if any(k in p for k in ["manager", "product", "business", "designer"]):
        tags += ["communication", "leadership", "planning", "stakeholders"]

    return list(dict.fromkeys(tags))


def infer_profession_focus_terms(profession):
    if not profession:
        return []

    p = profession.lower().strip()
    if p in PROFESSION_FOCUS_MAP:
        return PROFESSION_FOCUS_MAP[p]

    dynamic = []
    if any(k in p for k in ["engineer", "developer", "qa", "devops", "software"]):
        dynamic += ["api", "debug", "performance", "architecture", "testing"]
    if any(k in p for k in ["data", "analyst", "scientist", "ml", "ai"]):
        dynamic += ["data", "sql", "metrics", "analysis", "model"]
    if any(k in p for k in ["hr", "recruit", "talent", "people"]):
        dynamic += ["communication", "candidate", "culture", "conflict", "fit"]
    if any(k in p for k in ["manager", "product", "business", "designer"]):
        dynamic += ["stakeholders", "impact", "prioritization", "planning", "users"]

    return list(dict.fromkeys(dynamic))


def role_match_score(item, skills, profession_tags, profession_focus):
    q_skills = [x.lower() for x in item.get("skills", [])]
    q_text = " ".join(
        [
            item.get("question", ""),
            item.get("ideal_answer", ""),
            " ".join(item.get("keywords", [])),
            " ".join(q_skills),
        ]
    ).lower()

    resume_match = len(set(q_skills).intersection(skills))
    profession_match = len(set(q_skills).intersection(profession_tags))
    focus_match = sum(1 for token in profession_focus if token in q_text)
    company_match = 1 if item.get("question", "").startswith("[") else 0

    return profession_match * 5 + focus_match * 3 + resume_match * 2 + company_match * 20


def profession_term_adjustment(item, profession):
    if not profession:
        return 0
    p = profession.lower().strip()
    q_text = " ".join(
        [
            item.get("question", ""),
            item.get("ideal_answer", ""),
            " ".join(item.get("keywords", [])),
            " ".join(item.get("skills", [])),
        ]
    ).lower()

    penalty = sum(1 for t in PROFESSION_PENALTY_TERMS.get(p, []) if t in q_text) * 4
    boost = sum(1 for t in PROFESSION_BOOST_TERMS.get(p, []) if t in q_text) * 2
    return boost - penalty


def filter_questions(interview_type, difficulty, excluded_ids=None, skills=None, profession=None):
    excluded_ids = excluded_ids or []
    skills = [s.lower() for s in (skills or [])]
    profession_tags = [s.lower() for s in infer_profession_tags(profession)]
    profession_focus = [s.lower() for s in infer_profession_focus_terms(profession)]
    all_questions = load_questions() + get_company_questions_for_profession(profession)

    def apply_type(items):
        if interview_type == "mixed":
            return items
        return [x for x in items if x["type"] == interview_type]

    tier_1 = [x for x in apply_type(all_questions) if x["difficulty"] == difficulty and x["id"] not in excluded_ids]
    weighted_t1 = sorted(
        [(
            role_match_score(item, skills, profession_tags, profession_focus)
            + profession_term_adjustment(item, profession),
            item,
        ) for item in tier_1],
        key=lambda x: x[0],
        reverse=True,
    )
    if weighted_t1 and weighted_t1[0][0] > 0:
        top = weighted_t1[0][0]
        return [item for score, item in weighted_t1 if score >= max(2, top - 2)]

    tier_2 = [x for x in apply_type(all_questions) if x["id"] not in excluded_ids]
    weighted_t2 = sorted(
        [(
            role_match_score(item, skills, profession_tags, profession_focus)
            + profession_term_adjustment(item, profession),
            item,
        ) for item in tier_2],
        key=lambda x: x[0],
        reverse=True,
    )
    if weighted_t2 and weighted_t2[0][0] > 0:
        top = weighted_t2[0][0]
        return [item for score, item in weighted_t2 if score >= max(2, top - 2)]

    tier_3 = [x for x in apply_type(all_questions) if x["difficulty"] == difficulty and x["id"] not in excluded_ids]
    if tier_3:
        return tier_3

    broad = [x for x in all_questions if x["id"] not in excluded_ids]
    return broad if broad else all_questions


def personality_prefix(personality):
    styles = {
        "strict": "Answer precisely and avoid generic statements.",
        "friendly": "Take your time, and explain with clarity.",
        "technical": "Focus on implementation depth and practical detail.",
    }
    return styles.get(personality, styles["friendly"])


def get_question(
    interview_type,
    difficulty,
    excluded_ids=None,
    skills=None,
    profession=None,
    language="en",
    personality="friendly",
):
    pool = filter_questions(interview_type, difficulty, excluded_ids, skills, profession)
    item = random.choice(pool)
    display = item.get("question_hi") if language == "hi" and item.get("question_hi") else item["question"]

    if profession:
        role_prefix = f"For the {profession.title()} role"
        display = f"{role_prefix}, {display[0].lower() + display[1:]}" if len(display) > 1 else f"{role_prefix}, {display}"

    return {
        "id": item["id"],
        "type": item["type"],
        "difficulty": item["difficulty"],
        "display_question": display,
        "raw_question": item["question"],
        "keywords": item.get("keywords", []),
        "ideal_answer": item.get("ideal_answer", ""),
        "model_answer": item.get("model_answer", ""),
        "personality_prompt": personality_prefix(personality),
    }
