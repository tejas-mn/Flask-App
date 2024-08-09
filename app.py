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

from settings import*
from Models import*


##################################--Git WebHook--#########################################

@app.route('/git_update', methods=['POST'])
    def webhook():
        repo = git.Repo('./Flask-App')
        origin = repo.remotes.origin
        repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
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
    data=render_template("/Todo/home.html" ,title="Home" )
    return data

######################################---Dashboard--######################################

def update_days_left():
    res = Data.query.filter(Data.username==session['username']).all()
    current_date = date.today()
    
    for row in res:
        #print(row.deadline)
        deadline_date = datetime.strptime(row.deadline, "%Y-%m-%d").date()
        days_left = (str(deadline_date - current_date))
        
        #print(row.deadline,days_left)
        if deadline_date != current_date:
            days_left = int(days_left.split(' ')[0])
        else:
            days_left =0
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
        s=Data.query.filter_by(username=session["username"]).filter(Data.name.contains(search))
        SearchData=s.paginate(per_page=10 ,page=page_num, error_out = False)
        
        #request.referrer gives the link from where you came to this route
        #If search request came from dashboard
        #Got to page 1 of search result
        if "?txt" not in request.referrer:          
            SearchData=s.paginate(per_page=10 ,page=1, error_out = False)
        
        data=render_template("/Todo/index.html", Data=Data, Data_Paginate=SearchData ,txt=search,UserData = UserData, title="Search Results", image=image, usr_dir = usr_dir)
        return data
    
    Data_Paginate = Data.query.filter_by(username=session["username"]).paginate(per_page=10,page=page_num , error_out = False)

    data=render_template("/Todo/index.html", Data=Data, Data_Paginate=Data_Paginate ,UserData = UserData, title="Dashboard", image=image, usr_dir = usr_dir)
    return data

####################################--Add-New-Page--######################################

@app.route('/addnew')
@is_logged_in
def addnew():
    data=render_template("/Todo/addnew.html",title="New Todo")
    return data

################################--Insert-Data--###########################################

@app.route('/insert', methods = ['GET','POST'])
@is_logged_in
def insert():
    #global Data_Paginate

    name = request.form.get('name')
    desc = request.form.get('desc')
    deadline= request.form.get('deadline')
    status="❌"
    date_created = request.form.get('date')
    username=session["username"]
    
    
    current_date = date.today()
    deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    days_left = (str(deadline_date - current_date))
    days_left = int(days_left.split(' ')[0])
    #print(days_left)

    row = Data.query.filter(Data.username==(username))
    #setting serial number for each user
    try:
        if  row[-1].serial_no != None:
            serial_no = row[-1].serial_no+1
        else:
            serial_no=1
    except IndexError:
        serial_no=1

    my_data = Data(name, desc, deadline,date_created,status,username,serial_no,days_left)
    db.session.add(my_data)
    db.session.commit()

    #Data_Paginate = Data.query.filter_by(username=session["username"]).paginate(per_page=10)
    
    flash("Added New Record")
    return redirect(url_for('myform',page_num=Data_Paginate.pages))

######################################--Update-Page--#####################################

@app.route('/update/<id>', methods = ['GET', 'POST'])
@is_logged_in
def update(id):
    #checks if id belongs to current user else return 404 record not found
    id_list=[int(row.id) for row in Data.query.filter(Data.username==(session["username"])).all()]
    if int(id) not in id_list:
        return render_template("/Errors/404.html",title="Record not found"),404

    data=render_template("/Todo/update.html",id=id,Data=Data , title="Update")
    return data

######################################--Edit-Data--#######################################

@app.route('/edit', methods = ['GET', 'POST'])
@is_logged_in
def edit():
    #global Data_Paginate
    my_data = Data.query.get(request.form.get('id'))
    my_data.name = request.form.get('name')
    my_data.desc = request.form.get('desc')
    my_data.deadline= request.form.get('deadline')
    my_data.date=request.form.get('date')
    my_data.status=request.form.get('status')
    db.session.commit()
    
    flash("Updated Existing Record")
    return redirect(url_for('myform',page_num=Data_Paginate.page))

######################################--Delete-Data--#####################################

