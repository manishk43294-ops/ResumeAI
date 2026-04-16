# AI Resume Analyzer

A Streamlit resume parsing and recommendation app. Upload a PDF resume to extract key profile details, generate skill insights, suggest courses, and view admin analytics.

## Features
- Upload and parse PDF resumes with `pyresparser` and `pdfminer3`
- Extract name, email, mobile, skills, degree, page count, and resume score
- Recommend training courses and interview preparation videos
- Admin dashboard for user data, feedback, and charts
- Saves submissions to a local MySQL database

## Contents
- `App/` — Streamlit application source code and UI assets
- `pyresparser/` — local resume parser module
- `requirements.txt` — Python package dependencies
- `README.md` — project documentation
- `LICENSE` — project license

## Setup
1. Install Python 3.9+ and MySQL.
2. Clone the repository.
3. Create and activate a virtual environment:
   ```bash
   python -m venv venvapp
   venvapp\Scriptsctivate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Download the spaCy English model:
   ```bash
   python -m spacy download en_core_web_sm
   ```
6. Run the application:
   ```bash
   streamlit run App/App.py
   ```

## MySQL
The app uses a MySQL database named `cv`. It will create the database and required tables automatically on first run. Update credentials in `App/App.py` if your MySQL username or password differs.

## Notes
- Sample resumes are included under `App/Uploaded_Resumes/`.
- The local `pyresparser/` package is included to ensure consistent resume parsing.
- If geolocation fails, ensure your internet connection is active.

## Author
- `manishk43294-ops`
