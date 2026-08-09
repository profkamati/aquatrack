"""
Create additional Municipality or NamWater staff accounts.

Usage:
    python create_staff_account.py

Follow the prompts. This talks directly to the same aquatrack.db
that app.py uses, so run it from the same folder as app.py.
"""

import sqlite3
from pathlib import Path
from getpass import getpass

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).parent / "aquatrack.db"


def main():
    print("AquaTrack — create a staff account\n")

    role = ""
    while role not in ("municipality", "namwater"):
        role = input("Role (municipality / namwater): ").strip().lower()

    identifier = input("Work email or staff/employee ID: ").strip()
    name = input("Full name: ").strip()
    password = getpass("Password (min 6 characters): ")

    if len(password) < 6:
        print("Password must be at least 6 characters. Try again.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

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

    existing = conn.execute(
        "SELECT id FROM users WHERE role = ? AND identifier = ?", (role, identifier)
    ).fetchone()
    if existing:
        print(f"\nAn account already exists for {identifier} ({role}).")
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (role, identifier, password_hash, name) VALUES (?, ?, ?, ?)",
        (role, identifier, generate_password_hash(password), name),
    )
    conn.commit()
    conn.close()

    print(f"\nCreated {role} account for {identifier}. You can log in with it now.")


if __name__ == "__main__":
    main()
