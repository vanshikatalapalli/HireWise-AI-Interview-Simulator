# AI-Based Smart Interview Simulator (Flask + MySQL)

An advanced full-stack interview practice platform with AI-driven answer analysis, adaptive interview flow, resume-based personalization, and performance tracking.

## Features

- User authentication (signup/login/logout)
- Interview modes: HR, Technical, Mixed
- AI interviewer personalities: Friendly, Strict, Technical
- Dynamic question generation from a sample question bank
- Resume upload with skill extraction for personalized questions
- Text and voice-based answer support (browser speech recognition)
- AI answer analysis:
  - Keyword relevance score
  - Sentiment-based confidence score
  - Grammar quality and correction suggestion
  - Clarity and completeness scoring
  - Filler word detection (`um`, `uh`, `like`, etc.)
  - Think-time analyzer (delay before response)
- Adaptive interview difficulty based on performance
- Final report with:
  - Total score
  - Strengths and weaknesses
  - Improvement tips
  - Hire probability score
- Gamification:
  - Points and levels
  - Achievement badges
- Progress dashboard and interview history
- Multi-language question display (English/Hindi)
- Optional webcam confidence check endpoint using OpenCV

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python + Flask
- Database: MySQL (via Flask-SQLAlchemy + PyMySQL)
- AI/NLP: NLTK, TextBlob, spaCy (ready for extension)
- Optional: SpeechRecognition (browser API), OpenCV

## Project Structure

```text
aiinterview/
├── app.py
├── models.py
├── requirements.txt
├── .env.example
├── database.sql
├── README.md
├── ai/
│   ├── __init__.py
│   ├── adaptive.py
│   ├── analyzer.py
│   ├── questions.py
│   ├── company_questions.py
│   └── resume_parser.py
├── data/
│   └── question_bank.json
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js
│       └── interview.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   ├── dashboard.html
│   ├── start_interview.html
│   ├── interview.html
│   ├── report.html
│   └── history.html
└── uploads/
```

## Setup (MySQL + Flask)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create MySQL database (XAMPP phpMyAdmin or MySQL CLI):
   ```sql
   SOURCE database.sql;
   ```

3. Configure environment variables (or set in system env):
   - `SECRET_KEY`
   - `DB_HOST`
   - `DB_PORT`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`

4. Run the app:
   ```bash
   python app.py
   ```

5. Open:
   - `http://127.0.0.1:5000`

## Notes

- SQLAlchemy auto-creates tables at startup (`init_db()`).
- Voice input works on compatible browsers via Web Speech API.
- Webcam confidence check requires OpenCV and camera permissions.
- Resume parser currently supports `.txt` and `.pdf`.
