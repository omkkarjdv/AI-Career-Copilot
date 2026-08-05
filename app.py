from flask import Flask, render_template, request, redirect, session, url_for
from db import Base, engine, SessionLocal
from ai import analyse_resume
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
import models
import PyPDF2
import docx
import json
import os

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

app.secret_key = "secret123"
serializer = URLSafeTimedSerializer(app.secret_key)
Base.metadata.create_all(bind=engine)

#Home
@app.route('/')
def home():
    if "user" in session:
        return redirect('/dashboard')
    return redirect('/login')

#SignUp
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db = SessionLocal()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user  = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return "User already exists. Please log in."
        
        hashed_password = generate_password_hash(password)
        
        user = models.User(email=email, password=hashed_password)
        db.add(user)
        db.commit()

        return redirect('/login')
    return render_template('signup.html')

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = SessionLocal()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.query(models.User).filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.email
            return redirect('/dashboard')
        else:
            return "Invalid credentials. Please try again."
    
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "user" not in session:
        return redirect('/login')
    
    result = None

    if request.method == 'POST':
        user_goal = request.form.get('role')
        resume_text = request.form.get('resume_text')

        file = request.files.get('file')

        if file and file.filename != "":
            if file.filename.endswith('.pdf'):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"PDF error: {str(e)}"}
            
            elif file.filename.endswith('.docx'):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"DOCX error: {str(e)}"}

        if resume_text and user_goal:
            try:
                print("Resume length:", len(resume_text))
                print("Goal:", user_goal)

                result = analyse_resume(resume_text, user_goal)

                print("AI Result:")
                print(result)
                db = SessionLocal()
                user = db.query(models.User).filter_by(email=session['user']).first()

                report = models.Report(
                    user_id = user.id,
                    resume_text = resume_text,
                    result = json.dumps(result)

                )

                db.add(report)
                db.commit()

            except Exception as e:
                result = {"error": f"AI error: {str(e)}"}

    return render_template(
        "dashboard.html",
        user=session["user"],
        result = result
    )
    
#History
@app.route('/history')
def history():
    if "user" not in session:
        return redirect('/login')

    db = SessionLocal()

    user = db.query(models.User).filter_by(email=session['user']).first()

    reports = db.query(models.Report).filter_by(user_id=user.id).all()

    parsed_reports = []

    for r in reports:
        try:
            parsed_result = json.loads(r.result) if r.result else {}
        except json.JSONDecodeError:
            parsed_result = {}

        parsed_reports.append({
            "resume": r.resume_text,
            "result": parsed_result
        })

    db.close()

    return render_template("history.html", reports=parsed_reports)

#Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect("/login")


#Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        db = SessionLocal()
        user = db.query(models.User).filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt='password-reset')
            reset_link = url_for("reset_password", token=token, _external=True)
            msg = Message("Password Reset", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"""
            Hello,
            Click the link below to reset your password.

            {reset_link}

            This link will expire in 1 hour.
            """

            mail.send(msg)

        return "If the email exists, a password reset link has been sent."
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        return "Reset link has expired"
    
    if request.method == 'POST':
        new_password = request.form['password']
        db = SessionLocal()
        user = db.query(models.User).filter_by(email=email).first()
        user.password = generate_password_hash(new_password)
        db.commit()
        return redirect('/login')
    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)