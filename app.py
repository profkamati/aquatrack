"""
AquaTrack backend — authentication for the three portals (Citizen,
Municipality, NamWater) and role-gated access to their dashboards.

Run with:
    pip install flask --break-system-packages   (or: pip install -r requirements.txt)
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "aquatrack.db"
STATIC_DIR = BASE_DIR / "static"

VALID_ROLES = {"citizen", "municipality", "namwater"}

# maps each role to the dashboard file it should land on after login,
# and the login page it should bounce back to if not authenticated
ROLE_DASHBOARD = {
    "citizen": "citizen-dashboard.html",
    "municipality": "municipality-dashboard.html",
    "namwater": "namwater-dashboard.html",
}
ROLE_LOGIN_PAGE = {
    "citizen": "citizen.html",
    "municipality": "municipality.html",
    "namwater": "namwater.html",
}

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
app.secret_key = "dev-secret-key-change-this-before-deploying"  # replace for production


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            identifier TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            UNIQUE(role, identifier)
        )
        """
    )
    conn.commit()

    # seed demo staff accounts for municipality + namwater, since those
    # portals don't have self-registration (accounts are issued by an admin)
    demo_accounts = [
        ("municipality", "ops@municipality.gov.na", "demo1234", "Municipality Operations"),
        ("namwater", "ops@namwater.com.na", "demo1234", "NamWater Operations"),
    ]
    for role, identifier, password, name in demo_accounts:
        existing = conn.execute(
            "SELECT id FROM users WHERE role = ? AND identifier = ?", (role, identifier)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (role, identifier, password_hash, name) VALUES (?, ?, ?, ?)",
                (role, identifier, generate_password_hash(password), name),
            )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    role = data.get("role", "")
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    # only citizens can self-register; municipality/namwater accounts
    # are provisioned directly (see seeded demo accounts above)
    if role != "citizen":
        return jsonify(error="Self-registration is only available for citizen accounts."), 403

    if not identifier or not password:
        return jsonify(error="Please fill in all required fields."), 400

    if len(password) < 6:
        return jsonify(error="Password must be at least 6 characters."), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE role = ? AND identifier = ?", (role, identifier)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify(error="An account with that phone number or email already exists."), 409

    conn.execute(
        "INSERT INTO users (role, identifier, password_hash, name) VALUES (?, ?, ?, ?)",
        (role, identifier, generate_password_hash(password), name),
    )
    conn.commit()
    conn.close()

    session["role"] = role
    session["identifier"] = identifier
    session["name"] = name

    return jsonify(redirect=ROLE_DASHBOARD[role]), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    role = data.get("role", "")
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""

    if role not in VALID_ROLES:
        return jsonify(error="Unknown portal."), 400
    if not identifier or not password:
        return jsonify(error="Please fill in all fields."), 400

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE role = ? AND identifier = ?", (role, identifier)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Incorrect login details."), 401

    session["role"] = role
    session["identifier"] = identifier
    session["name"] = user["name"]

    return jsonify(redirect=ROLE_DASHBOARD[role]), 200


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(redirect="index.html"), 200


@app.route("/api/me", methods=["GET"])
def me():
    if "role" not in session:
        return jsonify(authenticated=False), 200
    return jsonify(authenticated=True, role=session["role"], name=session.get("name")), 200


# ---------------------------------------------------------------------------
# Page routes — front page + role-gated dashboards
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


def serve_dashboard(role):
    """Only serve a dashboard if the session role matches; otherwise
    bounce back to that portal's login page."""
    if session.get("role") != role:
        return redirect(ROLE_LOGIN_PAGE[role])
    return send_from_directory(app.static_folder, ROLE_DASHBOARD[role])


@app.route("/citizen-dashboard.html")
def citizen_dashboard():
    return serve_dashboard("citizen")


@app.route("/municipality-dashboard.html")
def municipality_dashboard():
    return serve_dashboard("municipality")


@app.route("/namwater-dashboard.html")
def namwater_dashboard():
    return serve_dashboard("namwater")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
