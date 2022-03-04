# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from datetime import datetime

from apps import db, login_manager

from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    # photo = db.Column(db.String)
    # role = db.Column(db.String(64), default='user') ## role {'user', 'docter', 'worker', 'teacher'}

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None


# -------------------------STUDENT--------------------------------

class Student(db.Model):

    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    date_birth = db.Column(db.Date)
    address = db.Column(db.String(100))
    xa = db.Column(db.String(100))
    quan = db.Column(db.String(100))
    city = db.Column(db.String(100))
    email = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(64), nullable=False)
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if property == 'date_birth':
                value = datetime.strptime(value, '%Y-%m-%d')
                
            setattr(self, property, value)

# -------------------------TEACHER--------------------------------

class Teacher(db.Model):

    __tablename__ = 'teacher'

    id = db.Column(db.Integer, primary_key=True)
    teacher_code = db.Column(db.String(30), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    date_birth = db.Column(db.Date)
    address = db.Column(db.String(100))
    xa = db.Column(db.String(100))
    quan = db.Column(db.String(100))
    city = db.Column(db.String(100))
    email = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(64), nullable=False)
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if property == 'date_birth':
                value = datetime.strptime(value, '%Y-%m-%d')

            setattr(self, property, value)

# -------------------------CATEGORY--------------------------------

class Category(db.Model):

    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(600), unique=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)

            setattr(self, property, value)

# -------------------------COURSE--------------------------------

class Course(db.Model):

    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(600))
    category_id = db.Column(db.Integer, ForeignKey(Category.id), nullable=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)

            setattr(self, property, value)

# -------------------------WEEKDAY--------------------------------

class Weekday(db.Model):

    __tablename__ = 'weekday'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(600))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)

            setattr(self, property, value)

# -------------------------CLASS--------------------------------

class Class(db.Model):

    __tablename__ = 'class'

    id = db.Column(db.Integer, primary_key=True)
    lesson = db.Column(db.String(600), unique=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    teacher_id = db.Column(db.Integer, ForeignKey(Teacher.id), nullable=False)
    course_id = db.Column(db.Integer, ForeignKey(Course.id), nullable=False)

    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if property=='start_date' or property=='end_date':
                value = datetime.strptime(value, '%Y-%m-%d')

            setattr(self, property, value)

# -------------------------CLASS_STUDENT--------------------------------

class ClassStudent(db.Model):

    __tablename__ = 'class_student'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, ForeignKey(Class.id), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey(Student.id), nullable=False)
    
    PrimaryKeyConstraint('class_id', 'student_id')
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)

# -------------------------CLASS_WEEKDAY--------------------------------

class ClassWeekday(db.Model):

    __tablename__ = 'class_weekday'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, ForeignKey(Class.id), nullable=False)
    weekday_id = db.Column(db.Integer, ForeignKey(Weekday.id), nullable=False)
    hours = db.Column(db.String(600))
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)

# -------------------------ATTENDANCE--------------------------------

class Attendance(db.Model):

    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(600))
    class_id = db.Column(db.Integer, ForeignKey(Class.id), nullable=False)
    weekday_id = db.Column(db.Integer, ForeignKey(Weekday.id), nullable=False)
    student_id = db.Column(db.Integer, ForeignKey(Student.id), nullable=False)

    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)

    def __init__(self, status, class_id, weekday_id, student_id):
        self.status = status
        self.class_id = class_id
        self.weekday_id = weekday_id
        self.student_id = student_id
