from flask import Flask, render_template, request, redirect
import sqlite3
import requests
import time
from datetime import datetime

app = Flask(__name__)
DB_NAME = "uptimebuddy.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS checks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url_id INTEGER,
                  status TEXT,
                  status_code INTEGER,
                  response_time REAL,
                  checked_at TEXT,
                  FOREIGN KEY(url_id) REFERENCES urls(id))''')
    conn.commit()
    conn.close()

def check_url(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        elapsed = round((time.time() - start) * 1000, 2)  # ms
        status = "UP" if r.status_code < 400 else "DOWN"
        return status, r.status_code, elapsed
    except requests.RequestException:
        return "DOWN", 0, 0

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, url FROM urls")
    urls = c.fetchall()

    results = []
    for url_id, url in urls:
        c.execute('''SELECT status, status_code, response_time, checked_at
                     FROM checks WHERE url_id=? ORDER BY id DESC LIMIT 1''', (url_id,))
        last_check = c.fetchone()
        results.append({
            "id": url_id,
            "url": url,
            "status": last_check[0] if last_check else "NOT CHECKED",
            "status_code": last_check[1] if last_check else "-",
            "response_time": last_check[2] if last_check else "-",
            "checked_at": last_check[3] if last_check else "-"
        })
    conn.close()
    return render_template("index.html", results=results)

@app.route("/add", methods=["POST"])
def add_url():
    url = request.form.get("url")
    if url:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO urls (url) VALUES (?)", (url,))
        conn.commit()
        conn.close()
    return redirect("/")

@app.route("/check/<int:url_id>")
def check_single(url_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT url FROM urls WHERE id=?", (url_id,))
    row = c.fetchone()
    if row:
        status, code, resp_time = check_url(row[0])
        c.execute('''INSERT INTO checks (url_id, status, status_code, response_time, checked_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  (url_id, status, code, resp_time, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:url_id>")
def delete_url(url_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM urls WHERE id=?", (url_id,))
    c.execute("DELETE FROM checks WHERE url_id=?", (url_id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)