from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mail import Mail,Message
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import os
from bs4 import BeautifulSoup
import requests

app=Flask(__name__)
name1=""
usernname1=""
email1=""
password1=""
username2=""

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='123subodh'
app.config['MYSQL_DB']='my_music'
app.config['MYSQL_CURSORCLASS']='DictCursor'

app.config.from_pyfile('config.cfg')
mail=Mail(app)

s=URLSafeTimedSerializer('secret123')

mysql=MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/Artists')
def artists():
    return render_template("artists.html")
@app.route('/Albums')
def albums():
    return render_template("album.html")

class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('Username',[validators.Length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='Password do not match')])
    confirm=PasswordField('confirm Password')

#register
@app.route('/register',methods=['GET','POST'])
def register():
    form =RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        global usernname1,name1,email1,password1
        usernname1=username
        name1=name
        email1=email
        password1=password

        token=s.dumps(email,salt='email-confirm')

        msg=Message('Confirm Email',sender='tejaskumar911336@gmail.com',recipients=[email])

        link=url_for('confirm_email',token=token,_external=True)

        msg.body='Your link is {}'.format(link)

        mail.send(msg)

        cur=mysql.connection.cursor()
        result=cur.execute("SELECT * FROM users WHERE username= %s",[username])
        result2=cur.execute("SELECT * FROM users WHERE email=%s",[email])
        if result>0:
            error='User name already exists,please try another user name'
            return render_template('register.html',form=form,error=error)
        if result2>0:
            error='Email already exists,please try another Email'
            return render_template('register.html',form=form,error=error)
        else:
            flash('A confirmation link has been sent to your email','success')
        return redirect(url_for('index'))

    return render_template('register.html',form=form)


#sending the confirmation link to email
@app.route('/confirm_email/<token>')
def confirm_email(token):
	cur=mysql.connection.cursor()
	try:
		email=s.loads(token,salt='email-confirm',max_age=3600)
	except SignatureExpired:
		flash('The confirmation link is invalid or has expired.','danger')
	else:
		cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name1,email1,usernname1,password1))
		mysql.connection.commit()
		cur.close()
		flash('Successfully verified','success')
	return redirect(url_for('login'))


#login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']

        password_candidate=request.form['password']

        cur=mysql.connection.cursor()

        result=cur.execute("SELECT * FROM users WHERE username= %s",[username])

        if result>0:
            data=cur.fetchone()
            password=data['password']

            if sha256_crypt.verify(password_candidate,password):
                session['logged_in']=True
                session['username']=username
                session['id']=data['id']

                flash('login successful','success')
                return redirect(url_for('dashboard'))
            else:
                error='wrong password'
            return render_template('login.html',error=error)
            cur.close()
        else:
            error='Username not found'
            return render_template('login.html',error=error)

    return render_template('login.html')

#to prevent using of app without login
def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('unauthorised,please login','danger')
			return redirect(url_for('login'))
	return wrap


#search
@app.route('/new',methods=['POST'])
def new():
	string=""
	co=request.form['give']
	song=co
	song_name=co+'.mp3'
	cur=mysql.connection.cursor()
	result=cur.execute("SELECT * FROM songs_list WHERE song_name=%s",[song_name])
	albu69=cur.fetchall()
	if result>0:
		return render_template('search.html',albu=albu69)
	else:
		try:
			page = requests.get("https://www.youtube.com/results?search_query="+song)
			soup = BeautifulSoup(page.text,'html.parser')
			for div in soup.find_all('div', { "class" : "yt-lockup-video" }):
				if div.get("data-context-item-id") != None:
					video_id = div.get("data-context-item-id")
					break
			os.system('youtube-dl --extract-audio --audio-format mp3 -o "akhil.mp3" https://www.youtube.com/watch?v='+video_id)
			os.system("mv *.mp3 ./static/music/")
			os.rename("static/music/akhil.mp3","static/music/"+song_name)
			string="/static/music/"+song_name
			cur=mysql.connection.cursor()
			cur.execute("INSERT INTO songs_list(path,album,song_name) VALUES (%s,%s,%s)",(string,"NA",song_name))
			mysql.connection.commit()
			result=cur.execute("SELECT * FROM songs_list WHERE song_name=%s",[song_name])
			albu99=cur.fetchall()
			return render_template('search.html',albu=albu99)
		except NameError:
			flash('Song Not Found','success')
			return render_template('dashboard.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
	cur=mysql.connection.cursor()

	result=cur.execute("SELECT * from songs WHERE user_id = %s",[session['id']])

	songs=cur.fetchall()

	if result>0:
		return render_template('dashboard.html',songs=songs)
	else:
		msg="NO PLAYLIST FOUND "

	return render_template('dashboard.html',msg=msg)
	cur.close()

class make_playlist(Form):
	title=StringField('Name',[validators.Length(min=1,max=25)])

@app.route('/create_playlist',methods=['GET','POST'])
@is_logged_in
def create_playlist():
	form=make_playlist(request.form)
	if request.method=='POST' and form.validate():
		title=form.title.data
		cur=mysql.connection.cursor()
		username=session['username']
		row=cur.execute("SELECT * FROM users WHERE username = %s",[username])
		result=cur.fetchone()
		idd=result['id']
		cur.execute("INSERT INTO songs(title,user_id) VALUES (%s,%s)",([title],idd,))
		cur.execute("UPDATE songs SET type=1 WHERE title=%s",([title]))
		mysql.connection.commit()
		cur.close()

		flash(idd,'success')

		return redirect(url_for('dashboard'))
	return render_template('add_playlist.html',form=form)

@app.route('/users')
@is_logged_in
def users():
	cur=mysql.connection.cursor()
	result=cur.execute("SELECT * from users")
	songs=cur.fetchall()
	if result>0:
		return render_template('Dashboard.html',songs=songs)
	else:
		msg="NO PLAYLIST FOUND "

	return render_template('Dashboard.html',msg=msg)
	cur.close()

@app.route('/users/playlist/<string:idd>')
@is_logged_in
def u_play(idd):
	cur=mysql.connection.cursor()
	result=cur.execute("SELECT * from songs WHERE user_id=%s and type=1",[idd])
	songs=cur.fetchall()
	if result>0:
		return render_template('das.html',songs=songs)
	else:
		msg="NO PLAYLIST FOUND "
	return render_template('das.html',msg=msg)
	cur.close()

@app.route('/Arijit Singh')
@is_logged_in
def play():
	cur=mysql.connection.cursor()
	cur.execute("SELECT * FROM songs_list WHERE album LIKE 'rep%'")
	albu=cur.fetchall()
	result=cur.execute("SELECT * from songs WHERE user_id = %s",[session['id']])
	songs=cur.fetchall()
	if result>0:
		return render_template('home.html',songs=songs,albu=albu)
	else:
		songs=0
		return render_template('home.html',albu=albu,song=songs)
	cur.close()
	return render_template('home.html',albu=albu)
    
@app.route('/BlackPanther')
@is_logged_in
def panther():
			cur=mysql.connection.cursor()
			cur.execute("SELECT * FROM songs_list WHERE album LIKE 'bla%'")
			albu3=cur.fetchall()
			result=cur.execute("SELECT * from songs WHERE user_id = %s",[session['id']])
			songs=cur.fetchall()
			if result>0:
				return render_template('blackpanther.html',songs=songs,albu=albu3)
			else:
				songs=0
				return render_template('blackpanther.html',albu=albu3,song=songs)
			cur.close()
			#    app.logger.info(albu[11]["path"]
			return render_template('blackpanther.html',albu=albu3)

if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
