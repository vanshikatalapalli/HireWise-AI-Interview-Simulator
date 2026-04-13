from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship("InterviewSession", backref="user", lazy=True)
    achievements = db.relationship("Achievement", backref="user", lazy=True)


class InterviewSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    interview_type = db.Column(db.String(20), nullable=False)
    personality = db.Column(db.String(20), nullable=False, default="friendly")
    language = db.Column(db.String(10), nullable=False, default="en")
    total_questions = db.Column(db.Integer, default=6)
    resume_filename = db.Column(db.String(255))
    personalized_skills = db.Column(db.Text)
    status = db.Column(db.String(20), default="ongoing")
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_score = db.Column(db.Float, default=0)
    hire_probability = db.Column(db.Float, default=0)
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    suggestions = db.Column(db.Text)

    responses = db.relationship("InterviewResponse", backref="session", lazy=True)


class InterviewResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_session.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    ideal_answer = db.Column(db.Text)
    user_answer = db.Column(db.Text, nullable=False)
    keywords_json = db.Column(db.Text)
    relevance_score = db.Column(db.Float, default=0)
    sentiment_score = db.Column(db.Float, default=0)
    grammar_score = db.Column(db.Float, default=0)
    clarity_score = db.Column(db.Float, default=0)
    completeness_score = db.Column(db.Float, default=0)
    overall_score = db.Column(db.Float, default=0)
    filler_count = db.Column(db.Integer, default=0)
    think_time = db.Column(db.Float, default=0)
    difficulty = db.Column(db.String(20), default="medium")
    feedback_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), default="badge")
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
