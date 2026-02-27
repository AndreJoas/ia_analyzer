# backend/pages.py
from flask import Blueprint, render_template, session, redirect, url_for
from backend.config import app

@app.route("/")
def home():
 
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    user = session.get("user")

    if not user:
        return redirect(url_for("home"))
    return render_template("dashboard.html", user=user)

@app.route("/chat")
def chat_page():
    user = session.get("user")
    print("SESSION NO CHAT:", session.get("user"))
    print("SECRET NO CHAT:", app.secret_key)
    if not user:
        print("Usuário não autenticado, redirecionando para home.:valor:", user)
        return redirect(url_for("home"))

    return render_template("chat.html", user=user)