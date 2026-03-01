import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import init_db, get_db_connection, is_postgres
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

with app.app_context():
    init_db()


def fetchall(conn, query, params=()):
    if is_postgres():
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query.replace("?", "%s"), params)
        rows = cur.fetchall()
        cur.close()
        return rows
    else:
        return conn.execute(query, params).fetchall()


def fetchone(conn, query, params=()):
    if is_postgres():
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query.replace("?", "%s"), params)
        row = cur.fetchone()
        cur.close()
        return row
    else:
        return conn.execute(query, params).fetchone()


def execute(conn, query, params=()):
    if is_postgres():
        cur = conn.cursor()
        cur.execute(query.replace("?", "%s"), params)
        cur.close()
    else:
        conn.execute(query, params)


@app.route("/")
def index():
    conn = get_db_connection()
    subjects = fetchall(conn, "SELECT * FROM subjects ORDER BY created_at DESC")
    conn.close()
    stats = {
        "total_subjects": len(subjects),
        "at_risk": sum(1 for s in subjects if s["percentage"] < 75),
        "safe": sum(1 for s in subjects if s["percentage"] >= 75),
    }
    return render_template("index.html", subjects=subjects, stats=stats)


@app.route("/add", methods=["GET", "POST"])
def add_subject():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        total = request.form.get("total_classes", 0)
        attended = request.form.get("attended_classes", 0)
        if not name:
            flash("Subject name is required.", "error")
            return redirect(url_for("add_subject"))
        try:
            total = int(total)
            attended = int(attended)
        except ValueError:
            flash("Classes must be valid numbers.", "error")
            return redirect(url_for("add_subject"))
        if attended > total:
            flash("Attended classes cannot exceed total classes.", "error")
            return redirect(url_for("add_subject"))
        if total < 0 or attended < 0:
            flash("Values cannot be negative.", "error")
            return redirect(url_for("add_subject"))
        percentage = round((attended / total * 100), 2) if total > 0 else 0.0
        conn = get_db_connection()
        execute(conn,
            "INSERT INTO subjects (name, total_classes, attended_classes, percentage) VALUES (?, ?, ?, ?)",
            (name, total, attended, percentage),
        )
        conn.commit()
        conn.close()
        flash(f'Subject "{name}" added successfully!', "success")
        return redirect(url_for("index"))
    return render_template("add_subject.html")


@app.route("/subject/<int:subject_id>")
def subject_detail(subject_id):
    conn = get_db_connection()
    subject = fetchone(conn, "SELECT * FROM subjects WHERE id = ?", (subject_id,))
    conn.close()
    if not subject:
        flash("Subject not found.", "error")
        return redirect(url_for("index"))
    return render_template("subject_detail.html", subject=subject)


@app.route("/update/<int:subject_id>", methods=["POST"])
def update_subject(subject_id):
    conn = get_db_connection()
    subject = fetchone(conn, "SELECT * FROM subjects WHERE id = ?", (subject_id,))
    if not subject:
        conn.close()
        flash("Subject not found.", "error")
        return redirect(url_for("index"))
    action = request.form.get("action")
    total = subject["total_classes"]
    attended = subject["attended_classes"]
    if action == "attend":
        total += 1
        attended += 1
    elif action == "miss":
        total += 1
    elif action == "manual":
        try:
            total = int(request.form.get("total_classes", total))
            attended = int(request.form.get("attended_classes", attended))
        except ValueError:
            flash("Invalid values.", "error")
            conn.close()
            return redirect(url_for("subject_detail", subject_id=subject_id))
        if attended > total or total < 0 or attended < 0:
            flash("Invalid class counts.", "error")
            conn.close()
            return redirect(url_for("subject_detail", subject_id=subject_id))
    percentage = round((attended / total * 100), 2) if total > 0 else 0.0
    execute(conn,
        "UPDATE subjects SET total_classes=?, attended_classes=?, percentage=? WHERE id=?",
        (total, attended, percentage, subject_id),
    )
    conn.commit()
    conn.close()
    flash("Attendance updated!", "success")
    return redirect(url_for("subject_detail", subject_id=subject_id))


@app.route("/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    conn = get_db_connection()
    subject = fetchone(conn, "SELECT name FROM subjects WHERE id = ?", (subject_id,))
    if subject:
        execute(conn, "DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        flash(f'Subject "{subject["name"]}" deleted.', "success")
    conn.close()
    return redirect(url_for("index"))


@app.route("/predict/<int:subject_id>")
def predict(subject_id):
    miss = request.args.get("miss", 0, type=int)
    conn = get_db_connection()
    subject = fetchone(conn, "SELECT * FROM subjects WHERE id = ?", (subject_id,))
    conn.close()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    future_total = subject["total_classes"] + miss
    future_percentage = round((subject["attended_classes"] / future_total * 100), 2) if future_total > 0 else 0.0
    classes_needed = 0
    temp_attended = subject["attended_classes"]
    temp_total = future_total
    while temp_total > 0 and (temp_attended / temp_total * 100) < 75:
        temp_attended += 1
        temp_total += 1
        classes_needed += 1
        if classes_needed > 500:
            classes_needed = -1
            break
    return jsonify({
        "subject_name": subject["name"],
        "current_percentage": subject["percentage"],
        "future_percentage": future_percentage,
        "classes_to_attend": classes_needed,
        "total_after_miss": future_total,
        "attended": subject["attended_classes"],
        "safe": future_percentage >= 75,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
