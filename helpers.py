from db_operations import *
from flask import  session
import os 
from shutil import copyfile
from settings import app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png','jpg','jpeg','gif'])

#Returns true if file extension is allowed else false
def allowed_file(filename):
    #print(filename.rsplit('.',1)) #list with first item as filename and 2nd item as extension
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def set_image(usr_dir):
    #Query user data based on current user
    user = getUserByName(session['username'])

    #Create user directory for each username if it does'nt exists    
    if(not(os.path.exists(usr_dir))):
        os.mkdir(usr_dir)

    #file locations to be copied
    original = app.config['UPLOAD_FOLDER'] + '/' + 'default.jpg'
    target = usr_dir + '/' + 'default.jpg'

    #copy default.jpg(if exists) to user directory
    if(not(os.path.exists(target)) and os.path.exists(original)):
        copyfile(original,target)
    
    #if the user uploaded pic does not exists set it to default.jpg
    if(os.path.exists(usr_dir + '/' + user.pic)):
        return user.pic
    else:
        return "default.jpg"
    
def upload_requested_image(request_file):
    #If file exists and it is allowed
    if request_file and allowed_file(request_file.filename):

        #Get the user directory and filename
        usr_dir = app.config['UPLOAD_FOLDER']+'/'+session['username']
        filename = secure_filename(request_file.filename)

        #Save the file
        request_file.save(os.path.join(usr_dir, filename))

        #Removes the previous profile pic(if its not default.jpg and prev pic !=current filename) and updates the pic to current filename in the database
        user = getUserByName(session['username'])
        
        if user:
            try:
                if(user.pic != "default.jpg" and user.pic != filename):
                    os.remove(os.path.join(usr_dir, user.pic))
            except:
                pass
            
            user.pic = filename
            db.session.commit()
            return True
        return False
    else:
        return False
