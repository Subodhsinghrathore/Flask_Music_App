from flask import Flask,render_template,flash,redirect,url_for,session,logging,request

app=Flask(__name__)
name1=""
usernname1=""
email1=""
password1=""
username2=""


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
    
    return render_template('register.html',form=form)



if __name__=='__main__':
	app.secret_key='secret123'
	app.run(debug=True)