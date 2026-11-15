import os
import random
import time
from datetime import datetime, timezone
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from supabase import create_client
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 7
csrf = CSRFProtect(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

PASSAGES = [
    "Python is a popular programming language used by people around the world. It is approachable for beginners and powerful enough for professionals. Programming can help people solve problems, build useful tools, and express creative ideas.",
    "The human brain is an extraordinary organ. It helps us think, learn, remember, and understand the world around us. Curiosity, practice, rest, and healthy routines all support the learning process.",
    "Technology has transformed the way people communicate, study, and work. Digital tools make information easier to access and help people collaborate across long distances. Using technology thoughtfully helps us benefit from it.",
    "Reading opens a door to new ideas and perspectives. Every book offers an opportunity to explore unfamiliar places, understand different experiences, and develop a stronger imagination."
]

def database_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if supabase is None:
            flash("The database is not configured yet. Add your Supabase environment variables.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def current_user():
    if not supabase or "user_id" not in session:
        return None
    try:
        result = supabase.table("users").select("id, name, email").eq("id", session["user_id"]).single().execute()
        return result.data
    except Exception:
        session.clear()
        return None

def calculate_results(original_text, typed_text, duration):
    original_words = original_text.split()
    typed_words = typed_text.split()
    correct = sum(1 for i, word in enumerate(typed_words)
                  if i < len(original_words) and word == original_words[i])
    minutes = max(duration, 1) / 60
    wpm = correct / minutes
    accuracy = (correct / max(len(typed_words), 1)) * 100
    return round(wpm, 1), round(accuracy, 1), correct, len(typed_words)

@app.context_processor
def inject_user():
    return {"logged_in_user": current_user()}

@app.route("/")
def index():
    quote = "Small steps every day lead to meaningful progress."
    try:
        response = requests.get("https://api.quotable.io/random?maxLength=100", timeout=3)
        if response.ok:
            data = response.json()
            quote = data.get("content", quote)
    except requests.RequestException:
        pass
    return render_template("index.html", quote=quote)

@app.route("/signup", methods=["GET", "POST"])
@database_required
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "error")
            return render_template("signup.html")
        try:
            existing = supabase.table("users").select("id").eq("email", email).execute()
            if existing.data:
                flash("An account with that email already exists.", "error")
                return render_template("signup.html")
            created = supabase.table("users").insert({
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password)
            }).select("id, name, email").execute()
            user = created.data[0]
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session.permanent = True
            flash("Your account is ready. Welcome!", "success")
            return redirect(url_for("dashboard"))
        except Exception:
            app.logger.exception("Signup failed")
            flash("We couldn't create your account. Check your database setup and try again.", "error")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
@database_required
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        try:
            result = supabase.table("users").select("id, name, email, password_hash").eq("email", email).limit(1).execute()
            user = result.data[0] if result.data else None
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Email or password is incorrect.", "error")
                return render_template("login.html")
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session.permanent = True
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        except Exception:
            app.logger.exception("Login failed")
            flash("Login is temporarily unavailable. Please try again.", "error")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
@database_required
def dashboard():
    try:
        rows = (supabase.table("typing_tests").select("*")
                .eq("user_id", session["user_id"])
                .order("created_at", desc=True).limit(100).execute().data)
    except Exception:
        app.logger.exception("Dashboard read failed")
        rows = []
        flash("We couldn't load your statistics right now.", "error")
    total = len(rows)
    average_wpm = round(sum(float(r.get("wpm", 0)) for r in rows) / total, 1) if total else 0
    best_wpm = max((float(r.get("wpm", 0)) for r in rows), default=0)
    average_accuracy = round(sum(float(r.get("accuracy", 0)) for r in rows) / total, 1) if total else 0
    return render_template("dashboard.html", tests=rows, total=total,
                           average_wpm=average_wpm, best_wpm=round(best_wpm, 1),
                           average_accuracy=average_accuracy)

@app.route("/test")
@login_required
def typing_test():
    return render_template("test.html", passage=random.choice(PASSAGES))

@app.route("/save-test", methods=["POST"])
@login_required
@database_required
def save_test():
    passage = request.form.get("passage", "")
    typed_text = request.form.get("typed_text", "")
    notes = request.form.get("notes", "").strip()[:250]
    try:
        duration = max(1, min(float(request.form.get("duration", "1")), 3600))
    except ValueError:
        duration = 1
    if not passage or len(passage) > 2000 or len(typed_text) > 5000:
        flash("The test data was invalid. Please try again.", "error")
        return redirect(url_for("typing_test"))
    wpm, accuracy, correct, total = calculate_results(passage, typed_text, duration)
    try:
        supabase.table("typing_tests").insert({
            "user_id": session["user_id"],
            "passage": passage,
            "typed_text": typed_text,
            "duration_seconds": round(duration, 2),
            "wpm": wpm,
            "accuracy": accuracy,
            "correct_words": correct,
            "total_words": total,
            "notes": notes
        }).execute()
        flash("Your result has been saved!", "success")
        return redirect(url_for("dashboard"))
    except Exception:
        app.logger.exception("Saving test failed")
        flash("We couldn't save your result. Please try again.", "error")
        return redirect(url_for("typing_test"))

@app.route("/test/<test_id>/edit", methods=["POST"])
@login_required
@database_required
def edit_test(test_id):
    notes = request.form.get("notes", "").strip()[:250]
    try:
        supabase.table("typing_tests").update({"notes": notes}).eq("id", test_id).eq("user_id", session["user_id"]).execute()
        flash("Your note has been updated.", "success")
    except Exception:
        app.logger.exception("Updating test failed")
        flash("We couldn't update that result.", "error")
    return redirect(url_for("dashboard"))

@app.route("/test/<test_id>/delete", methods=["POST"])
@login_required
@database_required
def delete_test(test_id):
    try:
        supabase.table("typing_tests").delete().eq("id", test_id).eq("user_id", session["user_id"]).execute()
        flash("Test record deleted.", "success")
    except Exception:
        app.logger.exception("Deleting test failed")
        flash("We couldn't delete that result.", "error")
    return redirect(url_for("dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(_error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") != "production")
