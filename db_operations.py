from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from settings import db
from Models import Data, UserData

#found or not found todo
def getTodo(id):
    todo = Data.query.get(id)
    return todo

#add todo to db
def createTodo():
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
def updateTodo(id, todo):
    new_todo = getTodo(id)
    new_todo.name = todo.name
    new_todo.desc = todo.desc
    new_todo.deadline = todo.deadline
    new_todo.date = todo.date
    new_todo.status = todo.status
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
def getTodoByUser(username):
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
def createUser():
    new_user = UserData(username, email, password, pic)
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

#user with email not found
#old password same as new password
def updateUserPassword(email, new_password):
    res = UserData.query.filter(UserData.email == email).first()

    if res:
        res.password = sha256_crypt.hash(str(new_password))
        db.session.commit()
    else:
        pass
