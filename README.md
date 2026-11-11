# JobScope

JobScope is a Streamlit career toolkit for discovering job opportunities and preparing application materials. It combines job search, resume analysis, resume-to-job matching, mock interviews, and resume bullet rewriting in one app.

## Features

- **Job search:** Find roles by keyword and location, then save interesting listings.
- **Resume Lab:** Extract text from PDF and DOCX resumes and score a resume against a target role.
- **Top Matches:** Rank searched or saved jobs by semantic similarity to your resume.
- **AI Mock Interview:** Practice role-specific questions and get feedback on your answers.
- **Resume Rewriter:** Improve resume bullets for a target role while preserving the facts in the original text.
- **Job insights:** Explore trends in search results.

## Requirements

- Python 3.10 or later
- API keys for Jooble, Groq, and Google Gemini (features that use each service require its corresponding key)

## Setup

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/<your-username>/<your-repository>.git
   cd <your-repository>
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, you can invoke the environment's Python directly as `.\.venv\Scripts\python.exe`.

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Configure API keys. Create `.streamlit/secrets.toml` and add your keys:

   ```toml
   JOOBLE_API_KEY = "your-jooble-api-key"
   GROQ_API_KEY = "your-groq-api-key"
   GEMINI_API_KEY = "your-gemini-api-key"
   ```

   Keep this file private. It is excluded from Git by `.gitignore`; never commit or share API keys.

5. Start the app:

   ```powershell
   streamlit run app.py
   ```

   Streamlit will print a local URL to open in your browser.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Project structure

```text
app.py              Streamlit home page
pages/              Search, resume, matching, interview, insights, and saved-job pages
utils/              API clients, resume extraction, storage, and shared UI helpers
tests/              Automated tests
requirements.txt    Python dependencies
```

## Data and privacy

Saved jobs and activity are stored locally in `saved_jobs.json` and `activity.json`. Do not commit personal resumes, API keys, or other private data. Resume text and job descriptions used with AI features are sent to the configured Groq or Gemini service for processing.
