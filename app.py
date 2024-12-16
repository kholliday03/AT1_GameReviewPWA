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

@app.route("/") # Redirects to home page
def index():
    return redirect((url_for("home")))

@app.route("/home", defaults={"query": ""}, methods=["POST", "GET"]) # Setting a default value for query when query is empty - required as Flask handles this awkwardly.
@app.route("/home/<query>", methods=["POST", "GET"])    # If user puts something in the search bar
def home(query):
    db = get_db()
    if request.method == "POST":
        query = request.form["game-search"]

    if query:   # Only selects games which match the search
        games = db.execute("SELECT * FROM games WHERE game_title LIKE ? ORDER BY year_released DESC", (f"%{query}%",)).fetchall()
    else:   # Selects all games
        games = db.execute("SELECT * FROM games ORDER BY year_released DESC").fetchall()

    return render_template("index.html", games=games)

@app.route("/login", methods=["POST", "GET"])   # Login page
def login():
    if request.method == "POST":
        username = request.form["username"] # Get username
        password = request.form["password"] # Get password

        db = get_db()
        user = db.execute(
            "SELECT * FROM accounts WHERE username = ?", (username,)    # Select an account which matchest the username
        ).fetchone()

        if user and check_password_hash(user["password"], password):    # If passwords match
            session.clear() # Enter a session
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))   # Go to home page
        flash("Invalid username or password", "error")

    return render_template("login.html")    # Retry login

@app.route("/register", methods=["POST", "GET"])    # Register page
def register():
    if request.method == "POST":
        username = request.form["username"] # Get username
        password = request.form["password"] # Get password

        db = get_db()
        try:
            db.execute(
                "INSERT INTO accounts (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))    # Insert new account information into the database
            )
            db.commit()
            flash("Registration successful! Please log in.", "success")
        except sqlite3.IntegrityError:  # In case username given already exists
            flash("Username already exists! Please try again.", "error")
        return redirect(url_for("login"))   # Redirect to login page
    
    return render_template("register.html")

@app.route("/offline")  # Offline page
def offline():
    response = make_response(render_template('offline.html'))   # Response to service worker
    return response

@app.route("/service-worker.js")    # Service worker
def sw():
    response = make_response(   # Get the service worker from the appropriate directory
        send_from_directory(os.path.join(app.root_path, "static/js"), "service-worker.js")
    )
    return response # Send to offline page

@app.route("/manifest.json")    # Icons for caching
def manifest():
    response = make_response(   # Get the manifest from the appropriate directory
        send_from_directory(os.path.join(app.root_path, "static"), "manifest.json")
    )
    return response # Send to offline page

@app.route("/logout")   # Logout
def logout():
    session.clear() # Clearing session
    return redirect(url_for("home"))    # Redirect to home page

@app.route("/game/<id>")
def game(id):
    db = get_db()
    gamePostData = db.execute(f"SELECT * FROM games WHERE id = ?", (id,)).fetchone()
    postData = db.execute(f"SELECT posts.*, games.*, accounts.* FROM posts JOIN accounts ON posts.user_id=accounts.id JOIN games ON posts.game_id=games.id WHERE games.id = ?", (id,)).fetchall()
    averageRating = db.execute(f"SELECT AVG(posts.rating) AS average FROM posts WHERE posts.game_id = ?", (id,)).fetchone()
    return render_template("game.html", game=gamePostData, posts=postData, averageRating=averageRating)

@app.route("/add_post", methods=["POST"])
def add_post():
    db = get_db()
    try:    # Failsafe for if the user posts a review with no rating, whether deliberate or intentional.
        rating_fix = request.form["rating"]     # Normal rating (1-5 stars)
    except Exception:
        rating_fix = 0  # No rating (0 stars)
    db.execute("INSERT INTO posts (user_id, game_id, title, description, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)", (
        session["user_id"],
        request.form["game_id"],
        request.form["title"],
        request.form["description"],
        rating_fix,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    db.commit()

    flash("Review created.", "success")
    return redirect(url_for("game", id=request.form["game_id"]))    # Redirect to the same game link

@app.route("/delete_post/<int:post_id>", methods=['POST'])
def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()

    flash('Post deleted.', 'success') 
    return redirect(url_for("game", id=request.form["game_id"]))

@app.route("/edit_post/<int:post_id>", methods=["POST"])
def edit_post(post_id):
    db = get_db()
    title = request.form["title"]
    description = request.form["description"]
    try:    # Normal rating 1-5 stars
        rating = request.form["edit-rating"]
    except Exception:   # Rating of 0 if none given
        rating = 0

    db.execute("UPDATE posts SET title = ?, description = ?, rating = ? WHERE id = ?", (title, description, rating, post_id))   # Edit post query
    db.commit()

    flash("Post updated.", "success")
    return redirect(url_for("game", id=request.form["game_id"]))    # Redirect to the same game link

app.run(debug=True, port=5000)