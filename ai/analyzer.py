import re


def keyword_relevance(answer, keywords):
    if not keywords:
        return 50
    text = answer.lower()
    hits = sum(1 for k in keywords if k.lower() in text)
    return round((hits / len(keywords)) * 100, 2)


def simple_sentiment(answer):
    positive = ["confident", "improved", "achieved", "success", "strong", "efficient"]
    negative = ["not sure", "difficult", "confused", "failed"]
    a = answer.lower()
    score = 50 + 8 * sum(w in a for w in positive) - 8 * sum(w in a for w in negative)
    return max(0, min(100, score))


def grammar_quality(answer):
    if not answer.strip():
        return 0, "Please provide a complete answer."
    starts_capital = answer.strip()[0].isupper()
    ends_punct = answer.strip()[-1] in ".!?"
    score = 70 + (15 if starts_capital else 0) + (15 if ends_punct else 0)
    return min(100, score), "Grammar looks good." if score >= 80 else "Use proper capitalization and punctuation."


def clarity_score(answer):
    words = re.findall(r"[A-Za-z]+", answer)
    if not words:
        return 0
    return 80 if 20 <= len(words) <= 120 else 60


def completeness_score(answer, ideal):
    aw = set(re.findall(r"[A-Za-z]+", answer.lower()))
    iw = set(re.findall(r"[A-Za-z]+", (ideal or "").lower()))
    if not iw:
        return 60
    return round(100 * len(aw.intersection(iw)) / len(iw), 2)


def filler_word_count(answer):
    fillers = ["um", "uh", "like", "actually", "basically", "you know"]
    t = answer.lower()
    return sum(len(re.findall(r"\\b" + re.escape(x) + r"\\b", t)) for x in fillers)


def think_time_score(seconds):
    if seconds <= 2:
        return 55
    if seconds <= 8:
        return 90
    if seconds <= 15:
        return 70
    return 50


def rewrite_answer_coach(answer, question_text, model_answer, keywords):
    answer = (answer or "").strip()
    if not answer:
        return {
            "improved_answer": "Start with a concise context, add your action, and close with a measurable result.",
            "coach_tips": [
                "Use STAR format: Situation, Task, Action, Result.",
                "Mention at least 2 role-specific keywords.",
                "End with impact (time saved, quality improved, or revenue/user impact).",
            ],
            "missing_keywords": list(keywords or [])[:4],
        }

    original = re.sub(r"\s+", " ", answer).strip()
    sanitized = re.sub(r"\b(um|uh|like|basically|actually|you know)\b", "", original, flags=re.IGNORECASE)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    sanitized = re.sub(r"\bi think\b", "I believe", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bmaybe\b", "with a clear plan", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bkind of\b", "specifically", sanitized, flags=re.IGNORECASE)

    if sanitized and sanitized[-1] not in ".!?":
        sanitized += "."
    if sanitized and sanitized[0].islower():
        sanitized = sanitized[0].upper() + sanitized[1:]

    present = {k for k in (keywords or []) if k.lower() in sanitized.lower()}
    missing = [k for k in (keywords or []) if k.lower() not in sanitized.lower()]

    sentence_parts = [s.strip() for s in re.split(r"[.!?]+", sanitized) if s.strip()]
    user_summary = sentence_parts[0] if sentence_parts else sanitized
    model_seed = re.sub(r"\s+", " ", (model_answer or "")).strip()
    q_focus = re.sub(r"\s+", " ", (question_text or "")).strip()

    missing_line = ""
    if missing:
        missing_line = " I would explicitly mention " + ", ".join(missing[:3]) + " to align with interviewer expectations."

    if model_seed:
        improved = (
            f"For this question ({q_focus[:90]}), a stronger answer is: {model_seed} "
            f"My relevant context is: {user_summary}.{missing_line}"
        )
    else:
        improved = (
            f"For this question ({q_focus[:90]}), I would answer with a clear structure: "
            f"Situation, action, and measurable outcome. My context: {user_summary}.{missing_line}"
        )

    improved = re.sub(r"\s+", " ", improved).strip()
    improved = re.sub(r"\bi\b", "I", improved)
    if improved and improved[0].islower():
        improved = improved[0].upper() + improved[1:]

    if improved.lower().strip(". ") == original.lower().strip(". "):
        improved = (
            "I handled this by defining the goal clearly, taking focused action, and delivering a measurable outcome. "
            + improved
        )

    return {
        "improved_answer": improved.strip(),
        "coach_tips": [
            "Lead with one-line summary, then action, then measurable outcome.",
            "Use fewer filler words and avoid uncertain phrases.",
            "Keep answers between 45 and 90 words for strong clarity.",
        ],
        "missing_keywords": missing[:5],
        "matched_keywords": sorted(list(present))[:5],
        "question_focus": question_text[:120],
    }


