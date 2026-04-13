from ai.questions import get_question
from models import InterviewResponse


def get_target_difficulty(session_id):
    responses = InterviewResponse.query.filter_by(session_id=session_id).all()
    if not responses:
        return "easy"
    avg = sum(r.overall_score for r in responses) / len(responses)
    if avg >= 80:
        return "hard"
    if avg >= 55:
        return "medium"
    return "easy"


def get_next_question(
    interview_type,
    difficulty,
    excluded_ids=None,
    skills=None,
    profession=None,
    language="en",
    personality="friendly",
):
    return get_question(
        interview_type=interview_type,
        difficulty=difficulty,
        excluded_ids=excluded_ids,
        skills=skills,
        profession=profession,
        language=language,
        personality=personality,
    )
