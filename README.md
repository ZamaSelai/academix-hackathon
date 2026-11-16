# AcademiX

**Verified human intelligence for the AI era.**

AcademiX is a hackathon prototype of a platform where students upload original academic essays, receive an automated originality check, and earn credit in a virtual wallet based on word count. The idea: give students flexible income while building a pool of verified, original academic writing.

> **Status:** hackathon MVP (48-hour build). See [What works and what doesn't](#what-works-and-what-doesnt) for an honest breakdown.

**Hackathon:** STADIO SOIT Hackathon 2026 (48-hour, AI for real business problems)

**My role:** Lead developer. I built the main application and the entire backend (Flask API, PDF processing and the originality-checking logic).

**Team:** Team of 5

## The problem

- Many students are unemployed or underemployed and have few options for quick, flexible income.
- AI models need fresh, original, well-sourced writing, and generated content is increasingly feeding back into training data.

## How it works

1. **Register** as a student (or patron) and log in.
2. **Upload** an essay as a PDF.
3. The backend extracts the text and runs checks:
   - **Originality / similarity:** sentence embeddings (`all-MiniLM-L6-v2` from Sentence-Transformers) compared against a small set of cached reference texts using cosine similarity.
   - **Academic tone:** keyword-based score (words like "analysis", "evidence", "furthermore").
   - **Published-content check:** looks for publisher and journal markers (DOI, ISBN, "All rights reserved", etc.).
   - **Word count:** used to calculate earnings at R0.02 per word.
4. **Outcome:** verified essays credit the student's wallet; high-similarity or published content adds a strike (three-strike policy).

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python, Flask, Flask-CORS |
| AI / NLP | Sentence-Transformers (`all-MiniLM-L6-v2`), NumPy |
| PDF handling | PyPDF2 |
| Front end | HTML, CSS, vanilla JavaScript (single-page app) |
| Storage | JSON file (`users.json`) for the prototype |

## Run it locally

```bash
git clone https://github.com/ZamaSelai/academix-hackathon.git
cd academix-hackathon

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python app.py
```

Then open `http://localhost:5001`. The first run downloads the Sentence-Transformers model, so it needs an internet connection and may take a minute.

## What works and what doesn't

**Built and working**
- Account registration and login with sessions
- PDF upload and text extraction
- Semantic similarity scoring with Sentence-Transformers
- Academic-tone scoring, word count and earnings calculation
- Strike tracking and wallet balance

**Simulated or demo-only in this build**
- Parts of the dashboard (marketplace, patron stats, admin view) use demo data.
- Withdrawals are simulated; no real payment integration.
- The similarity check compares against only 5 sample sentences, not a real web index.

**Pitched but not built**
- Vector database (Pinecone or FAISS) for storing verified essays
- LLM-based review of tone, structure and sources
- Real payments (e.g. Stripe Connect)

## Known limitations

This was built in a hackathon, so some shortcuts were taken. These are the first things I'd fix:

- Passwords are hashed with plain SHA-256 and no salt. They should use `bcrypt` or `argon2`.
- The Flask secret key is hardcoded. It should come from an environment variable.
- User data lives in a JSON file instead of a database.
- The published-content check treats common words like "Introduction" and "References" as markers, so it can wrongly flag genuine student essays.
- The `/api/withdraw` route is defined after `app.run()`, so it never registers.
- Registration collects ID numbers; a real version would need proper data protection (POPIA) handling.

## Roadmap

- [ ] Move to a real database (SQLite or PostgreSQL)
- [ ] Secure authentication (salted password hashing, environment-based secrets)
- [ ] Replace the sample reference set with a real vector index
- [ ] Improve the published-content detection
- [ ] Add automated tests

## Author

**Zamantungwa Selai**, Information Systems student (STADIO) and Junior Business Analyst Intern.
[LinkedIn](https://www.linkedin.com/in/zamantungwa-selai-692076257) · zamaselai@gmail.com
