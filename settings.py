from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from datetime import timedelta

##################################--FLASK-SETUP--#########################################

app=Flask(__name__)

UPLOAD_FOLDER = 'static/images'

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///customer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png','jpg','jpeg','gif'])

#app.config['SESSION_COOKIE_SAMESITE'] = 'None'
#app.config['SESSION_COOKIE_SECURE'] = True
app.secret_key="abc"

global COOKIE_TIME_OUT
COOKIE_TIME_OUT = 60*60*24*7 #7 days
#COOKIE_TIME_OUT = 60*5 #5 minutes

db=SQLAlchemy(app)
