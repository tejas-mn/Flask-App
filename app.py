from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, make_response,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
from shutil import copyfile
from datetime import date,datetime
import urllib.request
import os
import logging
import git

from settings import app, COOKIE_TIME_OUT, ALLOWED_EXTENSIONS
from Models import*
from db_operations import *
global Data_Paginate

##################################--Git WebHook--#########################################

@app.route('/git_update', methods=['POST'])
def webhook():
    repo = git.Repo('./mysite/Flask-App/')
    origin = repo.remotes.origin
    #repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    origin.pull()
    return '', 200

##################################--Check-if-loggedin-####################################

#Decorator function to check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#######################################---Home--##########################################

@app.route("/")
@app.route("/home")
def home():
    return render_template("/Todo/home.html" ,title="Home" )

######################################---Dashboard--######################################

def update_days_left():
    res = Data.query.filter(Data.username == session['username']).all()
    current_date = date.today()
    
    for row in res:
        #print(row.deadline)
        deadline_date = datetime.strptime(row.deadline, "%Y-%m-%d").date()
        days_left = (str(deadline_date - current_date))
        
        #print(row.deadline,days_left)
        if deadline_date != current_date:
            days_left = int(days_left.split(' ')[0])
        else:
            days_left = 0
        row.days_left = days_left
    db.session.commit()

def set_image(usr_dir):
    #Query user data based on current user
    res=UserData.query.filter(UserData.username==(session['username'])).first()

    #Create user directory for each username if it doesnt exists
    if(not(os.path.exists(usr_dir))):
        os.mkdir(usr_dir)

    #file locations to be copied
    original = app.config['UPLOAD_FOLDER'] + '/' + 'default.jpg'
    target = usr_dir + '/' + 'default.jpg'

    #copy default.jpg(if exitsts) to user directory
    if(not(os.path.exists(target)) and os.path.exists(original)):
        copyfile(original,target)
    
    #if the user uploaded pic does not exists set it to default.jpg
    if(os.path.exists(usr_dir + '/' + res.pic)):
        return res.pic
    else:
        return "default.jpg"

@app.route("/dashboard/")
@is_logged_in
def red():
    return redirect(url_for('myform',page_num=1))

@app.route("/dashboard/<int:page_num>")
@is_logged_in
def myform(page_num):
    global Data_Paginate

    #Update the days left 
    update_days_left()

    #Set Image
    logger = logging.getLogger("my-logger")
    logger.info("CWD: " + os.getcwd())
    usr_dir = app.config['UPLOAD_FOLDER']+'/'+session['username']
    image = set_image(usr_dir)

    #Get item to be searched  
    search = request.args.get("txt")

    if search:
        search_results = searchUserTodo(session["username"], search)
        SearchData = getPaginatedItems(search_results, 10, page_num)
        
        #request.referrer gives the link from where you came to this route
        #If search request came from dashboard
        #Got to page 1 of search result
        if "?txt" not in request.referrer:          
            SearchData = getPaginatedItems(search_results, 10, 1)
        
        return render_template("/Todo/index.html", Data=Data, Data_Paginate=SearchData ,txt=search,UserData = UserData, title="Search Results", image=image, usr_dir = usr_dir)
    
    Data_Paginate = filterTodosByUserName(session["username"])
    Data_Paginate = getPaginatedItems(Data_Paginate, 10, page_num)

    return render_template("/Todo/index.html", Data=Data, Data_Paginate=Data_Paginate ,UserData = UserData, title="Dashboard", image=image, usr_dir = usr_dir)

####################################--Add-New-Page--######################################

@app.route('/addnew')
@is_logged_in
def addnew():
    return render_template("/Todo/addnew.html",title="New Todo")

################################--Insert-Data--###########################################

@app.route('/insert', methods = ['GET','POST'])
@is_logged_in
def insert():
    name = request.form.get('name')
    desc = request.form.get('desc')
    deadline= request.form.get('deadline')
    date_created = request.form.get('date')
    createTodo(name, desc, deadline, date_created, session["username"])
    flash("Added New Record")
    return redirect(url_for('myform', page_num = Data_Paginate.pages))

######################################--Update-Page--#####################################

@app.route('/update/<id>', methods = ['GET', 'POST'])
@is_logged_in
def update(id):
    if not isValidTodoIdForUser(int(id), session["username"]):
        return render_template("/Errors/404.html", title="Record not found"), 404

    return render_template("/Todo/update.html", id=id, Data=Data , title="Update")

######################################--Edit-Data--#######################################

@app.route('/edit', methods = ['GET', 'POST'])
@is_logged_in
def edit():
    id = request.form.get('id')
    name = request.form.get('name')
    desc = request.form.get('desc')
    deadline= request.form.get('deadline')
    date=request.form.get('date')
    status=request.form.get('status')

    updateTodo(id, name, desc, deadline, date, status)
    
    flash("Updated Existing Record")
    return redirect(url_for('myform',page_num=Data_Paginate.page))

######################################--Delete-Data--#####################################

@app.route('/delete/<id>/', methods = ['GET', 'POST'])
@is_logged_in
def delete(id):
    if not isValidTodoIdForUser(int(id), session["username"]):
        return render_template("/Errors/404.html",title="Record not found"), 404

    deleteTodo(id)

    flash("Deleted")
    return redirect(url_for('myform',page_num=Data_Paginate.page))

########################################--Details--#######################################

@app.route("/details/<id>/")
@is_logged_in
def details(id):
    if not isValidTodoIdForUser(int(id), session["username"]):
        return render_template("/Errors/404.html",title="Record not found"), 404

    return render_template("/Todo/details.html",id=id,Data=Data,title="Details" ,UserData=UserData)

