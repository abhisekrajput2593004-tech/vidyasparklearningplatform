# VidyaSpark — AI Study Resource Recommendation System

VidyaSpark is a Streamlit-based study companion for students preparing for school, university, and competitive exams. It brings curated study resources, YouTube searches, an AI doubt solver, and study planning tools into one app.

## Features

- Resources organized across ten streams: B.Tech CSE, Mechanical, Electrical, Class 10/12 Boards, JEE, NEET, UPSC, SSC, Banking/Railway, and SSB.
- Searchable study resources with links to subject-related YouTube video results and related channel results.
- Gemini-powered AI Doubt Solver with English and Hindi responses.
- 50 mock tests: five tests for each stream, with 15 questions per test and a suggested 20-minute duration. Answers start unselected; students must answer every question before submitting and can review correct answers afterward.
- Personal study planner with completion tracking.
- Student review and feedback form.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements_final.txt`
- A Gemini API key for AI features

## Setup

1. Open a terminal in the project folder.
2. (Optional) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the dependencies:

   ```powershell
   python -m pip install -r requirements_final.txt
   ```

4. Add your Gemini API key to `.streamlit/secrets.toml`:

   ```toml
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
   ```

   Keep this file private. It is excluded by `.gitignore`.

## Run the app

From the project folder, run:

```powershell
python -m streamlit run vidyaspark_professional.py
```

Streamlit will print a local address to open in your browser, usually `http://localhost:8501`.

## Project files

- `vidyaspark_professional.py` — Streamlit application and study content
- `requirements_final.txt` — Python dependencies
- `.streamlit/secrets.toml` — Local Gemini API key configuration (not committed)
- `.gitignore` — Excludes secrets and Python-generated files
