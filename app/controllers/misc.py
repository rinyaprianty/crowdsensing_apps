from flask import render_template, redirect, session, url_for, flash
from app.models.User import *
import bcrypt

def index():
	return render_template('pages/dashboard.html')

##AUTH
def login():
	if "user" in session:
		return redirect(url_for("index"))
	else:
		return render_template('pages/login.html')

def doLogin(data):
	try:
		user = User.get_by_username(data['username'])
		print(user)
		if user == None:
			flash('Username tidak terdaftar.!', 'danger')
			return redirect(url_for('login'))
		if bcrypt.checkpw(data['password'].encode('utf8'), user['password'].encode('utf8')):
			session['user'] = user
			return redirect(url_for("index"))
		else:
			flash('Password yang dimasukan salah.!', 'danger')
			return redirect(url_for('login'))
	except Exception as e:
		raise e
	

def logout():
	if "user" in session:
		session.pop("user", None)

	return redirect(url_for("login"))