def analyze_answer(answer, question_data, think_time=0):
    relevance = keyword_relevance(answer, question_data.get("keywords", []))
    confidence = simple_sentiment(answer)
    grammar, grammar_suggestion = grammar_quality(answer)
    clarity = clarity_score(answer)
    completeness = completeness_score(answer, question_data.get("ideal_answer", ""))
    fillers = filler_word_count(answer)
    tscore = think_time_score(think_time)

    overall = relevance * 0.3 + confidence * 0.15 + grammar * 0.2 + clarity * 0.15 + completeness * 0.15 + tscore * 0.05 - min(20, fillers * 3)
    overall = round(max(0, min(100, overall)), 2)

    strengths = []
    weaknesses = []
    suggestions = []

    if relevance >= 70:
        strengths.append("Good relevance to the asked question.")
    else:
        weaknesses.append("Missing important role-specific keywords.")
        suggestions.append("Mention key technical/business terms and outcomes.")

    if fillers > 2:
        weaknesses.append(f"High filler usage ({fillers}).")
        suggestions.append("Pause silently instead of using filler words.")
    else:
        strengths.append("Low filler words and better fluency.")

    if think_time > 12:
        suggestions.append("Use a quick answer framework to reduce think time.")

    if not suggestions:
        suggestions.append("Keep practicing with concise STAR-based answers.")

    rewrite = rewrite_answer_coach(
        answer=answer,
        question_text=question_data.get("display_question", ""),
        model_answer=question_data.get("model_answer", ""),
        keywords=question_data.get("keywords", []),
    )

    return {
        "relevance_score": relevance,
        "confidence_score": confidence,
        "grammar_score": grammar,
        "clarity_score": clarity,
        "completeness_score": completeness,
        "think_time_score": tscore,
        "filler_word_count": fillers,
        "overall_score": overall,
        "grammar_suggestion": grammar_suggestion,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "model_answer": question_data.get("model_answer", ""),
        "rewrite_coach": rewrite,
    }


def compute_hire_probability(responses):
    if not responses:
        return 0
    avg = sum(r.overall_score for r in responses) / len(responses)
    filler = sum(r.filler_count for r in responses) / len(responses)
    think = sum(r.think_time for r in responses) / len(responses)
    score = avg - min(15, filler * 3) - (5 if think > 12 else 0)
    return max(0, min(100, score))


def build_interview_dna_profile(responses, interview_type="mixed", personality="friendly"):
    if not responses:
        return {
            "archetype": "Emerging Candidate",
            "summary": "Complete one interview to unlock your Interview DNA.",
            "traits": [],
            "dimensions": [],
        }

    n = len(responses)
    avg_relevance = sum(r.relevance_score for r in responses) / n
    avg_confidence = sum(r.sentiment_score for r in responses) / n
    avg_grammar = sum(r.grammar_score for r in responses) / n
    avg_clarity = sum(r.clarity_score for r in responses) / n
    avg_completeness = sum(r.completeness_score for r in responses) / n
    avg_filler = sum(r.filler_count for r in responses) / n
    avg_think_time = sum(r.think_time for r in responses) / n

    communication = max(0, min(100, (avg_grammar * 0.45 + avg_clarity * 0.55) - min(12, avg_filler * 3)))
    problem_solving = max(0, min(100, avg_completeness * 0.5 + avg_relevance * 0.5))
    confidence_exec = max(0, min(100, avg_confidence * 0.75 + (100 - min(35, avg_think_time * 2)) * 0.25))
    role_alignment = max(0, min(100, avg_relevance * 0.6 + avg_completeness * 0.4))

    if communication >= 78 and role_alignment >= 75 and confidence_exec >= 70:
        archetype = "Structured Communicator"
        summary = "You present ideas clearly with strong role alignment and steady delivery."
    elif problem_solving >= 75 and role_alignment >= 70:
        archetype = "Analytical Solver"
        summary = "You are strong at solution thinking and covering key technical/business points."
    elif confidence_exec >= 72 and communication >= 68:
        archetype = "Confident Storyteller"
        summary = "You communicate confidently and can strengthen depth to become interview-ready faster."
    else:
        archetype = "Growth Track Candidate"
        summary = "You have a strong base and will improve quickly with focused practice on weak spots."

    traits = []
    if avg_filler <= 2:
        traits.append("Fluent delivery with minimal filler words.")
    if avg_think_time <= 8:
        traits.append("Quick response readiness under interview pressure.")
    if avg_relevance >= 72:
        traits.append("Answers stay aligned with what interviewers ask.")
    if not traits:
        traits.append("Your pattern is improving; consistency will unlock stronger performance.")

    dimensions = [
        {"label": "Communication", "score": round(communication, 2)},
        {"label": "Problem Solving", "score": round(problem_solving, 2)},
        {"label": "Confidence", "score": round(confidence_exec, 2)},
        {"label": "Role Fit", "score": round(role_alignment, 2)},
        {"label": "Interview Type Match", "score": 82 if interview_type == "mixed" else 76},
        {"label": "Personality Sync", "score": 80 if personality == "friendly" else 74},
    ]

    return {
        "archetype": archetype,
        "summary": summary,
        "traits": traits,
        "dimensions": dimensions,
    }


def build_skill_gap_heatmap(responses):
    if not responses:
        return []

    buckets = {
        "Role Keywords": [],
        "Completeness": [],
        "Communication": [],
        "Confidence": [],
        "Fluency": [],
        "Think-Time Control": [],
    }

    for r in responses:
        buckets["Role Keywords"].append(r.relevance_score)
        buckets["Completeness"].append(r.completeness_score)
        buckets["Communication"].append((r.grammar_score + r.clarity_score) / 2)
        buckets["Confidence"].append(r.sentiment_score)
        buckets["Fluency"].append(max(0, 100 - min(45, r.filler_count * 12)))
        buckets["Think-Time Control"].append(max(0, 100 - min(50, r.think_time * 4)))

    rows = []
    for name, values in buckets.items():
        score = round(sum(values) / len(values), 2)
        gap = round(max(0, 100 - score), 2)
        if score >= 80:
            level = "strong"
        elif score >= 65:
            level = "moderate"
        else:
            level = "critical"
        rows.append({"skill": name, "score": score, "gap": gap, "level": level})

    rows.sort(key=lambda x: x["gap"], reverse=True)
    return rows
