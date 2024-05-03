from flask import render_template, redirect, url_for, flash
from app.models.User import *
import bcrypt

def index():
	try:
		get_user = User.get().serialize()
		# SELECT * FROM users
		return render_template('pages/user/index.html', users=get_user)
	except Exception as e:
		return 'Something went wrong ' + str(e)

def create():
	return render_template('pages/user/create.html')

def store(request):
	try:
		post          = request.form
		password      = bcrypt.hashpw(post['password'].encode('utf8'), bcrypt.gensalt())
		checkUsername = User.get_by_username(post['username'])
		if checkUsername == None:
			data = {
				"username" : post['username'],
				"name"     : post['name'],
				"password" : password
			}
			User.store(data)
			flash('Save success.!', 'success')
			return redirect(url_for('user_index'))
		else:
			flash('Username already registered', 'danger')
			return redirect(url_for('user_create'))
	except Exception as e:
		return 'Something went wrong ' + str(e)

def edit(id):
	try:
		data = User.find_or_fail(id).serialize()
		return render_template('/pages/user/edit.html', data=data)
	except Exception as e:
		return 'Something went wrong ' + str(e)

def update(request, id):
	try:
		post = request.form
		user = User.find(id)
		user.name     = post['name']
		user.username = post['username']
		if post['password'] != "":
			password = bcrypt.hashpw(post['password'].encode('utf8'), bcrypt.gensalt())
			user.password = password
		user.save()
		flash('Update success.!', 'success')
		return redirect(url_for('user_index'))
	except Exception as e:
		return 'Something went wrong ' + str(e)

def delete(id):
	try:
		delete = User.find(id).delete()
		flash('Delete Success.!', 'success')
		return redirect(url_for("user_index"))
	except Exception as e:
		return 'Something went wrong ' + str(e)
	