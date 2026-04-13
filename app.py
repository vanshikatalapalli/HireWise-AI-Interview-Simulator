import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from ai.adaptive import get_next_question, get_target_difficulty
from ai.analyzer import (
    analyze_answer,
    build_interview_dna_profile,
    build_skill_gap_heatmap,
    compute_hire_probability,
)
from ai.resume_parser import extract_text_from_resume, find_skills
from models import Achievement, InterviewResponse, InterviewSession, User, db

try:
    import cv2
except ImportError:
    cv2 = None

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-smart-interview-secret")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

db_backend = os.environ.get("DB_BACKEND", "sqlite").lower()
if db_backend == "mysql":
    db_user = os.environ.get("DB_USER", "root")
    db_password = quote_plus(os.environ.get("DB_PASSWORD", ""))
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT", "3306")
    db_name = os.environ.get("DB_NAME", "smart_interview")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
else:
    sqlite_path = os.path.join(tempfile.gettempdir(), "interview_simulator.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path.replace(os.sep, '/')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["APPLICATION_ROOT"] = os.environ.get("APPLICATION_ROOT", "/")
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1, x_host=1, x_proto=1)

PROFESSION_TYPE_MAP = {
    "software engineer": "technical",
    "backend developer": "technical",
    "frontend developer": "technical",
    "full stack developer": "technical",
    "devops engineer": "technical",
    "qa engineer": "technical",
    "data analyst": "technical",
    "data scientist": "mixed",
    "machine learning engineer": "technical",
    "cybersecurity analyst": "technical",
    "product manager": "mixed",
    "business analyst": "mixed",
    "ui/ux designer": "mixed",
    "hr recruiter": "hr",
    "hr manager": "hr",
    "sales executive": "hr",
    "marketing specialist": "hr",
}

PROFESSION_GROUPS = {
    "technical": sorted([p for p, t in PROFESSION_TYPE_MAP.items() if t == "technical"]),
    "hr": sorted([p for p, t in PROFESSION_TYPE_MAP.items() if t == "hr"]),
    "mixed": sorted([p for p, t in PROFESSION_TYPE_MAP.items() if t == "mixed"]),
}

db.init_app(app)


def init_db():
    with app.app_context():
        db.create_all()


def login_required(view_func):
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    wrapped.__name__ = view_func.__name__
    return wrapped


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def infer_interview_type_from_profession(profession):
    if not profession:
        return "mixed"
    normalized = profession.lower().strip()
    if normalized in PROFESSION_TYPE_MAP:
        return PROFESSION_TYPE_MAP[normalized]

    technical_keywords = [
        "engineer", "developer", "data", "analyst", "qa", "devops", "cyber", "cloud",
        "architect", "programmer", "software", "it", "ai", "ml",
    ]
    hr_keywords = [
        "hr", "recruit", "talent", "people", "sales", "marketing", "support", "customer",
    ]
    mixed_keywords = [
        "manager", "designer", "consultant", "product", "business",
    ]

    if any(k in normalized for k in technical_keywords):
        return "technical"
    if any(k in normalized for k in hr_keywords):
        return "hr"
    if any(k in normalized for k in mixed_keywords):
        return "mixed"
    return "mixed"


