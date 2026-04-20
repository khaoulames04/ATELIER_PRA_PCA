import os
import sqlite3
import time
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")


@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )


@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)


@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)


# ---------- NEW ROUTE /status ----------
@app.get("/status")
def status():
    init_db()

    # 📊 nombre d’événements
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    count_events = cur.fetchone()[0]
    conn.close()

    # 📁 backups
    backup_dir = "/backup"
    files = []

    if os.path.exists(backup_dir):
        files = os.listdir(backup_dir)

    if files:
        latest_file = max(
            files,
            key=lambda f: os.path.getmtime(os.path.join(backup_dir, f))
        )
        latest_path = os.path.join(backup_dir, latest_file)
        backup_age = int(time.time() - os.path.getmtime(latest_path))
    else:
        latest_file = None
        backup_age = None

    return jsonify({
        "count": count_events,
        "last_backup_file": latest_file,
        "backup_age_seconds": backup_age
    })


# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)