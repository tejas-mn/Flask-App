from settings import db

##########################--Data-Table-SETUP--###############################

class Data(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    desc = db.Column(db.String(100))
    deadline = db.Column(db.String(100))
    date=db.Column(db.String(100))
    status=db.Column(db.String(100))
    username=db.Column(db.String(100))
    serial_no = db.Column(db.Integer)
    days_left=db.Column(db.Integer)
    
    def __init__(self, name, desc, deadline,date,status,username,serial_no,days_left):
        self.name = name
        self.desc = desc
        self.deadline = deadline
        self.date=date
        self.status=status
        self.username=username
        self.serial_no=serial_no
        self.days_left = days_left

##########################--UserData-Table-SETUP--###############################

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100),unique=True)
    email = db.Column(db.String(100),unique = True)
    password = db.Column(db.String(100))
    pic = db.Column(db.String(100))

    def __init__(self, username, email, password,pic):
        self.username = username
        self.email = email
        self.password = password
        self.pic = pic
        