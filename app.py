from flask import Flask, request, render_template, flash, redirect, url_for,session, logging, send_file, jsonify, Response, render_template_string, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
#from werkzeug.security import generate_password_hash
#from werkzeug.security import check_password_hash
import random, string
import os
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DateTimeField, BooleanField, IntegerField, DecimalField, HiddenField, SelectField, RadioField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_mail import Mail, Message
from functools import wraps
from werkzeug.utils import secure_filename
from coolname import generate_slug
from datetime import timedelta, datetime
from objective import ObjectiveTest
from subjective import SubjectiveTest
from deepface import DeepFace
import pandas as pd
import stripe
import operator
import functools
import math, random 
import csv
import cv2
import numpy as np
import json
import base64
from wtforms_components import TimeField
from wtforms.fields import DateField
from wtforms.validators import ValidationError, NumberRange
from flask_session import Session
from flask_cors import CORS, cross_origin
import camera

app = Flask(__name__)
app.secret_key = 'sem6project'
app.permanent_session_lifetime = timedelta(hours=2)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'quizapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['MAIL_SERVER']='smtp.stackmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'care@youremail.com'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'quizapp:'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = False  # Keep False for localhost
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"  # Fix Chrome cookie issue
app.config['WTF_CSRF_ENABLED'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
stripe_keys = {
    "secret_key": "dummy",
    "publishable_key": "dummy",
}

stripe.api_key = stripe_keys["secret_key"]

mail = Mail(app)

sess = Session(app)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


mysql = MySQL(app)

sender = 'whitegeorge5611@gmail.com'

YOUR_DOMAIN = 'http://localhost:5000'

# # -------------------------
# # Session setup
# # -------------------------
@app.before_request
def make_session_permanent():
    session.permanent = True

# # -------------------------
# # Professor role check decorator
# # -------------------------
def user_role_professor(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			if session.get('user_role').lower() == "teacher":
				return f(*args, **kwargs)
			else:
				flash('You do not have privileges to access this page!', 'danger')
				return render_template("404.html")
		else:
			flash('Unauthorized, please login!', 'danger')
			return redirect(url_for('login'))
	return wrap

# # -------------------------
# # Student role check decorator
# # -------------------------
def user_role_student(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session.get('user_role').lower() == 'student':
            return f(*args, **kwargs)
        else:
            flash("Please login first!", "danger")
            return redirect(url_for('login'))  # or your login route name
    return wrap

@app.route("/config")
#@user_role_professor
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)

@app.route('/video_feed', methods=['GET','POST'])
#@user_role_student
def video_feed():
	if request.method == "POST":
		imgData = request.form['data[imgData]']
		testid = request.form['data[testid]']
		voice_db = request.form['data[voice_db]']
		proctorData = camera.get_frame(imgData)
		jpg_as_text = proctorData['jpg_as_text']
		mob_status =proctorData['mob_status']
		person_status = proctorData['person_status']
		user_move1 = proctorData['user_move1']
		user_move2 = proctorData['user_move2']
		eye_movements = proctorData['eye_movements']
		cur = mysql.connection.cursor()
		results = cur.execute('INSERT INTO proctoring_log (email, name, test_id, voice_db, img_log, user_movements_updown, user_movements_lr, user_movements_eyes, phone_detection, person_status, uid) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
			(session.get('email'), session.get('name'), testid, voice_db, jpg_as_text, user_move1, user_move2, eye_movements, mob_status, person_status,session.get('uid')))
		mysql.connection.commit()
		cur.close()
		if(results > 0):
			return "recorded image of video"
		else:
			return "error in video"

@app.route('/window_event', methods=['GET','POST'])
#@user_role_student
def window_event():
	if request.method == "POST":
		testid = request.form['testid']
		cur = mysql.connection.cursor()
		results = cur.execute('INSERT INTO window_estimation_log (email, test_id, name, window_event, uid) values(%s,%s,%s,%s,%s)', (session.get('email'), testid, session.get('name'), 1, session.get('uid')))
		mysql.connection.commit()
		cur.close()
		if(results > 0):
			return "recorded window"
		else:
			return "error in window"

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'inr',
                        'unit_amount': 499*100,
                        'product_data': {
                            'name': 'Basic Exam Plan of 10 units',
                            'images': ['https://i.imgur.com/LsvO3kL_d.webp?maxwidth=760&fidelity=grand'],
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancelled',
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/livemonitoringtid")
#@user_role_professor
def livemonitoringtid():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT * from teachers where email = %s and uid = %s and proctoring_type = 1', (session['email'], session['uid']))
	if results > 0:
		cresults = cur.fetchall()
		now = datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
		testids = []
		for a in cresults:
			if datetime.strptime(str(a['start']),"%Y-%m-%d %H:%M:%S") <= now and datetime.strptime(str(a['end']),"%Y-%m-%d %H:%M:%S") >= now:
				testids.append(a['test_id'])
		cur.close()
		return render_template("livemonitoringtid.html", cresults = testids)
	else:
		return render_template("livemonitoringtid.html", cresults = None)

@app.route('/live_monitoring', methods=['GET','POST'])
#@user_role_professor
def live_monitoring():
	if request.method == 'POST':
		testid = request.form['choosetid']
		return render_template('live_monitoring.html',testid = testid)
	else:
		return render_template('live_monitoring.html',testid = None)	

@app.route("/success")
#@user_role_professor
def success():
	cur = mysql.connection.cursor()
	cur.execute('UPDATE users set examcredits = examcredits+10 where email = %s and uid = %s', (session['email'], session['uid']))
	mysql.connection.commit()
	cur.close()
	return render_template("success.html")

@app.route("/cancelled")
#@user_role_professor
def cancelled():
    return render_template("cancelled.html")

@app.route("/payment")
#@user_role_professor
def payment():
	cur = mysql.connection.cursor()
	cur.execute('SELECT examcredits FROM USERS where email = %s and uid = %s', (session['email'], session['uid']))
	callresults = cur.fetchone()
	cur.close()
	return render_template("payment.html", key = stripe_keys['publishable_key'], callresults = callresults)

@app.route('/')
def index():
	return render_template('index.html')

@app.errorhandler(404) 
def not_found(e):
	return render_template("404.html") 

@app.errorhandler(500)
def internal_error(error):
	return render_template("500.html") 

@app.route('/calc')
def calc():
	return render_template('calc.html')

@app.route('/report_professor')
#@user_role_professor
def report_professor():
	return render_template('report_professor.html')

@app.route('/professor_index')
#@user_role_professor
def professor_index():
	print("Session data:", dict(session))
	return render_template('professor_index.html', name=session.get('name'))

@app.route('/student_index')
#@user_role_student
def student_index():
    name = session.get('name')
    return render_template('student_index.html', name=session.get('name'))

@app.route('/faq')
def faq():
	return render_template('faq.html')

@app.route('/report_student')
#@user_role_student
def report_student():
	return render_template('report_student.html')

@app.route('/report_professor_email', methods=['GET','POST'])
#@user_role_professor
def report_professor_email():
	if request.method == 'POST':
		careEmail = "whitegeorge5611@gmail.com"
		cname = session['name']
		cemail = session['email']
		ptype = request.form['prob_type']
		cquery = request.form['rquery']
		msg1 = Message('PROBLEM REPORTED', sender = sender, recipients = [careEmail])
		msg1.body = " ".join(["NAME:", cname, "PROBLEM TYPE:", ptype ,"EMAIL:", cemail, "", "QUERY:", cquery]) 
		mail.send(msg1)
		flash('Your Problem has been recorded.', 'success')
	return render_template('report_professor.html')

@app.route('/report_student_email', methods=['GET','POST'])
#@user_role_student
def report_student_email():
	if request.method == 'POST':
		careEmail = "whitegeorge5611@gmail.com"
		cname = session['name']
		cemail = session['email']
		ptype = request.form['prob_type']
		cquery = request.form['rquery']
		msg1 = Message('PROBLEM REPORTED', sender = sender, recipients = [careEmail])
		msg1.body = " ".join(["NAME:", cname, "PROBLEM TYPE:", ptype ,"EMAIL:", cemail, "", "QUERY:", cquery]) 
		mail.send(msg1)
		flash('Your Problem has been recorded.', 'success')
	return render_template('report_student.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
	if request.method == 'POST':
		careEmail = "whitegeorge5611@gmail.com"
		cname = request.form['cname']
		cemail = request.form['cemail']
		cquery = request.form['cquery']
		msg1 = Message('Hello', sender = sender, recipients = [cemail])
		msg2 = Message('Hello', sender = sender, recipients = [careEmail])
		msg1.body = "YOUR QUERY WILL BE PROCESSED! WITHIN 24 HOURS"
		msg2 = Message('Hello', sender = sender, recipients = [careEmail])
		msg2.body = " ".join(["NAME:", cname, "EMAIL:", cemail, "QUERY:", cquery]) 
		mail.send(msg1)
		mail.send(msg2)
		flash('Your Query has been recorded.', 'success')
	return render_template('contact.html')

@app.route('/lostpassword', methods=['GET','POST'])
def lostpassword():
	if request.method == 'POST':
		lpemail = request.form['lpemail']
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT * from users where email = %s' , [lpemail])
		if results > 0:
			sesOTPfp = generateOTP()
			session['tempOTPfp'] = sesOTPfp
			session['seslpemail'] = lpemail
			msg1 = Message('MyProctor.ai - OTP Verification for Lost Password', sender = sender, recipients = [lpemail])
			msg1.body = "Your OTP Verfication code for reset password is "+sesOTPfp+"."
			mail.send(msg1)
			return redirect(url_for('verifyOTPfp')) 
		else:
			return render_template('lostpassword.html',error="Account not found.")
	return render_template('lostpassword.html')

@app.route('/verifyOTPfp', methods=['GET','POST'])
def verifyOTPfp():
	if request.method == 'POST':
		fpOTP = request.form['fpotp']
		fpsOTP = session['tempOTPfp']
		if(fpOTP == fpsOTP):
			return redirect(url_for('lpnewpwd')) 
	return render_template('verifyOTPfp.html')

@app.route('/lpnewpwd', methods=['GET','POST'])
def lpnewpwd():
	if request.method == 'POST':
		npwd = request.form['npwd']
		cpwd = request.form['cpwd']
		slpemail = session['seslpemail']
		if(npwd == cpwd ):
			cur = mysql.connection.cursor()
			cur.execute('UPDATE users set password = %s where email = %s', (npwd, slpemail))
			mysql.connection.commit()
			cur.close()
			session.clear()
			return render_template('login.html',success="Your password was successfully changed.")
		else:
			return render_template('login.html',error="Password doesn't matched.")
	return render_template('lpnewpwd.html')

@app.route('/generate_test')
#@user_role_professor
def generate_test():
	return render_template('generatetest.html')

@app.route('/changepassword_professor')
#@user_role_professor
def changepassword_professor():
	return render_template('changepassword_professor.html')

@app.route('/changepassword_student')
#@user_role_student
def changepassword_student():
	return render_template('changepassword_student.html')

def generateOTP() : 
    digits = "0123456789"
    OTP = "" 
    for i in range(5) : 
        OTP += digits[math.floor(random.random() * 10)] 
    return OTP 

# -------------------------
# Register Route (No Hash)
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type'].lower()

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO users (name, email, password, user_type)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, user_type))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# -------------------------
# Login Route (Role-Based)
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
	msg = ''
	try:
		if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
			email = request.form['email'].strip()
			password = request.form['password'].strip()

			# ✅ Correct way to create cursor for flask_mysqldb
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

			# ✅ Correct parameterized query (NO f-string, NO manual quotes)
			cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
			user = cur.fetchone()
			cur.close()

			print("Fetched user:", user)  # Debug log

			if user:
				session['logged_in'] = True
				session['uid'] = user['uid']
				session['email'] = user['email']
				session['user_role'] = user['user_type']
				session['name'] = user['name']
				session.permanent = True
				session.modified = True
				app.permanent_session_lifetime = timedelta(minutes=30)
				mysql.connection.commit()
				print("✅ Session after login:", dict(session))  # <-- add this line

				# ✅ Role-based redirect
				if user['user_type'].lower() == 'student':
					return redirect(url_for('student_index'))
				elif user['user_type'].lower() == 'teacher':
					return redirect(url_for('professor_index'))
				else:
					return redirect(url_for('register'))
			else:
				msg = 'Invalid email or password!'
				flash(msg, 'danger')

	except Exception as e:
		import traceback
		print("Database error:", traceback.format_exc())
		msg = f"Database error: {e}"
		flash(msg, 'danger')

	return render_template('login.html', msg=msg)

	
@app.route('/verifyEmail', methods=['GET','POST'])
def verifyEmail():
	if request.method == 'POST':
		theOTP = request.form['eotp']
		mOTP = session['tempOTP']
		dbName = session['tempName']
		dbEmail = session['tempEmail']
		dbPassword = session['tempPassword']
		dbUser_type = session['tempUT']
		dbImgdata = session['tempImage']
		if(theOTP == mOTP):
			cur = mysql.connection.cursor()
			ar = cur.execute('INSERT INTO users(name, email, password, user_type, user_image, user_login) values(%s,%s,%s,%s,%s,%s)', (dbName, dbEmail, dbPassword, dbUser_type, dbImgdata,0))
			mysql.connection.commit()
			if ar > 0:
				flash("Thanks for registering! You are sucessfully verified!.")
				return  redirect(url_for('login'))
			else:
				flash("Error Occurred!")
				return  redirect(url_for('login')) 
			cur.close()
			session.clear()
		else:
			return render_template('register.html',error="OTP is incorrect.")
	return render_template('verifyEmail.html')

@app.route('/changepassword', methods=["GET", "POST"])
def changePassword():
	if request.method == "POST":
		oldPassword = request.form['oldpassword']
		newPassword = request.form['newpassword']
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT * from users where email = %s and uid = %s', (session['email'], session['uid']))
		if results > 0:
			data = cur.fetchone()
			password = data['password']
			usertype = data['user_type']
			if(password == oldPassword):
				cur.execute("UPDATE users SET password = %s WHERE email = %s", (newPassword, session['email']))
				mysql.connection.commit()
				msg="Changed successfully"
				flash('Changed successfully.', 'success')
				cur.close()
				if usertype == "student":
					return render_template("student_index.html", success=msg)
				else:
					return render_template("professor_index.html", success=msg)
			else:
				error = "Wrong password"
				if usertype == "student":
					return render_template("student_index.html", error=error)
				else:
					return render_template("professor_index.html", error=error)
		else:
			return redirect(url_for('/'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        if 'email' in session and 'uid' in session:
            cur = mysql.connection.cursor()
            cur.execute(
                'UPDATE users SET user_login = 0 WHERE email = %s AND uid = %s',
                (session['email'], session['uid'])
            )
            mysql.connection.commit()
            cur.close()

        # ✅ Clear session
        session.clear()

        # ✅ Delete cookie
        resp = make_response()
        resp.delete_cookie('session')

        # ✅ Handle AJAX requests
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return "success"

        # ✅ Fallback for normal logout (direct click)
        flash("You have been logged out successfully.", "success")
        return redirect(url_for('login'))

    except Exception as e:
        print("Logout error:", str(e))
        session.clear()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return "error"
        flash("Logout failed. Please try again.", "danger")
        return redirect(url_for('login'))

def examcreditscheck():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT examcredits from users where examcredits >= 1 and email = %s and uid = %s', (session['email'], session['uid']))
	if results > 0:
		return True

class QAUploadForm(FlaskForm):
	subject = StringField('Subject')
	topic = StringField('Topic')
	doc = FileField('CSV Upload', validators=[FileRequired()])
	start_date = DateField('Start Date')
	start_time = TimeField('Start Time', default=datetime.utcnow()+timedelta(hours=5.5))
	end_date = DateField('End Date')
	end_time = TimeField('End Time', default=datetime.utcnow()+timedelta(hours=5.5))
	duration = IntegerField('Duration(in min)')
	password = PasswordField('Exam Password', [validators.Length(min=3, max=6)])
	proctor_type = RadioField('Proctoring Type', choices=[('0','Automatic Monitoring'),('1','Live Monitoring')])

	def validate_end_date(form, field):
		if field.data < form.start_date.data:
			raise ValidationError("End date must not be earlier than start date.")
	
	def validate_end_time(form, field):
		try:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M:%S")
			end_dt = datetime.strptime(f"{form.end_date.data} {form.end_time.data}", "%Y-%m-%d %H:%M:%S")
		except ValueError:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M")
			end_dt = datetime.strptime(f"{form.end_date.data} {form.end_time.data}", "%Y-%m-%d %H:%M")
		if end_dt <= start_dt:
			raise ValidationError("End date/time must be after start date/time")
	
	def validate_start_date(form, field):
		try:
			start_dt = datetime.strptime(f"{field.data} {form.start_time.data}", "%Y-%m-%d %H:%M:%S")
		except ValueError:
			start_dt = datetime.strptime(f"{field.data} {form.start_time.data}", "%Y-%m-%d %H:%M")
		
		if start_dt < datetime.now():
			raise ValidationError("Start date/time must not be earlier than now")

@app.route('/create_test_lqa', methods = ['GET', 'POST'])
#@user_role_professor
def create_test_lqa():
	form = QAUploadForm()
	if request.method == 'POST' and form.validate_on_submit():
		test_id = generate_slug(2)
		filename = secure_filename(form.doc.data.filename)
		filestream = form.doc.data
		filestream.seek(0)
		ef = pd.read_csv(filestream)
		fields = ['qid','q','marks']
		df = pd.DataFrame(ef, columns = fields)
		cur = mysql.connection.cursor()
		ecc = examcreditscheck()
		if ecc:
			for row in df.index:
				cur.execute('INSERT INTO longqa(test_id,qid,q,marks,uid) values(%s,%s,%s,%s,%s)', (test_id, df['qid'][row], df['q'][row], df['marks'][row], session['uid']))
				cur.connection.commit()
				
			start_date = form.start_date.data
			end_date = form.end_date.data
			start_time = form.start_time.data
			end_time = form.end_time.data
			start_date_time = str(start_date) + " " + str(start_time)
			end_date_time = str(end_date) + " " + str(end_time)
			duration = int(form.duration.data)*60
			password = form.password.data
			subject = form.subject.data
			topic = form.topic.data
			proctor_type = form.proctor_type.data
			cur.execute('INSERT INTO teachers (email, test_id, test_type, start, end, duration, show_ans, password, subject, topic, neg_marks, calc, proctoring_type, uid) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
				(session.get('email'), test_id, "subjective", start_date_time, end_date_time, duration, 0, password, subject, topic, 0, 0, proctor_type, session['uid']))
			mysql.connection.commit()
			cur.execute('UPDATE users SET examcredits = examcredits-1 where email = %s and uid = %s', (session['email'],session['uid']))
			mysql.connection.commit()
			cur.close()
			flash(f'Exam ID: {test_id}', 'success')
			return redirect(url_for('professor_index'))
		else:
			flash("No exam credits points are found! Please pay it!")
			return redirect(url_for('professor_index'))
	return render_template('create_test_lqa.html' , form = form)

class UploadForm(FlaskForm):
	subject = StringField('Subject')
	topic = StringField('Topic')
	doc = FileField('CSV Upload', validators=[FileRequired()])
	start_date = DateField('Start Date')
	start_time = TimeField('Start Time', default=datetime.utcnow()+timedelta(hours=5.5))
	end_date = DateField('End Date')
	end_time = TimeField('End Time', default=datetime.utcnow()+timedelta(hours=5.5))
	calc = BooleanField('Enable Calculator')
	neg_mark = DecimalField('Enable negative marking in % ', validators=[NumberRange(min=0, max=100)])
	duration = IntegerField('Duration(in min)')
	password = PasswordField('Exam Password', [validators.Length(min=3, max=6)])
	proctor_type = RadioField('Proctoring Type', choices=[('0','Automatic Monitoring'),('1','Live Monitoring')])

	def validate_end_date(form, field):
		if field.data < form.start_date.data:
			raise ValidationError("End date must not be earlier than start date.")
	
	def validate_end_time(form, field):
		start_time_str = form.start_time.data.strftime("%H:%M:%S")
		end_time_str = field.data.strftime("%H:%M:%S")

		start_dt = datetime.strptime(f"{form.start_date.data} {start_time_str}", "%Y-%m-%d %H:%M:%S")
		end_dt = datetime.strptime(f"{form.end_date.data} {end_time_str}", "%Y-%m-%d %H:%M:%S")
		
		if start_dt >= end_dt:
			raise ValidationError("End date/time must be later than start date/time")
	
	def validate_start_date(form, field):
		try:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M:%S")
		except ValueError:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M")
		if start_dt < datetime.now():
			raise ValidationError("Start date/time must not be earlier than now")

class PracUploadForm(FlaskForm):
	# Fields specific to practical/test with a code question
	subject = StringField('Subject')
	topic = StringField('Topic')
	compiler = SelectField('Compiler', choices=[('python','Python'),('c','C'),('cpp','C++'),('java','Java')])
	questionprac = TextAreaField('Practical Question')
	marksprac = IntegerField('Marks', validators=[NumberRange(min=0)])
	start_date = DateField('Start Date')
	start_time = TimeField('Start Time', default=datetime.utcnow()+timedelta(hours=5.5))
	end_date = DateField('End Date')
	end_time = TimeField('End Time', default=datetime.utcnow()+timedelta(hours=5.5))
	duration = IntegerField('Duration(in min)')
	password = PasswordField('Exam Password', [validators.Length(min=3, max=6)])
	proctor_type = RadioField('Proctoring Type', choices=[('0','Automatic Monitoring'),('1','Live Monitoring')])

	def validate_end_date(form, field):
		if field.data < form.start_date.data:
			raise ValidationError("End date must not be earlier than start date.")
	
	def validate_end_time(form, field):
		start_date_time = datetime.strptime(str(form.start_date.data) + " " + str(form.start_time.data),"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
		end_date_time = datetime.strptime(str(form.end_date.data) + " " + str(field.data),"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
		if start_date_time >= end_date_time:
			raise ValidationError("End date time must not be earlier/equal than start date time")
	
	def validate_start_date(form, field):
		try:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M:%S")
		except ValueError:
			start_dt = datetime.strptime(f"{form.start_date.data} {form.start_time.data}", "%Y-%m-%d %H:%M")
		if start_dt < datetime.now():
			raise ValidationError("Start date/time must not be earlier than now")

class TestForm(Form):
	test_id = StringField('Exam ID')
	password = PasswordField('Exam Password')
	img_hidden_form = HiddenField(label=(''))

@app.route('/create-test', methods=['GET', 'POST'])
# @user_role_professor
def create_test():
	if 'email' not in session or 'uid' not in session:
		flash("Session expired. Please log in again.", "danger")
		return redirect(url_for('login'))
	print("📦 Session at create-test:", dict(session))
	form = UploadForm()
	if request.method == 'POST':
		print("🟢 POST request received for /create-test")
		print("Form data:", request.form)
		print("Uploaded file:", form.doc.data)
		if form.validate_on_submit():
			test_id = generate_slug(2)
			filename = secure_filename(form.doc.data.filename)
			filestream = form.doc.data
			filestream.seek(0)

			# ✅ Read CSV properly
			ef = pd.read_csv(filestream)
			fields = ['qid', 'q', 'a', 'b', 'c', 'd', 'ans', 'marks']

			# ✅ Validate columns
			if not all(col in ef.columns for col in fields):
				flash("CSV file missing required columns!", "danger")
				return redirect(url_for('create_test'))

			df = ef[fields]

			# ✅ Check for missing values
			if df.isnull().values.any():
				flash("CSV file has empty fields. Please fix and upload again.", "danger")
				return redirect(url_for('create_test'))

			cur = mysql.connection.cursor()
			ecc = examcreditscheck()
			if ecc:
				# ✅ Insert all questions
				for _, row in df.iterrows():
					cur.execute("""
						INSERT INTO questions (test_id, qid, q, a, b, c, d, ans, marks, uid)
						VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
					""", (test_id, row['qid'], row['q'], row['a'], row['b'], row['c'],
						  row['d'], row['ans'], row['marks'], session['uid']))
				mysql.connection.commit()

				# ✅ Insert exam details
				start_date_time = f"{form.start_date.data} {form.start_time.data.strftime('%H:%M')}"
				end_date_time = f"{form.end_date.data} {form.end_time.data.strftime('%H:%M')}"
				neg_mark = int(form.neg_mark.data or 0)
				calc = 1 if form.calc.data else 0
				duration = int(form.duration.data) * 60
				password = form.password.data
				subject = form.subject.data
				topic = form.topic.data
				proctor_type = form.proctor_type.data

				cur.execute("""
					INSERT INTO teachers 
					(email, test_id, test_type, start, end, duration, show_ans, password, subject, topic, neg_marks, calc, proctoring_type, uid)
					VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
				""", (session['email'], test_id, "objective", start_date_time, end_date_time,
					  duration, 1, password, subject, topic, neg_mark, calc, proctor_type, session['uid']))
				mysql.connection.commit()

				# ✅ Deduct one credit
				cur.execute("UPDATE users SET examcredits = examcredits - 1 WHERE email = %s AND uid = %s",
							(session['email'], session['uid']))
				mysql.connection.commit()
				cur.close()

				flash(f'✅ Exam created successfully! Exam ID: {test_id}', 'success')
				return redirect(url_for('professor_index'))
			else:
				flash("No exam credits found! Please recharge your credits.", "danger")
				return redirect(url_for('professor_index'))
		else:
			print("❌ Validation errors:", form.errors)
			flash("Form validation failed. Please check all fields!", "danger")
	return render_template('create_test.html', form=form)

@app.route('/create_test_pqa', methods = ['GET', 'POST'])
#@user_role_professor
def create_test_pqa():
	form = PracUploadForm()
	if request.method == 'POST' and form.validate_on_submit():
		test_id = generate_slug(2)
		ecc = examcreditscheck()
		print(ecc)
		if ecc:
			test_id = generate_slug(2)
			compiler = form.compiler.data
			questionprac = form.questionprac.data
			marksprac = int(form.marksprac.data)
			cur = mysql.connection.cursor()
			cur.execute('INSERT INTO practicalqa(test_id,qid,q,compiler,marks,uid) values(%s,%s,%s,%s,%s,%s)', (test_id, 1, questionprac, compiler, marksprac, session['uid']))
			mysql.connection.commit()
			start_date = form.start_date.data
			end_date = form.end_date.data
			start_time = form.start_time.data
			end_time = form.end_time.data
			start_date_time = str(start_date) + " " + str(start_time)
			end_date_time = str(end_date) + " " + str(end_time)
			duration = int(form.duration.data)*60
			password = form.password.data
			subject = form.subject.data
			topic = form.topic.data
			proctor_type = form.proctor_type.data
			cur.execute('INSERT INTO teachers (email, test_id, test_type, start, end, duration, show_ans, password, subject, topic, neg_marks, calc, proctoring_type, uid) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
				(session.get('email'), test_id, "practical", start_date_time, end_date_time, duration, 0, password, subject, topic, 0, 0, proctor_type, session['uid']))
			mysql.connection.commit()
			cur.execute('UPDATE users SET examcredits = examcredits-1 where email = %s and uid = %s', (session['email'],session['uid']))
			mysql.connection.commit()
			cur.close()
			flash(f'Exam ID: {test_id}', 'success')
			return redirect(url_for('professor_index'))
		else:
			flash("No exam credits points are found! Please pay it!")
			return redirect(url_for('professor_index'))	
	return render_template('create_prac_qa.html' , form = form)

@app.route('/deltidlist', methods=['GET'])
#@user_role_professor
def deltidlist():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT * from teachers where email = %s and uid = %s', (session['email'], session['uid']))
	if results > 0:
		cresults = cur.fetchall()
		now = datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
		testids = []
		for a in cresults:
			if datetime.strptime(str(a['start']),"%Y-%m-%d %H:%M:%S") > now:
				testids.append(a['test_id'])
		cur.close()
		return render_template("deltidlist.html", cresults = testids)
	else:
		return render_template("deltidlist.html", cresults = None)

@app.route('/deldispques', methods=['GET','POST'])
#@user_role_professor
def deldispques():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		et = examtypecheck(tidoption)
		if et['test_type'] == "objective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from questions where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("deldispques.html", callresults = callresults, tid = tidoption)
		elif et['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from longqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("deldispquesLQA.html", callresults = callresults, tid = tidoption)
		elif et['test_type'] == "practical":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from practicalqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("deldispquesPQA.html", callresults = callresults, tid = tidoption)
		else:
			flash("Some Error Occured!")
			return redirect(url_for('/deltidlist'))

@app.route('/delete_questions/<testid>', methods=['GET', 'POST'])
#@user_role_professor
def delete_questions(testid):
	et = examtypecheck(testid)
	if et['test_type'] == "objective":
		cur = mysql.connection.cursor()
		msg = '' 
		if request.method == 'POST':
			testqdel = request.json['qids']
			if testqdel:
				if ',' in testqdel:
					testqdel = testqdel.split(',')
					for getid in testqdel:
						cur.execute('DELETE FROM questions WHERE test_id = %s and qid =%s and uid = %s', (testid,getid,session['uid']))
						mysql.connection.commit()
					resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
					resp.status_code = 200
					return resp
				else:
					cur.execute('DELETE FROM questions WHERE test_id = %s and qid =%s and uid = %s', (testid,testqdel,session['uid']))
					mysql.connection.commit()
					resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
					resp.status_code = 200
					return resp
	elif et['test_type'] == "subjective":
		cur = mysql.connection.cursor()
		msg = '' 
		if request.method == 'POST':
			testqdel = request.json['qids']
			if testqdel:
				if ',' in testqdel:
					testqdel = testqdel.split(',')
					for getid in testqdel:
						cur.execute('DELETE FROM longqa WHERE test_id = %s and qid =%s and uid = %s', (testid,getid,session['uid']))
						mysql.connection.commit()
					resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
					resp.status_code = 200
					return resp
				else:
					cur.execute('DELETE FROM longqa WHERE test_id = %s and qid =%s and uid = %s', (testid,testqdel,session['uid']))
					mysql.connection.commit()
					resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
					resp.status_code = 200
					return resp
	elif et['test_type'] == "practical":
		cur = mysql.connection.cursor()
		msg = '' 
		if request.method == 'POST':
			testqdel = request.json['qids']
			if testqdel:
				if ',' in testqdel:
					testqdel = testqdel.split(',')
					for getid in testqdel:
						cur.execute('DELETE FROM practicalqa WHERE test_id = %s and qid =%s and uid = %s', (testid,getid,session['uid']))
						mysql.connection.commit()
					resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
					resp.status_code = 200
					return resp
			else:
				cur.execute('DELETE FROM questions WHERE test_id = %s and qid =%s and uid = %s', (testid,testqdel,session['uid']))
				mysql.connection.commit()
				resp = jsonify('<span style=\'color:green;\'>Questions deleted successfully</span>')
				resp.status_code = 200
				return resp
	else:
		flash("Some Error Occured!")
		return redirect(url_for('/deltidlist'))

@app.route('/<testid>/<qid>')
#@user_role_professor
def del_qid(testid, qid):
	cur = mysql.connection.cursor()
	results = cur.execute('DELETE FROM questions where test_id = %s and qid = %s and uid = %s', (testid,qid,session['uid']))
	mysql.connection.commit()
	if results>0:
		msg="Deleted successfully"
		flash('Deleted successfully.', 'success')
		cur.close()
		return render_template("deldispques.html", success=msg)
	else:
		return redirect(url_for('/deldispques'))

@app.route('/updatetidlist', methods=['GET'])
#@user_role_professor
def updatetidlist():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT * from teachers where email = %s and uid = %s', (session['email'],session['uid']))
	if results > 0:
		cresults = cur.fetchall()
		now = datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
		testids = []
		for a in cresults:
			if datetime.strptime(str(a['start']),"%Y-%m-%d %H:%M:%S") > now:
				testids.append(a['test_id'])
		cur.close()
		return render_template("updatetidlist.html", cresults = testids)
	else:
		return render_template("updatetidlist.html", cresults = None)

@app.route('/updatedispques', methods=['GET','POST'])
#@user_role_professor
def updatedispques():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		et = examtypecheck(tidoption)
		if et['test_type'] == "objective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from questions where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("updatedispques.html", callresults = callresults)
		elif et['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from longqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("updatedispquesLQA.html", callresults = callresults)
		elif et['test_type'] == "practical":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from practicalqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("updatedispquesPQA.html", callresults = callresults)
		else:
			flash('Error Occured!')
			return redirect(url_for('updatetidlist'))

@app.route('/update/<testid>/<qid>', methods=['GET','POST'])
#@user_role_professor
def update_quiz(testid, qid):
	if request.method == 'GET':
		cur = mysql.connection.cursor()
		cur.execute('SELECT * FROM questions where test_id = %s and qid =%s and uid = %s', (testid,qid,session['uid']))
		uresults = cur.fetchall()
		mysql.connection.commit()
		return render_template("updateQuestions.html", uresults=uresults)
	if request.method == 'POST':
		ques = request.form['ques']
		ao = request.form['ao']
		bo = request.form['bo']
		co = request.form['co']
		do = request.form['do']
		anso = request.form['anso']
		markso = request.form['mko']
		cur = mysql.connection.cursor()
		cur.execute('UPDATE questions SET q = %s, a = %s, b = %s, c = %s, d = %s, ans = %s, marks = %s where test_id = %s and qid = %s and uid = %s', (ques,ao,bo,co,do,anso,markso,testid,qid,session['uid']))
		cur.connection.commit()
		flash('Updated successfully.', 'success')
		cur.close()
		return redirect(url_for('updatetidlist'))
	else:
		flash('ERROR  OCCURED.', 'error')
		return redirect(url_for('updatetidlist'))

@app.route('/updateLQA/<testid>/<qid>', methods=['GET','POST'])
#@user_role_professor
def update_lqa(testid, qid):
	if request.method == 'GET':
		cur = mysql.connection.cursor()
		cur.execute('SELECT * FROM longqa where test_id = %s and qid =%s and uid = %s', (testid,qid,session['uid']))
		uresults = cur.fetchall()
		mysql.connection.commit()
		return render_template("updateQuestionsLQA.html", uresults=uresults)
	if request.method == 'POST':
		ques = request.form['ques']
		markso = request.form['mko']
		cur = mysql.connection.cursor()
		cur.execute('UPDATE longqa SET q = %s, marks = %s where test_id = %s and qid = %s and uid = %s', (ques,markso,testid,qid,session['uid']))
		cur.connection.commit()
		flash('Updated successfully.', 'success')
		cur.close()
		return redirect(url_for('updatetidlist'))
	else:
		flash('ERROR  OCCURED.', 'error')
		return redirect(url_for('updatetidlist'))

@app.route('/updatePQA/<testid>/<qid>', methods=['GET','POST'])
#@user_role_professor
def update_PQA(testid, qid):
	if request.method == 'GET':
		cur = mysql.connection.cursor()
		cur.execute('SELECT * FROM practicalqa where test_id = %s and qid =%s and uid = %s', (testid,qid,session['uid']))
		uresults = cur.fetchall()
		mysql.connection.commit()
		return render_template("updateQuestionsPQA.html", uresults=uresults)
	if request.method == 'POST':
		ques = request.form['ques']
		markso = request.form['mko']
		cur = mysql.connection.cursor()
		cur.execute('UPDATE practicalqa SET q = %s, marks = %s where test_id = %s and qid = %s and uid = %s', (ques,markso,testid,qid,session['uid']))
		cur.connection.commit()
		flash('Updated successfully.', 'success')
		cur.close()
		return redirect(url_for('updatetidlist'))
	else:
		flash('ERROR  OCCURED.', 'error')
		return redirect(url_for('updatetidlist'))

@app.route('/viewquestions', methods=['GET'])
#@user_role_professor
def viewquestions():
    if 'email' not in session or 'uid' not in session:
        flash('Please log in first.', 'warning')
        return redirect('/login')

    cur = mysql.connection.cursor()
    results = cur.execute('SELECT test_id FROM teachers WHERE email = %s AND uid = %s',
                          (session['email'], session['uid']))
    if results > 0:
        cresults = cur.fetchall()
        cur.close()
        return render_template("viewquestions.html", cresults=cresults)
    else:
        return render_template("viewquestions.html", cresults=None)


def examtypecheck(tidoption):
	cur = mysql.connection.cursor()
	cur.execute('SELECT test_type from teachers where test_id = %s and email = %s and uid = %s', (tidoption,session['email'],session['uid']))
	callresults = cur.fetchone()
	cur.close()
	return callresults

@app.route('/displayquestions', methods=['GET','POST'])
#@user_role_professor
def displayquestions():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		et = examtypecheck(tidoption)
		if et['test_type'] == "objective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from questions where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("displayquestions.html", callresults = callresults)
		elif et['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from longqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("displayquestionslong.html", callresults = callresults)
		elif et['test_type'] == "practical":
			cur = mysql.connection.cursor()
			cur.execute('SELECT * from practicalqa where test_id = %s and uid = %s', (tidoption,session['uid']))
			callresults = cur.fetchall()
			cur.close()
			return render_template("displayquestionspractical.html", callresults = callresults)

@app.route('/viewstudentslogs', methods=['GET'])
#@user_role_professor
def viewstudentslogs():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT test_id from teachers where email = %s and uid = %s and proctoring_type = 0', (session['email'], session['uid']))
	if results > 0:
		cresults = cur.fetchall()
		cur.close()
		return render_template("viewstudentslogs.html", cresults = cresults)
	else:
		return render_template("viewstudentslogs.html", cresults = None)

@app.route('/insertmarkstid', methods=['GET'])
#@user_role_professor
def insertmarkstid():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT * from teachers where show_ans = 0 and email = %s and uid = %s and (test_type = %s or test_type = %s)', (session['email'], session['uid'],"subjective","practical"))
	if results > 0:
		cresults = cur.fetchall()
		now = datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
		testids = []
		for a in cresults:
			if datetime.strptime(str(a['end']),"%Y-%m-%d %H:%M:%S") < now:
				testids.append(a['test_id'])
		cur.close()
		return render_template("insertmarkstid.html", cresults = testids)
	else:
		return render_template("insertmarkstid.html", cresults = None)

@app.route('/displaystudentsdetails', methods=['GET','POST'])
#@user_role_professor
def displaystudentsdetails():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		cur = mysql.connection.cursor()
		cur.execute('SELECT DISTINCT email,test_id from proctoring_log where test_id = %s', [tidoption])
		callresults = cur.fetchall()
		cur.close()
		return render_template("displaystudentsdetails.html", callresults = callresults)

@app.route('/insertmarksdetails', methods=['GET','POST'])
#@user_role_professor
def insertmarksdetails():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		et = examtypecheck(tidoption)
		if et['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT DISTINCT email,test_id from longtest where test_id = %s', [tidoption])
			callresults = cur.fetchall()
			cur.close()
			return render_template("subdispstudentsdetails.html", callresults = callresults)
		elif et['test_type'] == "practical":
			cur = mysql.connection.cursor()
			cur.execute('SELECT DISTINCT email,test_id from practicaltest where test_id = %s', [tidoption])
			callresults = cur.fetchall()
			cur.close()
			return render_template("pracdispstudentsdetails.html", callresults = callresults)
		else:
			flash("Some Error was occured!",'error')
			return redirect(url_for('insertmarkstid'))

@app.route('/insertsubmarks/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def insertsubmarks(testid,email):
	if request.method == "GET":
		cur = mysql.connection.cursor()
		cur.execute('SELECT l.email as email, l.marks as inputmarks, l.test_id as test_id, l.qid as qid, l.ans as ans, lqa.marks as marks, l.uid as uid, lqa.q as q  from longtest l, longqa lqa where l.test_id = %s and l.email = %s and l.test_id = lqa.test_id and l.qid = lqa.qid ORDER BY qid ASC', (testid, email))
		callresults = cur.fetchall()
		cur.close()
		return render_template("insertsubmarks.html", callresults = callresults)
	if request.method == "POST":
		cur = mysql.connection.cursor()
		results1 = cur.execute('SELECT COUNT(qid) from longtest where test_id = %s and email = %s',(testid, email))
		results1 = cur.fetchone()
		cur.close()
		for sa in range(1,results1['COUNT(qid)']+1):
			marksByProfessor = request.form[str(sa)]
			cur = mysql.connection.cursor()
			cur.execute('UPDATE longtest SET marks = %s WHERE test_id = %s and email = %s and qid = %s', (marksByProfessor, testid, email, sa))
			mysql.connection.commit()
		cur.close()
		flash('Marks Entered Sucessfully!', 'success')
		return redirect(url_for('insertmarkstid'))

@app.route('/insertpracmarks/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def insertpracmarks(testid,email):
	if request.method == "GET":
		cur = mysql.connection.cursor()
		cur.execute('SELECT l.email as email, l.marks as inputmarks, l.test_id as test_id, l.qid as qid, l.code as code, l.input as input, l.executed as executed, lqa.marks as marks, l.uid as uid, lqa.q as q  from practicaltest l, practicalqa lqa where l.test_id = %s and l.email = %s and l.test_id = lqa.test_id and l.qid = lqa.qid ORDER BY qid ASC', (testid, email))
		callresults = cur.fetchall()
		cur.close()
		return render_template("insertpracmarks.html", callresults = callresults)
	if request.method == "POST":
		cur = mysql.connection.cursor()
		results1 = cur.execute('SELECT COUNT(qid) from practicaltest where test_id = %s and email = %s',(testid, email))
		results1 = cur.fetchone()
		cur.close()
		for sa in range(1,results1['COUNT(qid)']+1):
			marksByProfessor = request.form[str(sa)]
			cur = mysql.connection.cursor()
			cur.execute('UPDATE practicaltest SET marks = %s WHERE test_id = %s and email = %s and qid = %s', (marksByProfessor, testid, email, sa))
			mysql.connection.commit()
		cur.close()
		flash('Marks Entered Sucessfully!', 'success')
		return redirect(url_for('insertmarkstid'))

def displaywinstudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from window_estimation_log where test_id = %s and email = %s and window_event = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return callresults

def countwinstudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT COUNT(*) as wincount from window_estimation_log where test_id = %s and email = %s and window_event = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	winc = [i['wincount'] for i in callresults]
	return winc

def countMobStudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT COUNT(*) as mobcount from proctoring_log where test_id = %s and email = %s and phone_detection = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	mobc = [i['mobcount'] for i in callresults]
	return mobc

def countMTOPstudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT COUNT(*) as percount from proctoring_log where test_id = %s and email = %s and person_status = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	perc = [i['percount'] for i in callresults]
	return perc

def countMTOPstudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT COUNT(*) as percount from proctoring_log where test_id = %s and email = %s and person_status = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	perc = [i['percount'] for i in callresults]
	return perc

def countTotalstudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT COUNT(*) as total from proctoring_log where test_id = %s and email = %s', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	tot = [i['total'] for i in callresults]
	return tot

@app.route('/studentmonitoringstats/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def studentmonitoringstats(testid,email):
	return render_template("stat_student_monitoring.html", testid = testid, email = email)

@app.route('/ajaxstudentmonitoringstats/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def ajaxstudentmonitoringstats(testid,email):
	win = countwinstudentslogs(testid,email)
	mob = countMobStudentslogs(testid,email)
	per = countMTOPstudentslogs(testid,email)
	tot = countTotalstudentslogs(testid,email)
	return jsonify({"win":win,"mob":mob,"per":per,"tot":tot})

@app.route('/displaystudentslogs/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def displaystudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from proctoring_log where test_id = %s and email = %s', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return render_template("displaystudentslogs.html", testid = testid, email = email, callresults = callresults)

@app.route('/mobdisplaystudentslogs/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def mobdisplaystudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from proctoring_log where test_id = %s and email = %s and phone_detection = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return render_template("mobdisplaystudentslogs.html", testid = testid, email = email, callresults = callresults)

@app.route('/persondisplaystudentslogs/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def persondisplaystudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from proctoring_log where test_id = %s and email = %s and person_status = 1', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return render_template("persondisplaystudentslogs.html",testid = testid, email = email, callresults = callresults)

@app.route('/audiodisplaystudentslogs/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def audiodisplaystudentslogs(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from proctoring_log where test_id = %s and email = %s', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return render_template("audiodisplaystudentslogs.html", testid = testid, email = email, callresults = callresults)

@app.route('/wineventstudentslogs/<testid>/<email>', methods=['GET','POST'])
#@user_role_professor
def wineventstudentslogs(testid,email):
	callresults = displaywinstudentslogs(testid,email)
	return render_template("wineventstudentlog.html", testid = testid, email = email, callresults = callresults)

@app.route('/<email>/<testid>/share_details', methods=['GET','POST'])
#@user_role_professor
def share_details(testid,email):
	cur = mysql.connection.cursor()
	cur.execute('SELECT * from teachers where test_id = %s and email = %s', (testid, email))
	callresults = cur.fetchall()
	cur.close()
	return render_template("share_details.html", callresults = callresults)

@app.route('/share_details_emails', methods=['GET','POST'])
#@user_role_professor
def share_details_emails():
	if request.method == 'POST':
		tid = request.form['tid']
		subject = request.form['subject']
		topic = request.form['topic']
		duration = request.form['duration']
		start = request.form['start']
		end = request.form['end']
		password = request.form['password']
		neg_marks = request.form['neg_marks']
		calc = request.form['calc']
		emailssharelist = request.form['emailssharelist']
		msg1 = Message('EXAM DETAILS - MyProctor.ai', sender = sender, recipients = [emailssharelist])
		msg1.body = " ".join(["EXAM-ID:", tid, "SUBJECT:", subject, "TOPIC:", topic, "DURATION:", duration, "START", start, "END", end, "PASSWORD", password, "NEGATIVE MARKS in %:", neg_marks,"CALCULATOR ALLOWED:",calc ]) 
		mail.send(msg1)
		flash('Emails sended sucessfully!', 'success')
	return render_template('share_details.html')

@app.route("/publish-results-testid", methods=['GET','POST'])
#@user_role_professor
def publish_results_testid():
	cur = mysql.connection.cursor()
	results = cur.execute('SELECT * from teachers where test_type != %s AND show_ans = 0 AND email = %s AND uid = %s', ("objectve", session['email'], session['uid']))
	if results > 0:
		cresults = cur.fetchall()
		now = datetime.now()
		now = now.strftime("%Y-%m-%d %H:%M:%S")
		now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
		testids = []
		for a in cresults:
			if datetime.strptime(str(a['end']),"%Y-%m-%d %H:%M:%S") < now:
				testids.append(a['test_id'])
		cur.close()
		return render_template("publish_results_testid.html", cresults = testids)
	else:
		return render_template("publish_results_testid.html", cresults = None)

@app.route('/viewresults', methods=['GET','POST'])
#@user_role_professor
def viewresults():
	if request.method == 'POST':
		tidoption = request.form['choosetid']
		et = examtypecheck(tidoption)
		if et['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			cur.execute('SELECT SUM(marks) as marks, email from longtest where test_id = %s group by email', ([tidoption]))
			callresults = cur.fetchall()
			cur.close()
			return render_template("publish_viewresults.html", callresults = callresults, tid = tidoption)
		elif et['test_type'] == "practical":
			cur = mysql.connection.cursor()
			cur.execute('SELECT SUM(marks) as marks, email from practicaltest where test_id = %s group by email', ([tidoption]))
			callresults = cur.fetchall()
			cur.close()
			return render_template("publish_viewresults.html", callresults = callresults, tid = tidoption)
		else:
			flash("Some Error Occured!")
			return redirect(url_for('publish-results-testid'))

@app.route('/publish_results', methods=['GET','POST'])
#@user_role_professor
def publish_results():
	if request.method == 'POST':
		tidoption = request.form['testidsp']
		cur = mysql.connection.cursor()
		cur.execute('UPDATE teachers set show_ans = 1 where test_id = %s', ([tidoption]))
		mysql.connection.commit()
		cur.close()
		flash("Results published sucessfully!")
		return redirect(url_for('professor_index'))

@app.route("/upload-face", methods=["GET", "POST"])
# @user_role_student
def upload_face():
    if request.method == "POST":
        img_data = request.form.get("img_hidden_form")
        if not img_data:
            flash("No image captured!", "danger")
            return redirect(url_for("upload_face"))
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET user_image = %s WHERE email = %s AND uid = %s",
                    (img_data, session['email'], session['uid']))
        mysql.connection.commit()
        cur.close()
        flash("✅ Face image uploaded successfully!", "success")
        return redirect(url_for("student_index"))
    return render_template("upload_face.html")


@app.route('/test_update_time', methods=['GET','POST'])
#@user_role_student
def test_update_time():
	if request.method == 'POST':
		cur = mysql.connection.cursor()
		time_left = request.form['time']
		testid = request.form['testid']
		cur.execute('UPDATE studentTestInfo set time_left=SEC_TO_TIME(%s) where test_id = %s and email = %s and uid = %s and completed=0', (time_left, testid, session['email'], session['uid']))
		mysql.connection.commit()
		t1 = cur.rowcount
		cur.close()
		if t1 > 0:
			return "time recorded updated"
		else:
			cur = mysql.connection.cursor()
			cur.execute('INSERT into studentTestInfo (email, test_id,time_left,uid) values(%s,%s,SEC_TO_TIME(%s),%s)', (session['email'], testid, time_left, session['uid']))
			t2 = mysql.connection.commit()
			t2 = cur.rowcount
			cur.close()
			if t2 > 0:
				return "time recorded inserted"
			else:
				return "time error"

@app.route("/give-test", methods = ['GET', 'POST'])
#@user_role_student
def give_test():
	global duration, marked_ans, calc, subject, topic, proctortype
	form = TestForm(request.form)
	if request.method == 'POST' and form.validate():
		test_id = form.test_id.data
		password_candidate = form.password.data
		imgdata1 = form.img_hidden_form.data
		cur1 = mysql.connection.cursor()
		results1 = cur1.execute('SELECT user_image from users where email = %s and user_type = %s ', (session['email'],'student'))
		if results1 > 0:
			cresults = cur1.fetchone()
			imgdata2 = cresults['user_image']
			cur1.close()
			# ✅ Check if student has profile image stored
			if not imgdata2:
				flash("No registered face image found! Please upload your profile image before taking an exam.", "danger")
				return redirect(url_for('student_index'))
			# ✅ Decode captured image
			try:
				nparr1 = np.frombuffer(base64.b64decode(imgdata1), np.uint8)
				nparr2 = np.frombuffer(base64.b64decode(imgdata2), np.uint8)
				image1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
				image2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)
			except Exception as e:
				print("⚠️ Image decode failed:", e)
				flash("Image verification failed. Please recapture your image clearly.", "danger")
				return redirect(url_for('give_test'))
			
			img_result  = DeepFace.verify(image1, image2, enforce_detection = False)
			if img_result["verified"] == True:
				cur = mysql.connection.cursor()
				results = cur.execute('SELECT * from teachers where test_id = %s', [test_id])
				if results > 0:
					data = cur.fetchone()
					password = data['password']
					duration = data['duration']
					calc = data['calc']
					subject = data['subject']
					topic = data['topic']
					start = data['start']
					start = str(start)
					end = data['end']
					end = str(end)
					proctortype = data['proctoring_type']
					if password == password_candidate:
						now = datetime.now()
						now = now.strftime("%Y-%m-%d %H:%M:%S")
						now = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
						if datetime.strptime(start,"%Y-%m-%d %H:%M:%S") < now and datetime.strptime(end,"%Y-%m-%d %H:%M:%S") > now:
							results = cur.execute('SELECT time_to_sec(time_left) as time_left,completed from studentTestInfo where email = %s and test_id = %s', (session['email'], test_id))
							if results > 0:
								results = cur.fetchone()
								is_completed = results['completed']
								if is_completed == 0:
									time_left = results['time_left']
									if time_left <= duration:
										duration = time_left
										results = cur.execute('SELECT qid , ans from students where email = %s and test_id = %s and uid = %s', (session['email'], test_id, session['uid']))
										marked_ans = {}
										if results > 0:
											results = cur.fetchall()
											for row in results:
												print(row['qid'])
												qiddb = ""+row['qid']
												print(qiddb)
												marked_ans[qiddb] = row['ans']
												marked_ans = json.dumps(marked_ans)
								else:
									flash('Exam already given', 'success')
									return redirect(url_for('give_test'))
							else:
								cur.execute('INSERT into studentTestInfo (email, test_id,time_left,uid) values(%s,%s,SEC_TO_TIME(%s),%s)', (session['email'], test_id, duration, session['uid']))
								mysql.connection.commit()
								results = cur.execute('SELECT time_to_sec(time_left) as time_left,completed from studentTestInfo where email = %s and test_id = %s and uid = %s', (session['email'], test_id, session['uid']))
								if results > 0:
									results = cur.fetchone()
									is_completed = results['completed']
									if is_completed == 0:
										time_left = results['time_left']
										if time_left <= duration:
											duration = time_left
											results = cur.execute('SELECT * from students where email = %s and test_id = %s and uid = %s', (session['email'], test_id, session['uid']))
											marked_ans = {}
											if results > 0:
												results = cur.fetchall()
												for row in results:
													marked_ans[row['qid']] = row['ans']
												marked_ans = json.dumps(marked_ans)
						else:
							if datetime.strptime(start,"%Y-%m-%d %H:%M:%S") > now:
								flash(f'Exam start time is {start}', 'danger')
							else:
								flash(f'Exam has ended', 'danger')
							return redirect(url_for('give_test'))
						return redirect(url_for('test' , testid = test_id))
					else:
						flash('Invalid password', 'danger')
						return redirect(url_for('give_test'))
				flash('Invalid testid', 'danger')
				return redirect(url_for('give_test'))
				cur.close()
			else:
				flash('Image not Verified', 'danger')
				return redirect(url_for('give_test'))
	return render_template('give_test.html', form = form)

@app.route('/give-test/<testid>', methods=['GET','POST'])
#@user_role_student
def test(testid):
	cur = mysql.connection.cursor()
	cur.execute('SELECT test_type from teachers where test_id = %s ', [testid])
	callresults = cur.fetchone()
	cur.close()
	if callresults['test_type'] == "objective":
		global duration, marked_ans, calc, subject, topic, proctortype
		if request.method == 'GET':
			try:
				data = {'duration': duration, 'marks': '', 'q': '', 'a': '', 'b':'','c':'','d':'' }
				return render_template('testquiz.html' ,**data, answers=marked_ans, calc=calc, subject=subject, topic=topic, tid=testid, proctortype=proctortype)
			except:
				return redirect(url_for('give_test'))
		else:
			cur = mysql.connection.cursor()
			flag = request.form['flag']
			if flag == 'get':
				num = request.form['no']
				results = cur.execute('SELECT test_id,qid,q,a,b,c,d,ans,marks from questions where test_id = %s and qid =%s',(testid, num))
				if results > 0:
					data = cur.fetchone()
					del data['ans']
					cur.close()
					return json.dumps(data)
			elif flag=='mark':
				qid = request.form['qid']
				ans = request.form['ans']
				cur = mysql.connection.cursor()
				results = cur.execute('SELECT * from students where test_id =%s and qid = %s and email = %s', (testid, qid, session['email']))
				if results > 0:
					cur.execute('UPDATE students set ans = %s where test_id = %s and qid = %s and email = %s', (testid, qid, session['email']))
					mysql.connection.commit()
					cur.close()
				else:
					cur.execute('INSERT INTO students(email,test_id,qid,ans,uid) values(%s,%s,%s,%s,%s)', (session['email'], testid, qid, ans, session['uid']))
					mysql.connection.commit()
					cur.close()
			elif flag=='time':
				cur = mysql.connection.cursor()
				time_left = request.form['time']
				try:
					cur.execute('UPDATE studentTestInfo set time_left=SEC_TO_TIME(%s) where test_id = %s and email = %s and uid = %s and completed=0', (time_left, testid, session['email'], session['uid']))
					mysql.connection.commit()
					cur.close()
					return json.dumps({'time':'fired'})
				except:
					pass
			else:
				try:
					cur = mysql.connection.cursor()
					cur.execute('UPDATE studentTestInfo SET completed = 1, time_left = SEC_TO_TIME(0) WHERE test_id = %s AND email = %s AND uid = %s',(testid, session['email'], session['uid']))
					mysql.connection.commit()
					cur.close()
					flash("✅ Exam submitted successfully!", 'success')
					return redirect(url_for('student_index'))
					
				except Exception as e:
					print("❌ Error finishing exam:", e)
					flash("Something went wrong while submitting the exam.", 'danger')
					return redirect(url_for('student_index'))

	elif callresults['test_type'] == "subjective":
		if request.method == 'GET':
			cur = mysql.connection.cursor()
			cur.execute('SELECT test_id, qid, q, marks from longqa where test_id = %s ORDER BY RAND()',[testid])
			callresults1 = cur.fetchall()
			cur.execute('SELECT time_to_sec(time_left) as duration from studentTestInfo where completed = 0 and test_id = %s and email = %s and uid = %s', (testid, session['email'], session['uid']))
			studentTestInfo = cur.fetchone()
			if studentTestInfo != None:
				duration = studentTestInfo['duration']
				cur.execute('SELECT test_id, subject, topic, proctoring_type from teachers where test_id = %s',[testid])
				testDetails = cur.fetchone()
				subject = testDetails['subject']
				test_id = testDetails['test_id']
				topic = testDetails['topic']
				proctortypes = testDetails['proctoring_type']
				cur.close()
				return render_template("testsubjective.html", callresults = callresults1, subject = subject, duration = duration, test_id = test_id, topic = topic, proctortypes = proctortypes )
			else:
				cur = mysql.connection.cursor()
				cur.execute('SELECT test_id, duration, subject, topic from teachers where test_id = %s',[testid])
				testDetails = cur.fetchone()
				subject = testDetails['subject']
				duration = testDetails['duration']
				test_id = testDetails['test_id']
				topic = testDetails['topic']
				cur.close()
				return render_template("testsubjective.html", callresults = callresults1, subject = subject, duration = duration, test_id = test_id, topic = topic )
		elif request.method == 'POST':
			cur = mysql.connection.cursor()
			test_id = request.form["test_id"]
			cur = mysql.connection.cursor()
			results1 = cur.execute('SELECT COUNT(qid) from longqa where test_id = %s',[testid])
			results1 = cur.fetchone()
			cur.close()
			insertStudentData = None
			for sa in range(1,results1['COUNT(qid)']+1):
				answerByStudent = request.form[str(sa)]
				cur = mysql.connection.cursor()
				insertStudentData = cur.execute('INSERT INTO longtest(email,test_id,qid,ans,uid) values(%s,%s,%s,%s,%s)', (session['email'], testid, sa, answerByStudent, session['uid']))
				mysql.connection.commit()
			else:
				if insertStudentData > 0:
					insertStudentTestInfoData = cur.execute('UPDATE studentTestInfo set completed = 1 where test_id = %s and email = %s and uid = %s', (test_id, session['email'], session['uid']))
					mysql.connection.commit()
					cur.close()
					if insertStudentTestInfoData > 0:
						flash('Successfully Exam Submitted', 'success')
						return redirect(url_for('student_index'))
					else:
						cur.close()
						flash('Some Error was occured!', 'error')
						return redirect(url_for('student_index'))	
				else:
					cur.close()
					flash('Some Error was occured!', 'error')
					return redirect(url_for('student_index'))

	elif callresults['test_type'] == "practical":
		if request.method == 'GET':
			cur = mysql.connection.cursor()
			cur.execute('SELECT test_id, qid, q, marks, compiler from practicalqa where test_id = %s ORDER BY RAND()',[testid])
			callresults1 = cur.fetchall()
			cur.execute('SELECT time_to_sec(time_left) as duration from studentTestInfo where completed = 0 and test_id = %s and email = %s and uid = %s', (testid, session['email'], session['uid']))
			studentTestInfo = cur.fetchone()
			if studentTestInfo != None:
				duration = studentTestInfo['duration']
				cur.execute('SELECT test_id, subject, topic, proctoring_type from teachers where test_id = %s',[testid])
				testDetails = cur.fetchone()
				subject = testDetails['subject']
				test_id = testDetails['test_id']
				topic = testDetails['topic']
				proctortypep = testDetails['proctoring_type']
				cur.close()
				return render_template("testpractical.html", callresults = callresults1, subject = subject, duration = duration, test_id = test_id, topic = topic, proctortypep = proctortypep )
			else:
				cur = mysql.connection.cursor()
				cur.execute('SELECT test_id, duration, subject, topic from teachers where test_id = %s',[testid])
				testDetails = cur.fetchone()
				subject = testDetails['subject']
				duration = testDetails['duration']
				test_id = testDetails['test_id']
				topic = testDetails['topic']
				cur.close()
				return render_template("testpractical.html", callresults = callresults1, subject = subject, duration = duration, test_id = test_id, topic = topic )
		elif request.method == 'POST':
			test_id = request.form["test_id"]
			codeByStudent = request.form["codeByStudent"]
			inputByStudent = request.form["inputByStudent"]
			executedByStudent = request.form["executedByStudent"]
			cur = mysql.connection.cursor()
			insertStudentData = cur.execute('INSERT INTO practicaltest(email,test_id,qid,code,input,executed,uid) values(%s,%s,%s,%s,%s,%s,%s)', (session['email'], testid, "1", codeByStudent, inputByStudent, executedByStudent, session['uid']))
			mysql.connection.commit()
			if insertStudentData > 0:
				insertStudentTestInfoData = cur.execute('UPDATE studentTestInfo set completed = 1 where test_id = %s and email = %s and uid = %s', (test_id, session['email'], session['uid']))
				mysql.connection.commit()
				cur.close()
				if insertStudentTestInfoData > 0:
					flash('Successfully Exam Submitted', 'success')
					return redirect(url_for('student_index'))
				else:
					cur.close()
					flash('Some Error was occured!', 'error')
					return redirect(url_for('student_index'))	
			else:
				cur.close()
				flash('Some Error was occured!', 'error')
				return redirect(url_for('student_index'))

@app.route('/randomize', methods = ['POST'])
def random_gen():
	if request.method == "POST":
		id = request.form['id']
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT count(*) from questions where test_id = %s', [id])
		if results > 0:
			data = cur.fetchone()
			total = data['count(*)']
			nos = list(range(1,int(total)+1))
			random.Random(id).shuffle(nos)
			cur.close()
			return json.dumps(nos)

@app.route('/<email>/<testid>')
#@user_role_student
def check_result(email, testid):
	if email == session['email']:
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT * FROM teachers where test_id = %s', [testid])
		if results>0:
			results = cur.fetchone()
			check = results['show_ans']
			if check == 1:
				results = cur.execute('select q,a,b,c,d,marks,q.qid as qid, \
					q.ans as correct, ifnull(s.ans,0) as marked from questions q left join \
					students s on  s.test_id = q.test_id and s.test_id = %s \
					and s.email = %s and s.uid = %s and s.qid = q.qid group by q.qid \
					order by LPAD(lower(q.qid),10,0) asc', (testid, email, session['uid']))
				if results > 0:
					results = cur.fetchall()
					return render_template('tests_result.html', results= results)
			else:
				flash('You are not authorized to check the result', 'danger')
				return redirect(url_for('tests_given',email = email))
	else:
		return redirect(url_for('student_index'))

def neg_marks(email,testid,negm):
	cur=mysql.connection.cursor()
	results = cur.execute("select marks,q.qid as qid, \
				q.ans as correct, ifnull(s.ans,0) as marked from questions q inner join \
				students s on  s.test_id = q.test_id and s.test_id = %s \
				and s.email = %s and s.qid = q.qid group by q.qid \
				order by q.qid asc", (testid, email))
	data=cur.fetchall()

	sum=0.0
	for i in range(results):
		if(str(data[i]['marked']).upper() != '0'):
			if(str(data[i]['marked']).upper() != str(data[i]['correct']).upper()):
				sum=sum - (negm/100) * int(data[i]['marks'])
			elif(str(data[i]['marked']).upper() == str(data[i]['correct']).upper()):
				sum+=int(data[i]['marks'])
	return sum

def totmarks(email,tests): 
	cur = mysql.connection.cursor()
	for test in tests:
		testid = test['test_id']
		results=cur.execute("select neg_marks from teachers where test_id=%s",[testid])
		results=cur.fetchone()
		negm = results['neg_marks']
		data = neg_marks(email,testid,negm)
		return data

def marks_calc(email,testid):
		cur = mysql.connection.cursor()
		results=cur.execute("select neg_marks from teachers where test_id=%s",[testid])
		results=cur.fetchone()
		negm = results['neg_marks']
		return neg_marks(email,testid,negm) 
		
@app.route('/<email>/tests-given', methods = ['POST','GET'])
#@user_role_student
def tests_given(email):
	if request.method == "GET":
		if email == session['email']:
			cur = mysql.connection.cursor()
			resultsTestids = cur.execute('select studenttestinfo.test_id as test_id from studenttestinfo,teachers where studenttestinfo.email = %s and studenttestinfo.uid = %s and studenttestinfo.completed=1 and teachers.test_id = studenttestinfo.test_id and teachers.show_ans = 1 ', (session['email'], session['uid']))
			resultsTestids = cur.fetchall()
			cur.close()
			return render_template('tests_given.html', cresults = resultsTestids)
		else:
			flash('You are not authorized', 'danger')
			return redirect(url_for('student_index'))
	if request.method == "POST":
		tidoption = request.form['choosetid']
		cur = mysql.connection.cursor()
		cur.execute('SELECT test_type from teachers where test_id = %s',[tidoption])
		callresults = cur.fetchone()
		cur.close()
		if callresults['test_type'] == "objective":
			cur = mysql.connection.cursor()
			results = cur.execute('select distinct(students.test_id) as test_id, students.email as email, subject,topic,neg_marks from students,studenttestinfo,teachers where students.email = %s and teachers.test_type = %s and students.test_id = %s and students.test_id=teachers.test_id and students.test_id=studenttestinfo.test_id and studenttestinfo.completed=1', (email, "objective", tidoption))
			results = cur.fetchall()
			cur.close()
			results1 = []
			studentResults = None
			for a in results:
				results1.append(neg_marks(a['email'],a['test_id'],a['neg_marks']))
				studentResults = zip(results,results1)
			return render_template('obj_result_student.html', tests=studentResults)
		elif callresults['test_type'] == "subjective":
			cur = mysql.connection.cursor()
			studentResults = cur.execute('select SUM(longtest.marks) as marks, longtest.test_id as test_id, teachers.subject as subject, teachers.topic as topic from longtest,teachers,studenttestinfo where longtest.email = %s and longtest.test_id = %s and longtest.test_id=teachers.test_id and studenttestinfo.test_id=teachers.test_id and longtest.email = studenttestinfo.email and studenttestinfo.completed = 1 and teachers.show_ans=1 group by longtest.test_id', (email, tidoption))
			studentResults = cur.fetchall()
			cur.close()
			return render_template('sub_result_student.html', tests=studentResults)
		elif callresults['test_type'] == "practical":
			cur = mysql.connection.cursor()
			studentResults = cur.execute('select SUM(practicaltest.marks) as marks, practicaltest.test_id as test_id, teachers.subject as subject, teachers.topic as topic from practicaltest,teachers,studenttestinfo where practicaltest.email = %s and practicaltest.test_id = %s and practicaltest.test_id=teachers.test_id and studenttestinfo.test_id=teachers.test_id and practicaltest.email = studenttestinfo.email and studenttestinfo.completed = 1 and teachers.show_ans=1 group by practicaltest.test_id', (email, tidoption))
			studentResults = cur.fetchall()
			cur.close()
			return render_template('prac_result_student.html', tests=studentResults)
	else:
		flash('You are not authorized', 'danger')
		return redirect(url_for('student_index'))

@app.route('/<email>/tests-created')
#@user_role_professor
def tests_created(email):
	if email == session['email']:
		cur = mysql.connection.cursor()
		results = cur.execute('select * from teachers where email = %s and uid = %s and show_ans = 1', (email,session['uid']))
		results = cur.fetchall()
		return render_template('tests_created.html', tests=results)
	else:
		flash('You are not authorized', 'danger')
		return redirect(url_for('professor_index'))

@app.route('/<email>/tests-created/<testid>', methods = ['POST','GET'])
#@user_role_professor
def student_results(email, testid):
	if email == session['email']:
		et = examtypecheck(testid)
		if request.method =='GET':
			if et['test_type'] == "objective":
				cur = mysql.connection.cursor()
				results = cur.execute('select users.name as name,users.email as email, studentTestInfo.test_id as test_id from studentTestInfo, users where test_id = %s and completed = 1 and  users.user_type = %s and studentTestInfo.email=users.email ', (testid,'student'))
				results = cur.fetchall()
				cur.close()
				final = []
				names = []
				scores = []
				count = 1
				for user in results:
					score = marks_calc(user['email'], user['test_id'])
					user['srno'] = count
					user['marks'] = score
					final.append([count, user['name'], score])
					names.append(user['name'])
					scores.append(score)
					count+=1
				return render_template('student_results.html', data=final, labels=names, values=scores)
			elif et['test_type'] == "subjective":
				cur = mysql.connection.cursor()
				results = cur.execute('select users.name as name,users.email as email, longtest.test_id as test_id, SUM(longtest.marks) AS marks from longtest, users where longtest.test_id = %s  and  users.user_type = %s and longtest.email=users.email', (testid,'student'))
				results = cur.fetchall()
				cur.close()
				names = []
				scores = []
				for user in results:
					names.append(user['name'])
					scores.append(user['marks'])
				return render_template('student_results_lqa.html', data=results, labels=names, values=scores)
			elif et['test_type'] == "practical":
				cur = mysql.connection.cursor()
				results = cur.execute('select users.name as name,users.email as email, practicaltest.test_id as test_id, SUM(practicaltest.marks) AS marks from practicaltest, users where practicaltest.test_id = %s  and  users.user_type = %s and practicaltest.email=users.email', (testid,'student'))
				results = cur.fetchall()
				cur.close()
				names = []
				scores = []
				for user in results:
					names.append(user['name'])
					scores.append(user['marks'])
				return render_template('student_results_pqa.html', data=results, labels=names, values=scores)

@app.route('/<email>/disptests')
#@user_role_professor
def disptests(email):
	if email == session['email']:
		cur = mysql.connection.cursor()
		results = cur.execute('select * from teachers where email = %s and uid = %s', (email,session['uid']))
		results = cur.fetchall()
		return render_template('disptests.html', tests=results)
	else:
		flash('You are not authorized', 'danger')
		return redirect(url_for('professor_index'))

@app.route('/<email>/student_test_history')
#@user_role_student
def student_test_history(email):
	if email == session['email']:
		cur = mysql.connection.cursor()
		results = cur.execute('SELECT a.test_id, b.subject, b.topic \
			from studenttestinfo a, teachers b where a.test_id = b.test_id and a.email=%s  \
			and a.completed=1', [email])
		results = cur.fetchall()
		return render_template('student_test_history.html', tests=results)
	else:
		flash('You are not authorized', 'danger')
		return redirect(url_for('student_index'))

@app.route('/test_generate', methods=["GET", "POST"])
#@user_role_professor
def test_generate():
	if request.method == "POST":
		inputText = request.form["itext"]
		testType = request.form["test_type"]
		noOfQues = request.form["noq"]
		if testType == "objective":
			objective_generator = ObjectiveTest(inputText,noOfQues)
			question_list, answer_list = objective_generator.generate_test()
			testgenerate = zip(question_list, answer_list)
			return render_template('generatedtestdata.html', cresults = testgenerate)
		elif testType == "subjective":
			subjective_generator = SubjectiveTest(inputText,noOfQues)
			question_list, answer_list = subjective_generator.generate_test()
			testgenerate = zip(question_list, answer_list)
			return render_template('generatedtestdata.html', cresults = testgenerate)
		else:
			return None

if __name__ == "__main__":
	app.run(host = "127.0.0.1",debug=True)
