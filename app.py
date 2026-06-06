from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os


app = Flask(__name__)
app.secret_key = "edutrack_secret"


# CREATE DATABASE
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    rollno TEXT UNIQUE,
    branch TEXT,
    email TEXT,
    phone TEXT,
    password TEXT,
    marks INTEGER,
    photo TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT
)
''')
conn.commit()
conn.close()


# HOME PAGE
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login-page')
def login_page():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():

    username = request.form['username']
    password = request.form['password']

    if username == "admin" and password == "admin123":
        session['user'] = username
        return redirect('/dashboard')
    else:
        return "<h2>Invalid Username or Password ❌</h2>"
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login-page')


# ADD STUDENT PAGE
@app.route('/add-student')
def add_student():
    if 'user' not in session:
        return redirect('/login-page')
    return render_template("add_student.html")


# SAVE STUDENT
@app.route('/save-student', methods=['POST'])
def save_student():
    if 'user' not in session:
        return redirect('/login-page')

    name = request.form['name']
    rollno = request.form['rollno']
    branch = request.form['branch']
    
    email = request.form['email']
    phone = request.form['phone']
    password = generate_password_hash(
    request.form['password']
)

    marks = request.form['marks']

    photo = request.files['photo']
    photo_filename = photo.filename

    # save image in static folder
    photo.save(os.path.join('static', photo_filename))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
INSERT INTO students
(name, rollno, branch, email, phone, password, marks, photo)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''',
(name, rollno, branch, email,
 phone, password,
 marks, photo_filename))

    conn.commit()
    conn.close()

    flash("Student Added Successfully ✅")
    return redirect('/students')

# VIEW STUDENTS
@app.route('/students', methods=['GET', 'POST'])
def students():
    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    search = ""

    if request.method == 'POST':
        search = request.form.get('search')

    if search:
        cursor.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR rollno LIKE ?
        """, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute("SELECT * FROM students")

    data = cursor.fetchall()
    conn.close()

    return render_template("students.html", students=data)

# DELETE STUDENT
@app.route('/delete-student/<int:id>')
def delete_student(id):
    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    flash("Student Deleted Successfully ✅")
    return redirect('/students')

# EDIT STUDENT PAGE
@app.route('/edit-student/<int:id>')
def edit_student(id):
    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))

    student = cursor.fetchone()

    conn.close()

    return render_template("edit_student.html", student=student)


# UPDATE STUDENT
@app.route('/update-student/<int:id>', methods=['POST'])
def update_student(id):

    name = request.form['name']
    rollno = request.form['rollno']
    branch = request.form['branch']
    marks = request.form['marks']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET name=?, rollno=?, branch=?, marks=?
    WHERE id=?
    """, (name, rollno, branch, marks, id))

    conn.commit()
    conn.close()

    flash("Student Updated Successfully ✅")
    return redirect('/students')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Attendance Percentage

    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE status='Present'"
    )
    present_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM attendance"
    )
    total_attendance = cursor.fetchone()[0]

    attendance_percentage = 0

    if total_attendance > 0:
        attendance_percentage = round(
            (present_count / total_attendance) * 100,
            2
        )

    # Total Students

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Highest Marks

    cursor.execute("SELECT MAX(marks) FROM students")
    highest_marks = cursor.fetchone()[0]

    # Average Marks

    cursor.execute("SELECT AVG(marks) FROM students")
    average_marks = cursor.fetchone()[0]

    if average_marks:
        average_marks = round(average_marks, 2)

    # Topper

    cursor.execute("""
    SELECT name FROM students
    WHERE marks = (
        SELECT MAX(marks) FROM students
    )
    """)

    topper_data = cursor.fetchone()
    topper = topper_data[0] if topper_data else "No Data"

    # Branch Analytics

    cursor.execute("""
    SELECT branch, COUNT(*)
    FROM students
    GROUP BY branch
    """)

    branch_data = cursor.fetchall()

    branch_labels = [row[0] for row in branch_data]
    branch_counts = [row[1] for row in branch_data]

    # Top 5 Students

    cursor.execute("""
    SELECT name, marks
    FROM students
    ORDER BY marks DESC
    LIMIT 5
    """)

    top_students = cursor.fetchall()

    top_names = [row[0] for row in top_students]
    top_marks = [row[1] for row in top_students]

    conn.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        highest_marks=highest_marks,
        average_marks=average_marks,
        topper=topper,
        attendance_percentage=attendance_percentage,
        branch_labels=branch_labels,
        branch_counts=branch_counts,
        top_names=top_names,
        top_marks=top_marks
    )

@app.route('/student-login')
def student_login():
    return render_template('student_login.html')


@app.route('/student-auth', methods=['POST'])
def student_auth():

    rollno = request.form['rollno']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE rollno=?",
        (rollno,)
    )

    student = cursor.fetchone()
    print(student)
    conn.close()

    if student and check_password_hash(student[6], password):
        session['student'] = student[0]
        return redirect('/student-dashboard')

    return "Invalid Login"


@app.route('/student-dashboard')
def student_dashboard():

    if 'student' not in session:
        return redirect('/student-login')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id=?",
        (session['student'],)
    )

    student = cursor.fetchone()

    conn.close()

    return render_template(
        'student_dashboard.html',
        student=student
    )

@app.route('/student-logout')
def student_logout():

    session.pop('student', None)

    return redirect('/student-login')

@app.route('/change-password')
def change_password():

    if 'student' not in session:
        return redirect('/student-login')

    return render_template('change_password.html')


@app.route('/update-password', methods=['POST'])
def update_password():

    if 'student' not in session:
        return redirect('/student-login')

    current_password = request.form['current_password']
    new_password = request.form['new_password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM students WHERE id=?",
        (session['student'],)
    )

    stored_password = cursor.fetchone()[0]

    if not check_password_hash(
        stored_password,
        current_password
    ):
        conn.close()
        return "Current Password Incorrect ❌"

    hashed_password = generate_password_hash(
        new_password
    )

    cursor.execute(
        """
        UPDATE students
        SET password=?
        WHERE id=?
        """,
        (hashed_password, session['student'])
    )

    conn.commit()
    conn.close()

    return "Password Changed Successfully ✅"

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():

    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':

        student_id = request.form['student_id']
        status = request.form['status']

        from datetime import date

        today = date.today()

        cursor.execute(
            '''
            INSERT INTO attendance
            (student_id, date, status)
            VALUES (?, ?, ?)
            ''',
            (student_id, today, status)
        )

        conn.commit()

    cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    conn.close()

    return render_template(
        'attendance.html',
        students=students
    )
@app.route('/attendance-history')
def attendance_history():

    if 'user' not in session:
        return redirect('/login-page')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        attendance.date,
        students.name,
        students.rollno,
        attendance.status
    FROM attendance
    JOIN students
    ON attendance.student_id = students.id
    ORDER BY attendance.date DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return render_template(
        'attendance_history.html',
        records=records
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)