@app.route('/delete/<id>/', methods = ['GET', 'POST'])
@is_logged_in
def delete(id):
    #global Data_Paginate
    #checks if id belongs to current user else return 404 record not found
    id_list=[int(row.id) for row in Data.query.filter(Data.username==(session["username"])).all()]
    if int(id) not in id_list:
        return render_template("/Errors/404.html",title="Record not found"),404

    my_data = Data.query.get(id)
    db.session.delete(my_data)
    db.session.commit()

    
    flash("Deleted")
    return redirect(url_for('myform',page_num=Data_Paginate.page))

########################################--Details--#######################################

@app.route("/details/<id>/")
@is_logged_in
def details(id):
    #checks if id belongs to current user else return 404 record not found
    id_list=[int(row.id) for row in Data.query.filter(Data.username==(session["username"])).all()]
    if int(id) not in id_list:
        return render_template("/Errors/404.html",title="Page not found"),404

    data=render_template("/Todo/details.html",id=id,Data=Data,title="Details" ,UserData=UserData)
    return data

######################################--Delete-All--######################################

@app.route('/deleteall/')
@is_logged_in
def deleteall():
    db.session.query(Data).filter(Data.username==session["username"]).delete()
    db.session.commit()
    flash("Deleted All Records!!")
    return redirect(url_for('myform',page_num=1))

#####################################--Signin--###########################################

@app.route('/signin/' , methods = ['GET', 'POST'])
def signin():
    if request.method=="POST":
        username=request.form.get("username")
        email=request.form.get("email")
        password=sha256_crypt.hash(str(request.form.get("password")))

        #Set default profile pic whenever user signin
        pic = "default.jpg"
        my_data = UserData(username, email, password,pic)
        db.session.add(my_data)

        #Ensures whether username and email are unique
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username/Email already exists! Try different name")
            return redirect(url_for('signin'))

        flash("Signin Successfull!! Please Login")
        return redirect(url_for('login'))

    return render_template("/Auth/signin.html",Data=Data,title="Signin")

#####################################--Login--############################################

@app.route('/login/' ,methods = ['GET', 'POST'])
def login():
    if request.method=="POST":
        username=request.form.get("username")
        password_candidate=request.form.get("password")
        remember = request.form.get("remember")

        #Get username and password from cookies
        usernam = request.cookies.get('usr')
        password_candidat = request.cookies.get('pwd')

        #Continue if details matches from cookies
        if 'usr' in request.cookies and (password_candidate == password_candidat) and (username == usernam):
            res=UserData.query.filter(UserData.username==(usernam)).first()

            if res is not None:
                 # Get stored hash
                password = res.password

                # Compare Passwords
                #if sha256_crypt.verify(password_candidat, password):
                if password_candidat == password:
                    # Passed
                    session['logged_in'] = True
                    session['username'] = usernam
                    
                    flash('You are now logged in', 'success')
                    return redirect(url_for('red'))
                else:
                    return render_template("/Auth/login.html",msg="Invalid password Details")
            else:

                return render_template("/Auth/login.html",msg="Invalid email/Password Details",title="Login")

        #If cookies doesnt exists
        elif username and password_candidate:

                    #Get user data of the entered username
                    res=UserData.query.filter(UserData.username==(username)).first()

                    if res is not None:
                        # Get stored hash
                        password = res.password

                        # Compare Passwords
                        if sha256_crypt.verify(password_candidate, password):
                            #Set the session values
                            session['logged_in'] = True
                            session['username'] = username

                            #If user has clicked remember me set the cookies
                            if remember:
                                resp = make_response(redirect('/dashboard'))
                                resp.set_cookie('usr',username,max_age=COOKIE_TIME_OUT)
                                resp.set_cookie('pwd',password,max_age=COOKIE_TIME_OUT)
                                resp.set_cookie('rem','on',max_age=COOKIE_TIME_OUT)
                                return resp

                            flash('You are now logged in', 'success')
                            flash("Hello")
                            return redirect(url_for('red'))
                        else:
                            return render_template("/Auth/login.html",msg="Invalid password Details")
                    else:
                        return render_template("/Auth/login.html",msg="Invalid email/Password Details",title="Login")


    if request.method=="GET":
        return render_template("/Auth/login.html",Data=Data ,title="Login")

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
    print(email,new_password)

    #Query user data based on entered email
    res=UserData.query.filter(UserData.email==(email)).first()

    if res:
        res.password=sha256_crypt.hash(str(new_password))
        db.session.commit()

        flash("Password reset successfully!! Please enter the new password")
        #Return json response to ajax call bcoz JS will recieve back redirect and render
        #template as result of call without changing DOM
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
