from flask import Flask, session, request, render_template, redirect, flash, url_for, g
from wtforms import Form,validators, StringField, SubmitField, PasswordField
from wtforms.validators import Length
import os
from flaskext.mysql import MySQL 
import datetime

mysql = MySQL()
app = Flask(__name__)
app.config['SECRET_KEY'] = '7d441f27d44'
app.config["MYSQL_DATABASE_USER"] = 'root'
app.config["MYSQL_DATABASE_PASSWORD"] = ''
app.config["MYSQL_DATABASE_DB"] = 'file_manager'
app.config["MYSQL_DATABASE_HOST"] = 'localhost'
mysql.init_app(app)
APP_ROOT = os.path.dirname(os.path.abspath(__file__)) #Path of app


class RegisterForm(Form):
	mail = StringField(validators=[Length(min =6, max=100)])
	username = StringField(validators=[Length(min =6, max=20)])
	password = PasswordField(validators=[Length(min =6, max=20)])
	confirm_password = PasswordField(validators=[Length(min =6, max=20)])
	button = SubmitField('Register')

class LoginForm(Form):
	username = StringField(validators=[Length(min =6, max=100)])
	password = PasswordField(validators=[Length(min =6, max=20)])
	button = SubmitField('Log In')

@app.before_request
def before_request(): #Function that checks if there is an active session 
	g.user = None
	if 'user' in session:
		g.user = session['user']

@app.route("/")
def index():
	if g.user:
		return redirect(url_for('profile'))
	form = RegisterForm(request.form)
	return render_template("index.html", form = form, options = ['Register' ,'Login'])


@app.route("/Register/")
def Register():
	form = RegisterForm(request.form)
	return render_template("index.html", form = form, options = ['Register' ,'Login'])
	


@app.route("/" ,methods =['POST'])
def CreateUser():
	a=0 #Variable to confirm that the password is correct
	b=0
	c=0
	d=0
	form = RegisterForm(request.form)
	email = request.form['mail']
	username = request.form['username']
	password = request.form['password']
	confirm = request.form ['confirm_password']

	#My way to check if the password has the enough specifications such as 1 Upper, and 1 Digit and be at least 6 letters long without spaces
	for x in password:
		if(x.upper() and b==0):
			a= a+1
			b=+1
		if(x == " "):
			a=0
			break
		if(x.lower() and c==0):
			a=a+1
			c=+1
		if(x.isdigit() and d==0):
			a=a+1
			d=+1
	print(a)
	if form.validate():
		if(password == confirm and a==3):
			conn = mysql.connect() #Connection to mysql
			cursor = conn.cursor()
			cursor.execute("SELECT * FROM users WHERE username='" + username+ "' OR mail='"+email +"'")
			data = cursor.fetchone()

			#This query is goiung to check for me if there is somebody with that username or email

			if data is None:
				#If nobody is signed with those credentials you can insert such username and start the session 
				cursor.execute("""INSERT INTO users (mail,username,password) VALUES (%s,%s,%s)""", (email, username, password))
				conn.commit() #To execute a insert to query
				session.pop('user', None)
				session['user'] = username
				cursor.close()
				conn.close()
				return redirect(url_for('profile'))
			else:
				cursor.close()
				conn.close()
				flash(username + " is already signed in the page. Try to log in " )
				return redirect(url_for('index'))
		else:
			flash("Password must have one Uppercase and one digit")
	else:
		flash("Please fill out to register")
				

			
				
	
	return  render_template("index.html", form = form, options = ['Register' ,'Login'])

		

@app.route("/Login/" ,methods=['POST', 'GET'])
def Login():
	if g.user:
		return redirect(url_for('profile'))
	form = LoginForm(request.form)
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		cursor = mysql.connect().cursor()
		cursor.execute("SELECT username, password FROM users WHERE username='"+username+"' AND password='"+password+"'")
		results = cursor.fetchone()
		if results is None:
			#If there ar no username and pass with those specifications it has to be incorrect
			flash("Username or Password Incorrect")
			cursor.close()
			return redirect(url_for('Login'))
		else:
			cursor.close()
			session['user'] = username
			print(session['user'])
			return redirect(url_for('profile'))


	return render_template("login.html", form = form, options=['Register', 'Login'] )

@app.route("/file_manager/" ,methods=['GET'])
def profile():
	#If you get in into the page and you do not have an active session is going to send you to Login.
	# I could have use either session or g.user in the if
	if 'user' in session:
		print(session['user'])
		g.user = session['user']
		cursor = mysql.connect().cursor()
		cursor.execute("SELECT t1.hour, t1.name ,t1.id_user FROM (SELECT id_user, name , hour FROM files) as t1 INNER JOIN (SELECT id_user FROM users WHERE username='"+g.user+"') as t2 ON t1.id_user = t2.id_user")
		#The query checks all the files in the files tables and if there are related to witch user id 
		results = cursor.fetchall()
		cursor.close()

	else:
		return redirect(url_for('Login'))
		print("Entre aqui")
		

	return render_template("profile.html", results=results)

@app.route("/file_manager/", methods=['POST'])
def file_delete():

	#Deleting files in database and directory
	file = request.form['fdelete']
	user_id = request.form['id_delete']
	print("Entre")
	print(file)
	print(user_id)
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("DELETE FROM files WHERE name='"+file+"' AND id_user="+user_id)
	conn.commit()
	cursor.close()
	conn.close() 
	str(user_id)
	target = os.path.join(APP_ROOT,"users/"+user_id+"/")
	destination = "/".join([target,file])
	print(destination)
	os.remove(destination)
	print("File Removed")
	return redirect(url_for('profile'))

@app.route("/upload/", methods=['GET', 'POST'])
def upload():
	if request.method == 'GET':
		return redirect(url_for('profile'))

	#Adding files in database and directory
	target = os.path.join(APP_ROOT, "users/") 
	if not os.path.isdir(target): 
		os.mkdir(target)
	print(target)
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT id_user FROM users WHERE username='"+g.user+"'")
	results = cursor.fetchone()
	normal = ''.join(str(x) for x in results) #Erase the tuple type of code to a normal one
	print(normal)
	if results is None:
		g.user = None
		session.pop('user', None)
		return redirect(url_for('Login'))
	else:
		target2 = os.path.join(target,normal+"/" ) 
		print(target2)
		if not os.path.isdir(target2): 
			os.mkdir(target2)
		for file in request.files.getlist("file_add"):
			a=0
			x= True
			filename = file.filename
			destination = "/".join([target2,filename])
			filename_without_ext = os.path.splitext(filename)[0]
			extension = os.path.splitext(filename)[1]

			#Checking if there are copies and adding them with an namefile(1).extension
			while (x!=False):
				if(os.path.isfile(destination)):
					a= a+1
					print(a)
					a= str(a)
					filename= filename_without_ext +"(" + a + ")"+extension
					a=int(a)
					destination = "/".join([target2,filename])
				else:
					x = False
			now = datetime.datetime.now() #Get datetime with seconds
			date = now.strftime("%Y-%m-%d %H:%M")
			file.save(destination)
			cursor.close()
			conn = mysql.connect() #Connection to mysql
			cursor = conn.cursor()
			cursor.execute("""INSERT INTO files (name,hour,id_user) VALUES (%s,%s,%s)""", (filename, date, normal))
			conn.commit() #To execute a insert to query
			cursor.close()
			conn.close()

		
	return redirect(url_for('profile'))

@app.route("/logout/" ,methods=['POST', 'GET'])
def Logout():
	session.pop('user', None)
	return redirect(url_for('Login'))



if __name__ == '__main__':
	app.run(debug= True, threaded=True)