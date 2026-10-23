from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-public-use")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "maternity_care.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Patients (
                PatientID INTEGER PRIMARY KEY AUTOINCREMENT,
                FirstName TEXT NOT NULL,
                LastName TEXT NOT NULL,
                DOB TEXT NOT NULL,
                BloodType TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Pregnancies (
                PregnancyID INTEGER PRIMARY KEY AUTOINCREMENT,
                PatientID INTEGER NOT NULL,
                LMP TEXT NOT NULL,
                EDD TEXT,
                Status TEXT DEFAULT 'Active',
                FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Visits (
                VisitID INTEGER PRIMARY KEY AUTOINCREMENT,
                PregnancyID INTEGER NOT NULL,
                VisitDate TEXT NOT NULL,
                Weight TEXT,
                BP TEXT,
                FHR TEXT,
                Notes TEXT,
                FOREIGN KEY (PregnancyID) REFERENCES Pregnancies(PregnancyID) ON DELETE CASCADE
            )
        """)

@app.route("/")
def index():
    with get_db() as conn:
        patients = conn.execute("""
            SELECT p.PregnancyID, pt.FirstName || ' ' || pt.LastName AS Name,
                   pt.DOB, pt.BloodType, p.LMP, p.EDD
            FROM Pregnancies p JOIN Patients pt ON p.PatientID = pt.PatientID
            WHERE p.Status = 'Active'
            ORDER BY p.PregnancyID DESC
        """).fetchall()
    return render_template("index.html", patients=patients, blood_types=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

@app.route("/register", methods=["POST"])
def register():
    fn = request.form.get("first_name", "").strip()
    ln = request.form.get("last_name", "").strip()
    dob = request.form.get("dob", "").strip()
    blood = request.form.get("blood_type", "").strip()
    lmp = request.form.get("lmp", "").strip()

    if not all([fn, ln, dob, lmp]):
        flash("First name, last name, date of birth and LMP are required.", "error")
        return redirect(url_for("index"))
    try:
        datetime.strptime(dob, "%Y-%m-%d")
        lmp_date = datetime.strptime(lmp, "%Y-%m-%d")
        edd = (lmp_date + timedelta(days=280)).strftime("%Y-%m-%d")
    except ValueError:
        flash("Please enter valid dates.", "error")
        return redirect(url_for("index"))

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO Patients (FirstName, LastName, DOB, BloodType) VALUES (?, ?, ?, ?)",
            (fn, ln, dob, blood)
        )
        conn.execute(
            "INSERT INTO Pregnancies (PatientID, LMP, EDD) VALUES (?, ?, ?)",
            (cur.lastrowid, lmp, edd)
        )
    flash(f"Patient registered successfully. Estimated delivery date: {edd}", "success")
    return redirect(url_for("index"))

@app.route("/visits")
def visits():
    selected_id = request.args.get("pregnancy_id", type=int)
    with get_db() as conn:
        pregnancies = conn.execute("""
            SELECT p.PregnancyID, pt.FirstName || ' ' || pt.LastName AS Name
            FROM Pregnancies p JOIN Patients pt ON p.PatientID = pt.PatientID
            WHERE p.Status = 'Active' ORDER BY pt.LastName, pt.FirstName
        """).fetchall()
        history = []
        selected = None
        if selected_id:
            selected = conn.execute("""
                SELECT p.PregnancyID, pt.FirstName || ' ' || pt.LastName AS Name
                FROM Pregnancies p JOIN Patients pt ON p.PatientID = pt.PatientID
                WHERE p.PregnancyID = ?
            """, (selected_id,)).fetchone()
            if selected:
                history = conn.execute("""
                    SELECT VisitID, VisitDate, Weight, BP, FHR, Notes
                    FROM Visits WHERE PregnancyID = ? ORDER BY VisitDate DESC, VisitID DESC
                """, (selected_id,)).fetchall()
    return render_template("visits.html", pregnancies=pregnancies, selected_id=selected_id, selected=selected, history=history)

@app.route("/visits/add", methods=["POST"])
def add_visit():
    pregnancy_id = request.form.get("pregnancy_id", type=int)
    weight = request.form.get("weight", "").strip()
    bp = request.form.get("bp", "").strip()
    fhr = request.form.get("fhr", "").strip()
    notes = request.form.get("notes", "").strip()
    if not pregnancy_id:
        flash("Please select a pregnancy record.", "error")
        return redirect(url_for("visits"))
    if not any([weight, bp, fhr]):
        flash("Enter at least one measurement: weight, blood pressure or fetal heart rate.", "error")
        return redirect(url_for("visits", pregnancy_id=pregnancy_id))
    with get_db() as conn:
        conn.execute(
            "INSERT INTO Visits (PregnancyID, VisitDate, Weight, BP, FHR, Notes) VALUES (?, ?, ?, ?, ?, ?)",
            (pregnancy_id, datetime.today().strftime("%Y-%m-%d"), weight, bp, fhr, notes)
        )
    flash("Antenatal visit saved.", "success")
    return redirect(url_for("visits", pregnancy_id=pregnancy_id))

@app.route("/health")
def health():
    return {"status": "ok"}

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
