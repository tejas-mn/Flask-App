from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from settings import db
from Models import Data, UserData
from datetime import date,datetime
from passlib.hash import sha256_crypt

#found or not found todo
def getTodo(id):
    todo = Data.query.get(id)
    return todo

#add todo to db
def createTodo( name, desc, deadline, date_created, username):
    current_date = date.today()
    status = "❌"
    deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
    days_left = (str(deadline_date - current_date))
    days_left = int(days_left.split(' ')[0])

    row = Data.query.filter(Data.username==(username))
    
    #setting serial number for each todo
    try:
        if  row[-1].serial_no != None:
            serial_no = row[-1].serial_no+1
        else:
            serial_no=1
    except IndexError:
        serial_no=1
        
    my_data = Data(
        name, desc, deadline, date_created, status, username, serial_no, days_left
    )
    
    try:
        db.session.add(my_data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

#todo not found
#if found update
def updateTodo(id, name, desc, deadline, date, status):
    todo = getTodo(id)
    todo.name = name
    todo.desc = desc
    todo.deadline = deadline
    todo.date = date
    todo.status = status
    db.session.commit()

#todo not found
def deleteTodo(id):
    todo = getTodo(id)
    db.session.delete(todo)
    db.session.commit()


#Empty or present
def deleteAllTodosOfUser(username):
    db.session.query(Data).filter(Data.username == username).delete()
    db.session.commit()
    pass

#Empty or present
def getAllTodoByUserName(username):
    result = Data.query.filter(Data.username == username).all()
    return result

#Empty or present
def getUserByName(username):
    result = UserData.query.filter(UserData.username == username).first()
    return result

#Empty or present
def getUserByEmail(email):
    result = UserData.query.filter(UserData.email == email).first()
    return result

#user with email already exist
#username is already taken
def createUser(userObj):
    new_user = UserData(userObj["username"], userObj["email"], sha256_crypt.hash(str(userObj["password"])), "default.jpg")
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

#user with email not found
#old password same as new password
def updateUserPassword(email, new_password):
    user = getUserByEmail(email)

    if user:
        user.password = sha256_crypt.hash(str(new_password))
        db.session.commit()
        return True
    else:
        return False

def update_days_left(username):
    todos = getAllTodoByUserName(username)
    current_date = date.today()
    for todo in todos:
        deadline_date = datetime.strptime(todo.deadline, "%Y-%m-%d").date()
        days_left = str(deadline_date - current_date)
        if deadline_date != current_date:
            days_left = int(days_left.split(' ')[0])
        else:
            days_left =0
            
        todo.days_left = days_left
    db.session.commit()

def searchUserTodo(username, search_text):
    search_results = Data.query.filter_by(username = username).filter(Data.name.contains(search_text))
    return search_results

def filterTodosByUserName(username):
    filtered_todos = Data.query.filter_by(username = username)
    return filtered_todos

def getPaginatedItems(todos, per_page, page_num):
    return todos.paginate(per_page = per_page, page = page_num, error_out = False)

def isValidTodoIdForUser(id, username):
    id_list=[int(todo.id) for todo in getAllTodoByUserName(username)]
    if id in id_list:
        return True
    return False
