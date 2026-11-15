# KeySprint — Typing Speed Test

A full-stack typing practice website built with Flask, HTML, CSS, JavaScript and Supabase.

## Features
- User registration and login with Werkzeug password hashing
- Flask sessions and CSRF protection
- 60-second typing test
- WPM and accuracy calculations
- Supabase-backed test history
- CRUD: create test records, read dashboard history, update session notes, delete records
- Third-party daily quote API with a local fallback
- Responsive interface

## 1. Requirements
Install Python 3.11 or newer. Create a Supabase account and project.

## 2. Set up Supabase
1. Open your Supabase project.
2. Open **SQL Editor**.
3. Paste the contents of `schema.sql` and click **Run**.
4. Open **Project Settings → API** and copy the Project URL and service-role key.
5. Keep the service-role key private. It belongs only in the server environment.

## 3. Run locally (Windows PowerShell)
Open a terminal in this project folder and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder values:
- `FLASK_SECRET_KEY`: use a long random secret
- `SUPABASE_URL`: your project URL
- `SUPABASE_SERVICE_ROLE_KEY`: your service-role key

Then start the website:

```powershell
python app.py
```

Open http://127.0.0.1:5000

## 4. Publish on GitHub
1. Create a new **public** GitHub repository.
2. Make sure `.env` is not included. The `.gitignore` file protects it.
3. Upload the project files (including `.gitignore`, `schema.sql`, and `README.md`).
4. Never upload your Supabase service-role key or Flask secret key.

## 5. Deploy on Vercel
1. Import the GitHub repository at https://vercel.com/new.
2. Vercel should detect the Flask app from `app.py`.
3. In Vercel Project → Settings → Environment Variables, add:
   - `FLASK_SECRET_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `FLASK_ENV` = `production`
4. Redeploy after adding the variables.
5. Open the deployment URL and test signup, login, saving a test, editing a note, and deleting a test.

The `public/static/` folder is included for Vercel's static asset hosting; the matching `static/` folder is used when running Flask locally.

Vercel's Flask guide: https://vercel.com/kb/guide/ship-a-flask-app-on-vercel

## Important security notes
- Passwords are stored as salted password hashes, never as plain text.
- The Supabase service-role key is server-side only. Do not expose it in frontend files.
- Database queries for test history, edits and deletions are scoped to the signed-in user's ID.
- CSRF protection is enabled for forms.
- For a production launch with real users, add email verification, password reset, rate limiting, and a stricter account-management flow.

## Project description for submission
**KeySprint** is a web-based typing speed assessment platform designed for students and individuals who want to improve their typing speed and accuracy. Users can create an account, log in securely, complete timed typing tests, and track their performance through a personal dashboard. The Flask backend handles authentication and application routes, while Supabase stores user accounts and typing-test records. Each record is linked to its owner, allowing users to view their own history, update session notes, and delete previous attempts. Passwords are protected using secure hashing, and Flask sessions maintain authenticated access.
