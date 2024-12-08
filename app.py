from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_from_directory 
import sqlite3 
import os 
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename 
from datetime import datetime 

app = Flask(__name__)
app.secret_key = "SftEng-PWA-AT1"

UPLOAD_FOLDER = 'static/uploads' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db(): 
    db = sqlite3.connect('database/database.db') 
    db.row_factory = sqlite3.Row 
    return db

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM accounts WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Invalid username or password", "error")

    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        try:
            db.execute(
                "INSERT INTO accounts (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            db.commit()
            flash("Registration successful! Please log in.", "success")
        except sqlite3.IntegrityError:
            flash("Username already exists! Please try again.", "error")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/offline")
def offline():
    response = make_response(render_template('offline.html'))
    return response

@app.route("/service-worker.js")
def sw():
    response = make_response(
        send_from_directory(os.path.join(app.root_path, "static/js"), "service-worker.js")
    )
    return response

@app.route("/manifest.json")
def manifest():
    response = make_response(
        send_from_directory(os.path.join(app.root_path, "static"), "manifest.json")
    )
    return response

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

app.run(debug=True, port=5000)