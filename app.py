from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_from_directory 
import sqlite3 
import os 
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename 
from datetime import datetime 

app = Flask(__name__)

@app.route("/")
def base():
    return render_template("base.html")

app.run(debug=True, port=5000)