def assign_badges(user):
    existing = {badge.title for badge in user.achievements}
    total_sessions = InterviewSession.query.filter_by(user_id=user.id, status="completed").count()

    if total_sessions >= 1 and "First Interview Completed" not in existing:
        db.session.add(
            Achievement(
                user_id=user.id,
                title="First Interview Completed",
                description="Completed your first mock interview.",
                icon="star",
            )
        )

    strong_sessions = (
        InterviewSession.query.filter_by(user_id=user.id, status="completed")
        .filter(InterviewSession.total_score >= 80)
        .count()
    )
    if strong_sessions >= 1 and "High Scorer" not in existing:
        db.session.add(
            Achievement(
                user_id=user.id,
                title="High Scorer",
                description="Scored 80+ in an interview.",
                icon="trophy",
            )
        )

    low_filler_sessions = (
        db.session.query(InterviewSession)
        .join(InterviewResponse)
        .filter(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
        .group_by(InterviewSession.id)
        .having(db.func.sum(InterviewResponse.filler_count) <= 2)
        .count()
    )
    if low_filler_sessions >= 1 and "Clear Communicator" not in existing:
        db.session.add(
            Achievement(
                user_id=user.id,
                title="Clear Communicator",
                description="Used almost no filler words in one full interview.",
                icon="chat",
            )
        )


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


@app.route("/")
def home():
    if get_current_user():
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for("signup"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        session.permanent = True
        flash("Account created successfully. You are now logged in.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session.permanent = True
        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/logout-confirm", methods=["GET", "POST"])
@login_required
def logout_confirm():
    if request.method == "POST":
        action = request.form.get("action", "").strip().lower()
        if action == "logout":
            return redirect(url_for("logout"))
        return redirect(url_for("dashboard"))
    return render_template("logout_confirm.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    completed_sessions = (
        InterviewSession.query.filter_by(user_id=user.id, status="completed")
        .order_by(InterviewSession.end_time.desc())
        .all()
    )
    recent_sessions = completed_sessions[:5]

    avg_score = round(sum(s.total_score for s in completed_sessions) / len(completed_sessions), 2) if completed_sessions else 0
    avg_hire = round(sum(s.hire_probability for s in completed_sessions) / len(completed_sessions), 2) if completed_sessions else 0

    progress_labels = [s.end_time.strftime("%d %b") for s in reversed(recent_sessions)]
    progress_scores = [s.total_score for s in reversed(recent_sessions)]
    weakness_counter = Counter()
    for s in completed_sessions:
        for w in json.loads(s.weaknesses or "[]"):
            weakness_counter[w] += 1
    recurring_weaknesses = weakness_counter.most_common(4)

    return render_template(
        "dashboard.html",
        completed_sessions=completed_sessions,
        recent_sessions=recent_sessions,
        avg_score=avg_score,
        avg_hire=avg_hire,
        progress_labels=progress_labels,
        progress_scores=progress_scores,
        badges=user.achievements,
        recurring_weaknesses=recurring_weaknesses,
    )


@app.route("/start", methods=["GET", "POST"])
@login_required
def start_interview():
    if request.method == "POST":
        user = get_current_user()
        profession = request.form.get("profession", "").strip()
        custom_profession = request.form.get("custom_profession", "").strip()
        selected_profession = custom_profession if custom_profession else profession
        interview_type = infer_interview_type_from_profession(selected_profession)
        personality = request.form.get("personality", "friendly").lower()
        language = request.form.get("language", "en").lower()
        total_questions = int(request.form.get("total_questions", 6))

        resume_file = request.files.get("resume")
        resume_filename = None
        extracted_skills = []

        if resume_file and resume_file.filename:
            filename = secure_filename(resume_file.filename)
            resume_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{datetime.utcnow().timestamp()}_{filename}")
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            resume_file.save(resume_path)
            resume_filename = resume_path

            resume_text = extract_text_from_resume(resume_path)
            extracted_skills = find_skills(resume_text)

        personalization_payload = {
            "profession": selected_profession,
            "resume_skills": extracted_skills,
        }

        interview_session = InterviewSession(
            user_id=user.id,
            interview_type=interview_type,
            personality=personality,
            status="ongoing",
            resume_filename=resume_filename,
            language=language,
            total_questions=total_questions,
            personalized_skills=json.dumps(personalization_payload),
        )
        db.session.add(interview_session)
        db.session.commit()

        session[f"active_question_{interview_session.id}"] = None
        session[f"asked_question_ids_{interview_session.id}"] = []
        session[f"last_feedback_{interview_session.id}"] = None
        flash(f"Interview started for {selected_profession or 'selected role'} ({interview_type.capitalize()} mode). Good luck!", "success")
        return redirect(url_for("interview", session_id=interview_session.id))

    return render_template("start_interview.html", profession_groups=PROFESSION_GROUPS)


@app.route("/interview/<int:session_id>", methods=["GET", "POST"])
@login_required
def interview(session_id):
    user = get_current_user()
    interview_session = InterviewSession.query.filter_by(id=session_id, user_id=user.id).first_or_404()

    if interview_session.status == "completed":
        return redirect(url_for("report", session_id=session_id))

    asked_ids_key = f"asked_question_ids_{session_id}"
    active_question_key = f"active_question_{session_id}"
    last_feedback_key = f"last_feedback_{session_id}"

    asked_ids = session.get(asked_ids_key, [])
    response_count = InterviewResponse.query.filter_by(session_id=session_id).count()

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        think_time = float(request.form.get("think_time", 0))

        question_data = session.get(active_question_key)
        personalization_raw = json.loads(interview_session.personalized_skills or "[]")
        if isinstance(personalization_raw, dict):
            resume_skills = personalization_raw.get("resume_skills", [])
            selected_profession = personalization_raw.get("profession", "")
        else:
            resume_skills = personalization_raw
            selected_profession = ""

        if not question_data:
            question_data = get_next_question(
                interview_type=interview_session.interview_type,
                difficulty=get_target_difficulty(session_id),
                excluded_ids=asked_ids,
                skills=resume_skills,
                profession=selected_profession,
                language=interview_session.language,
                personality=interview_session.personality,
            )

        analysis = analyze_answer(answer=answer, question_data=question_data, think_time=think_time)

        response = InterviewResponse(
            session_id=session_id,
            question_text=question_data["display_question"],
            ideal_answer=question_data["ideal_answer"],
            user_answer=answer,
            keywords_json=json.dumps(question_data.get("keywords", [])),
            relevance_score=analysis["relevance_score"],
            sentiment_score=analysis["confidence_score"],
            grammar_score=analysis["grammar_score"],
            clarity_score=analysis["clarity_score"],
            completeness_score=analysis["completeness_score"],
            overall_score=analysis["overall_score"],
            filler_count=analysis["filler_word_count"],
            think_time=think_time,
            difficulty=question_data["difficulty"],
            feedback_json=json.dumps(analysis),
        )
        db.session.add(response)

        user.points += int(max(5, analysis["overall_score"] // 4))
        user.level = max(1, user.points // 100 + 1)
        db.session.commit()

        session[last_feedback_key] = analysis
        asked_ids.append(question_data["id"])
        session[asked_ids_key] = asked_ids

        if response_count + 1 >= interview_session.total_questions:
            finalize_session(interview_session, user)
            db.session.commit()
            flash("Interview completed. Check your detailed report.", "success")
            return redirect(url_for("report", session_id=session_id))

    feedback = session.get(last_feedback_key)

    personalization_raw = json.loads(interview_session.personalized_skills or "[]")
    if isinstance(personalization_raw, dict):
        resume_skills = personalization_raw.get("resume_skills", [])
        selected_profession = personalization_raw.get("profession", "")
    else:
        resume_skills = personalization_raw
        selected_profession = ""

    active_question = get_next_question(
        interview_type=interview_session.interview_type,
        difficulty=get_target_difficulty(session_id),
        excluded_ids=asked_ids,
        skills=resume_skills,
        profession=selected_profession,
        language=interview_session.language,
        personality=interview_session.personality,
    )
    session[active_question_key] = active_question

    progress = InterviewResponse.query.filter_by(session_id=session_id).count()
    return render_template(
        "interview.html",
        interview_session=interview_session,
        question=active_question,
        feedback=feedback,
        progress=progress,
        total_questions=interview_session.total_questions,
    )


def finalize_session(interview_session, user):
    responses = InterviewResponse.query.filter_by(session_id=interview_session.id).all()
    if not responses:
        return

    total_score = round(sum(r.overall_score for r in responses) / len(responses), 2)
    hire_probability = round(compute_hire_probability(responses), 2)

    strengths = []
    weaknesses = []
    tips = []

    avg_relevance = sum(r.relevance_score for r in responses) / len(responses)
    avg_confidence = sum(r.sentiment_score for r in responses) / len(responses)
    avg_grammar = sum(r.grammar_score for r in responses) / len(responses)
    avg_filler = sum(r.filler_count for r in responses) / len(responses)
    avg_think_time = sum(r.think_time for r in responses) / len(responses)

    if avg_relevance >= 70:
        strengths.append("Good relevance and keyword coverage.")
    else:
        weaknesses.append("Answers often miss important keywords from the expected answer.")
        tips.append("Practice structuring answers with role-specific keywords and examples.")

    if avg_confidence >= 60:
        strengths.append("Confident and positive tone throughout answers.")
    else:
        weaknesses.append("Confidence level appears low or uncertain in response tone.")
        tips.append("Use concise, assertive language and avoid overusing uncertain phrases.")

    if avg_grammar >= 70:
        strengths.append("Grammar and sentence quality are generally strong.")
    else:
        weaknesses.append("Grammar issues reduced clarity in multiple answers.")
        tips.append("Use shorter sentences and review tense/subject-verb agreement.")

    if avg_filler <= 2:
        strengths.append("Minimal filler words improved communication clarity.")
    else:
        weaknesses.append("Frequent filler words affected fluency.")
        tips.append("Pause silently instead of using filler words while thinking.")

    if avg_think_time > 12:
        tips.append("Try a 3-part mental framework to reduce long response delays.")

    interview_session.total_score = total_score
    interview_session.hire_probability = hire_probability
    interview_session.strengths = json.dumps(strengths)
    interview_session.weaknesses = json.dumps(weaknesses)
    interview_session.suggestions = json.dumps(tips)
    interview_session.end_time = datetime.utcnow()
    interview_session.status = "completed"
    assign_badges(user)


@app.route("/report/<int:session_id>")
@login_required
def report(session_id):
    user = get_current_user()
    interview_session = InterviewSession.query.filter_by(id=session_id, user_id=user.id).first_or_404()
    responses = InterviewResponse.query.filter_by(session_id=session_id).all()

    dna_profile = build_interview_dna_profile(
        responses,
        interview_type=interview_session.interview_type,
        personality=interview_session.personality,
    )
    skill_gap_heatmap = build_skill_gap_heatmap(responses)
    detailed_rows = []
    for row in responses:
        feedback_payload = json.loads(row.feedback_json or "{}")
        detailed_rows.append({"response": row, "feedback": feedback_payload})

    return render_template(
        "report.html",
        interview_session=interview_session,
        responses=responses,
        detailed_rows=detailed_rows,
        strengths=json.loads(interview_session.strengths or "[]"),
        weaknesses=json.loads(interview_session.weaknesses or "[]"),
        suggestions=json.loads(interview_session.suggestions or "[]"),
        dna_profile=dna_profile,
        skill_gap_heatmap=skill_gap_heatmap,
    )


@app.route("/history")
@login_required
def history():
    user = get_current_user()
    sessions = (
        InterviewSession.query.filter_by(user_id=user.id, status="completed")
        .order_by(InterviewSession.end_time.desc())
        .all()
    )

    total = len(sessions)
    avg_score = round(sum(s.total_score for s in sessions) / total, 2) if total else 0
    avg_hire = round(sum(s.hire_probability for s in sessions) / total, 2) if total else 0
    best_score = round(max((s.total_score for s in sessions), default=0), 2)

    last_30_cutoff = datetime.utcnow() - timedelta(days=30)
    last_30_count = sum(1 for s in sessions if s.end_time and s.end_time >= last_30_cutoff)

    personality_counter = Counter(s.personality for s in sessions)
    most_used_personality = personality_counter.most_common(1)[0][0].capitalize() if personality_counter else "N/A"

    total_answered = sum(InterviewResponse.query.filter_by(session_id=s.id).count() for s in sessions)
    avg_questions_answered = round(total_answered / total, 1) if total else 0

    all_responses = []
    for s in sessions:
        all_responses.extend(InterviewResponse.query.filter_by(session_id=s.id).all())
    history_skill_gaps = build_skill_gap_heatmap(all_responses)[:4]

    return render_template(
        "history.html",
        sessions=sessions,
        total=total,
        avg_score=avg_score,
        avg_hire=avg_hire,
        best_score=best_score,
        last_30_count=last_30_count,
        most_used_personality=most_used_personality,
        avg_questions_answered=avg_questions_answered,
        history_skill_gaps=history_skill_gaps,
    )


@app.route("/brand-fonts")
def brand_fonts():
    return render_template("brand_fonts.html")


@app.route("/api/confidence", methods=["POST"])
@login_required
def confidence_api():
    if cv2 is None:
        return {"supported": False, "confidence": 50, "message": "OpenCV not installed."}

    image = request.files.get("frame")
    if not image:
        return {"supported": False, "confidence": 50, "message": "No frame provided."}, 400

    image_path = os.path.join(app.config["UPLOAD_FOLDER"], f"frame_{datetime.utcnow().timestamp()}.jpg")
    image.save(image_path)

    frame = cv2.imread(image_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    confidence = 65 if len(faces) > 0 else 45
    message = "Face detected. Keep eye contact and posture steady." if len(faces) > 0 else "Face not detected clearly. Adjust camera angle."

    return {"supported": True, "confidence": confidence, "message": message}


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
