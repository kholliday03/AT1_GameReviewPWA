from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_from_directory 
import sqlite3 
import os 
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename 
from datetime import datetime 

app = Flask(__name__)
app.secret_key = "SftEng-PWA-AT1"

def get_db(): 
    db = sqlite3.connect('database/database.db') 
    db.row_factory = sqlite3.Row 
    return db

@app.route("/")
def index():
    return redirect((url_for("home")))

@app.route("/home", defaults={"query": ""}, methods=["POST", "GET"]) # From ChatGPT - Setting a default value for query when query is empty - required as Flask handles this awkwardly.
@app.route("/home/<query>", methods=["POST", "GET"])
def home(query):
    db = get_db()
    if request.method == "POST":
        query = request.form["game-search"]

    if query:
        games = db.execute("SELECT * FROM games WHERE game_title LIKE ? ORDER BY year_released DESC", (f"%{query}%",)).fetchall()
    else:
        games = db.execute("SELECT * FROM games ORDER BY year_released DESC").fetchall()

    return render_template("index.html", games=games)

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
    return redirect(url_for("home"))

@app.route("/game/<id>")
def game(id):
    db = get_db()
    try:
        gamePostData = db.execute(f"SELECT posts.*, games.* FROM posts JOIN games ON posts.game_id=games.id WHERE games.id = {id}").fetchall()
        rows = db.execute("SELECT COUNT(*) FROM posts JOIN games ON posts.game_id = games.id WHERE games.id = ?", (id,)).fetchone()[0]
        if rows == 0:   # Alternative query in case a website has no reviews.
            gamePostData = db.execute(f"SELECT * FROM games WHERE id = ?", (id,)).fetchone()
        return render_template("game.html", game=gamePostData)
    except Exception:
        flash("Error: Invalid Game ID!", "error")
        return redirect(url_for("index"))

@app.route("/add_entry", methods=["POST"])
def add_entry():
    db = get_db()
    db.execute("INSERT INTO posts (user_id, game_id, title, description, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)", (
        session["user_id"],
        request.form["game_id"],
        request.form["title"],
        request.form["description"],
        request.form["rating"],
        datetime.now().timestamp()
    ))
    db.commit()

    flash("Review created.")
    return redirect(url_for("game", id=id))

app.run(debug=True, port=5000)