######################################--Delete-All--######################################

@app.route('/deleteall/')
@is_logged_in
def deleteall():
    deleteAllTodosOfUser(session["username"])
    flash("Deleted All Records!!")
    return redirect(url_for('myform',page_num=1))

#####################################--Signin--###########################################

@app.route('/signin/' , methods = ['GET', 'POST'])
def signin():
    if request.method == "POST":
        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        try:
            createUser({"username" : username, "email" : email, "password" : password})
        except IntegrityError:
            flash("Username/Email already exists! Try different name")
            return redirect(url_for('signin'))

        flash("Signin Successfull!! Please Login")
        return redirect(url_for('login'))

    return render_template("/Auth/signin.html", title="Signin")

#####################################--Login--############################################

@app.route('/login/' ,methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        remember = request.form.get("remember")

        #Continue if username and password is found in cookie
        if 'usr' in request.cookies and 'pwd' in request.cookies:
            
            #Get username and password from cookies
            username_from_cookie = request.cookies.get('usr')
            password_from_cookie = request.cookies.get('pwd')

            if password == password_from_cookie and username == username_from_cookie:
                user = getUserByName(username_from_cookie)

                if user is not None:
                    # Get stored hash
                    actual_password = user.password

                    # Compare Passwords
                    #if sha256_crypt.verify(password_from_cookie, password):
                    if password_from_cookie == actual_password:
                        # Passed
                        session['logged_in'] = True
                        session['username'] = username_from_cookie
                        
                        flash('You are now logged in', 'success')
                        return redirect(url_for('red'))
                    else:
                        return render_template("/Auth/login.html", msg="Invalid password Details")
                else:
                    return render_template("/Auth/login.html", msg="Invalid email/Password Details", title="Login")
            else:
                return render_template("/Auth/login.html", msg="Invalid email/Password Details", title="Login")

        #If cookie doesn't exist
        elif username and password:

            #Get user data of the entered username
            user = getUserByName(username)
            
            if user is not None:
                # Get stored hash
                actual_password = user.password

                # Compare Passwords
                if sha256_crypt.verify(password, actual_password):
                    #Set the session values
                    session['logged_in'] = True
                    session['username'] = username

                    #If user has clicked remember me set the cookies
                    if remember:
                        response = make_response(redirect('/dashboard'))
                        response.set_cookie('usr', username, max_age=COOKIE_TIME_OUT)
                        response.set_cookie('pwd', actual_password, max_age=COOKIE_TIME_OUT)
                        response.set_cookie('rem', 'on', max_age=COOKIE_TIME_OUT)
                        return response

                    flash('Hello, You are now logged in', 'success')
                    return redirect(url_for('red'))
                else:
                    return render_template("/Auth/login.html", msg="Invalid password Details")
            else:
                return render_template("/Auth/login.html", msg="Invalid email/Password Details", title="Login")

    else:
        return render_template("/Auth/login.html", title="Login")

#######################################--Logout--#########################################

@app.route('/logout')
@is_logged_in
def logout():
    #Clear the session once user logs out
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

########################################--Forgot-Password--##############################

@app.route('/forgot' , methods = ['POST'])
def forgot():
    email = request.form.get('email')
    new_password = request.form.get('new_password')

    if updateUserPassword(email, new_password): 
        flash("Password reset successfully!! Please enter the new password")
        return jsonify({"status":"Password reset successfully"})
    else:
        return jsonify({"status":"Incorrect Email"})

########################################--About--#########################################

@app.route('/about/' ,methods = ['GET', 'POST'])
def about():
    return render_template("/Todo/about.html",Data=Data , title="About")

########################################--UPLOAD-IMAGE--##########################################

#Returns true if file extension is allowed else false
def allowed_file(filename):
    #print(filename.rsplit('.',1)) #list with first item as filename and 2nd item as extension
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_image' , methods = ['POST'])
def upload_image():
    #global Data_Paginate
    #check if file is sent or not
    if 'file' not in request.files:
        flash('No file part')
        return url_for('myform',page_num=Data_Paginate.page)

    #Get the file
    file = request.files['file']

    #if filename is empty
    if file.filename == '':
        flash('No image selected')
        return redirect(request.url)

    #If file exists and it is allowed
    if file and allowed_file(file.filename):

        #Get the user directory and filename
        usr_dir = app.config['UPLOAD_FOLDER']+'/'+session['username']
        filename=secure_filename(file.filename)

        #Save the file
        file.save(os.path.join(usr_dir, filename))

        #Removes the previous profile pic(if its not default.jpg and prev pic !=current filename) and updates the pic to current filename in the database
        res=UserData.query.filter(UserData.username==(session['username'])).first()
        if res:
            try:
                if(res.pic!="default.jpg"  and res.pic!=filename):
                    os.remove(os.path.join(usr_dir,res.pic))
            except :
                pass
            res.pic=filename
            db.session.commit()

        flash('IMAGE UPLOADED')
        return redirect(url_for('myform',page_num=Data_Paginate.page))
    else:
        flash("Allowed Image Types - [jpg, png, jpeg, gif]")
        return redirect(url_for('myform',page_num=Data_Paginate.page))

#######################################--Dues--##########################################
@app.route('/dues')
@is_logged_in
def dues():
    return render_template("/Todo/display_dues.html", Data=Data,title="Dues" ,UserData=UserData )
########################################--MAIN--##########################################

if __name__ =='__main__':
    app.run(debug = True)
