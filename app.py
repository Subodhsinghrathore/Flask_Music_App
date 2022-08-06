from flask import Flask,render_template,flash,redirect,url_for,session,logging,request

app=Flask(__name__)

if __name__=='__main__':
	app.secret_key='secret123'
	app.run(debug=True)