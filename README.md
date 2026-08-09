# AquaTrack — Backend

Flask backend that handles login/registration for the three AquaTrack
portals (Citizen, Municipality, NamWater) and serves the matching
dashboard only to a signed-in user of that role.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. That serves
`index.html`, and every link on the site (logins, dashboards, "Home"
buttons) works from there — no need to open the HTML files directly.

## How it works

- `aquatrack.db` (SQLite) is created automatically the first time you
  run the app, with a `users` table storing `role`, `identifier`,
  a hashed password, and `name`.
- **Citizens** can self-register from `citizen.html` (the "Register as
  a citizen" link switches the form into sign-up mode).
- **Municipality** and **NamWater** accounts are staff-provisioned —
  there's no public sign-up for them. Two demo accounts are seeded
  automatically so you can log in and test both portals:
  - Municipality: `ops@municipality.gov.na` / `demo1234`
  - NamWater: `ops@namwater.com.na` / `demo1234`
- Need more staff accounts? See "Adding more staff accounts" below.
- Sessions are handled with Flask's built-in signed cookies
  (`app.secret_key`) — change that key before deploying anywhere real.
- Each dashboard route (`/citizen-dashboard.html`, etc.) checks the
  session's role before serving the file; if it doesn't match, it
  redirects back to that portal's login page instead.

## Adding more staff accounts

Municipality and NamWater don't have public sign-up on purpose (real
staff accounts should be issued by an admin, not self-registered).
Two demo accounts are seeded automatically — see below — but if you
want to create more, run:

```bash
python create_staff_account.py
```

It'll ask for the role, work email/ID, name, and a password, and add
it straight to `aquatrack.db`.

## Uploading this to GitHub

1. **Create the repo on GitHub** — go to github.com, click "New
   repository", name it (e.g. `aquatrack`), leave it empty (no
   README/license), and click "Create repository".
2. **From this folder**, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit — AquaTrack backend and frontend"
   git branch -M main
   git remote add origin https://github.com/<your-username>/aquatrack.git
   git push -u origin main
   ```
   Replace `<your-username>` with your GitHub username. GitHub will
   prompt you to sign in (or use a personal access token) the first
   time you push.
3. **`.gitignore` is already included**, so `aquatrack.db` and
   `__pycache__/` won't be committed — good, since the database gets
   recreated automatically every time `app.py` runs.
4. Anyone who clones the repo can then run it the same way:
   ```bash
   git clone https://github.com/<your-username>/aquatrack.git
   cd aquatrack
   pip install -r requirements.txt
   python app.py
   ```



- Passwords are hashed with Werkzeug's `generate_password_hash` /
  `check_password_hash` — never stored in plain text.
- This is a demo-scoped backend (single SQLite file, dev secret key,
  no rate limiting, no email verification). Fine for a hackathon
  application/demo; would need hardening before any real deployment.
