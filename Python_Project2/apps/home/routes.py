# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from re import S
from apps.authentication.forms import CreateStudentForm, CreateTeacherForm, CreateWeekdayForm, CreateCategoryForm, CreateCourseForm, CreateClassForm, CreateClassStudentForm, CreateClassWeekdayForm, CreateAttendanceForm
from apps.authentication.models import Student, Teacher, Weekday, Category, Course, Class, ClassStudent, ClassWeekday, Attendance, Users
from apps.home import blueprint
from apps import db, login_manager, create_app
from flask import render_template, redirect, request, session, url_for, Response
from flask_login import login_required
from jinja2 import TemplateNotFound
import cv2
import dlib
import numpy as np
import os
from PIL import Image
import re

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')


#-------------------------------DIEMDANH-------------------------------------

@blueprint.route('/diemdanh/<int:id>')
def diemdanh(id):
    classw = ClassWeekday.query.filter_by(id=id).first()
    cid = classw.class_id
    wid = classw.weekday_id

    # All sinh vien co trong lop
    class_students = ClassStudent.query.filter_by(class_id=int(cid)).all()
    # All sinh vien
    students = Student.query.all()
    
    face_detector = dlib.get_frontal_face_detector()
    recognier = cv2.face.LBPHFaceRecognizer_create()
    recognier.read('recoginzer/trainningData.yml')
    fontface = cv2.FONT_HERSHEY_SIMPLEX
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            cap.release()
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)

            for face in faces:
                x1 = face.left()
                y1 = face.top()
                x2 = face.right()
                y2 = face.bottom()
                roi_gray = gray[y1: y2, x1: x2]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,225,0), 2)
                    # ss gray frame
                id, confidence = recognier.predict(roi_gray)
                    # print(id)

                if confidence < 40:
                        
                    # get msv
                    msv = None
                    for student in students:
                        if student.id == id:
                            msv = student.student_code
                            break

                    # check student trong danh sach lop
                    check = False
                    for student in class_students:
                        if student.student_id == id:
                            check = True
                            break
                    if check:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,225,0), 2)
                        cv2.putText(frame, msv, (x1, y2+30), fontface, 1, (0,225,0), 2)

                        # All sinh vien da diem danh
                        checkAtt = Attendance.query.filter_by(class_id=cid, weekday_id=wid).all()
                        # check student trong danh sach diem danh
                        check = False
                        for student in checkAtt:
                            if student.student_id == id:
                                check = True
                                break

                        if not check:
                            # Diem danh | chua co trong Attendance
                            attendance = Attendance('Đã điểm danh', cid, wid, id)
                            db.session.add(attendance)
                            db.session.commit()
                    else:
                        # K diem danh | k co trong ClassStudent
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (225,0,0), 2)
                        cv2.putText(frame, msv, (x1, y2+30), fontface, 1, (225,0,0), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,225), 2)
                    cv2.putText(frame, 'Unknow', (x1, y2+30), fontface, 1, (0,0,225), 2)

            cv2.imshow('DETECTING FACE', frame)
            if(cv2.waitKey(1) == ord("q")):
                break
    cap.release()
    cv2.destroyAllWindows()

    # All sinh vien da diem danh
    checkAtt = Attendance.query.filter_by(class_id=cid, weekday_id=wid).all()
    for cs in class_students:
        check = True
        for att in checkAtt:
            if cs.student_id == att.student_id:
                check = False
                break
        if check:
            attendance = Attendance('Vắng', cid, wid, cs.student_id)
            db.session.add(attendance)
            db.session.commit()

    return render_template('home/diemdanh.html', segment='diemdanh')


#-------------------------------GETDATA-------------------------------------

@blueprint.route('/camera/<int:id>/<string:student_code>')
def camera(id, student_code):
    return render_template('home/camera.html', segment='camera', id=id, student_code=student_code)

def training():
    recognier = cv2.face.LBPHFaceRecognizer_create()
    path = 'dataset'
    ids, faces = getImageWithMSV(path)
    recognier.train(faces, np.array(ids))

    if not os.path.exists('recoginzer'):
        os.makedirs('recoginzer')

    recognier.save('recoginzer/trainningData.yml')


def getImageWithMSV(path):
    imagePaths = [os.path.join(f) for f in os.listdir(path)]
    faces = []
    ids = []
    for imagePath in imagePaths:
        faceImg = Image.open(path+'/'+imagePath).convert('L')
        faceNp = np.array(faceImg, 'uint8')
        id = int(imagePath.split('.')[1])

        print(id, '\n', faceNp)

        faces.append(faceNp)
        ids.append(id)

    return ids, faces


def generate_frames(id, student_code):
    if not os.path.exists('dataset'):
        os.makedirs('dataset')
    face_detector = dlib.get_frontal_face_detector()
    camera = cv2.VideoCapture(0)
    count = 0
    while True:
        ## read the camera frame
        success, frame = camera.read()
        if not success or count > 99:
            camera.release()
            training()
            return redirect(url_for('home_blueprint.student'))
        # if not success:
        #     camera.release()
        #     return redirect(url_for('home_blueprint.student'))
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)
            for face in faces:
                x1 = face.left()
                y1 = face.top()
                x2 = face.right()
                y2 = face.bottom()
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,225,0), 2)
                count += 1
                cv2.imwrite('dataset/' + str(student_code) + '.' + str(id) + '.' + str(count) + '.jpg', gray[y1: y2, x1: x2])

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@blueprint.route('/video/<int:id>/<string:student_code>')
def video(id, student_code):
    return Response(generate_frames(id, student_code), mimetype='multipart/x-mixed-replace; boundary=frame')


#-------------------------------------STUDENT------------------------------------------

@blueprint.route('/student', methods=['GET', 'POST'])
def student():
    if 'delete' in request.form:
        Student.query.filter_by(id=int(request.form['delete'])).delete()
        students = Student.query.all()
        db.session.commit()
        return redirect(url_for('home_blueprint.student'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.student_profile_update', id=request.form['edit']))

    students = Student.query.all()
    return render_template('home/student.html', segment='student', students=students)


regexEmail = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
regexPhone = r'/^(^\+251|^251|^0)?9\d{8}$/'

@blueprint.route('/student_profile', methods=['GET', 'POST'])
def student_profile():
    create_student_form = CreateStudentForm(request.form)

    if 'new_student' in request.form:

        # read form data
        student_code = request.form['student_code']
        email = request.form['email']
        phone = request.form['phone']

        if  not (re.fullmatch(regexEmail,email)):
            print('\nEmail khong dung\n')
            return render_template('home/student_profile.html', segment='student_profile',
                                   msg='Email không đúng định dạng',
                                   success=False,
                                   form=create_student_form)

        student = Student.query.filter_by(student_code=student_code).first()
        if student:
            return render_template('home/student_profile.html', segment='student_profile',
                                   msg='Mã sinh viên đã tồn tại',
                                   success=False,
                                   form=create_student_form)

        student = Student.query.filter_by(email=email).first()
        if student:
            return render_template('home/student_profile.html', segment='student_profile',
                                   msg='Email đã tồn tại',
                                   success=False,
                                   form=create_student_form)

        student = Student.query.filter_by(phone=phone).first()
        if student:
            return render_template('home/student_profile.html', segment='student_profile',
                                   msg='Số điện thoại đã tồn tại',
                                   success=False,
                                   form=create_student_form)

        student = Student(**request.form)
        db.session.add(student)
        db.session.commit()
        
        return render_template('home/student_profile.html', segment='student_profile',
                               msg='Thêm sinh viên thành công <a href="/student">Student List</a>',
                               success=True,
                               form=create_student_form)


    return render_template('home/student_profile.html', segment='student_profile',
                               success=False,
                               form=create_student_form)
                            
@blueprint.route('/student_profile-update/<int:id>', methods=['GET', 'POST'])
def student_profile_update(id):
    create_student_form = CreateStudentForm(request.form)
    found_student = Student.query.filter_by(id=id).first()
    if 'update_student' in request.form:
        # read form data
        student_code = request.form['student_code']
        email = request.form['email']
        phone = request.form['phone']

        if student_code == found_student.student_code:
            student = Student.query.filter_by(student_code=student_code).first()
            if student:
                return render_template('home/student_profile.html', segment='student_profile',
                                    msg='Mã sinh viên đã tồn tại',
                                    success=False,
                                    form=create_student_form)

        if email == found_student.email:
            student = Student.query.filter_by(email=email).first()
            if student:
                return render_template('home/student_profile.html', segment='student_profile',
                                    msg='Email đã tồn tại',
                                    success=False,
                                    form=create_student_form)

        if phone == found_student.phone:
            student = Student.query.filter_by(phone=phone).first()
            if student:
                return render_template('home/student_profile.html', segment='student_profile',
                                    msg='Số điện thoại đã tồn tại',
                                    success=False,
                                    form=create_student_form)
                                   
        student = Student(**request.form)
        found_student.student_code = student.student_code
        found_student.first_name = student.first_name
        found_student.last_name = student.last_name
        found_student.date_birth = student.date_birth
        found_student.address = student.address
        found_student.xa = student.xa
        found_student.quan = student.quan
        found_student.city = student.city
        found_student.email = student.email
        found_student.phone = student.phone
        db.session.commit()

        return render_template('home/student_profile.html', segment='student_profile',
                               msg='Cập nhập sinh viên thành công <a href="/student">Student List</a>',
                               success=True,
                               form=create_student_form)

    return render_template('home/student_profile.html', segment='student_profile',
                               success=False,
                               student=found_student,
                               form=create_student_form)



#-------------------------------------TEACHER------------------------------------------

@blueprint.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if 'delete' in request.form:
        Teacher.query.filter_by(id=int(request.form['delete'])).delete()
        teachers = Teacher.query.all()
        db.session.commit()
        return redirect(url_for('home_blueprint.teacher'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.teacher_profile_update', id=request.form['edit']))

    teachers = Teacher.query.all()
    return render_template('home/teacher.html', segment='teacher', teachers=teachers)

@blueprint.route('/teacher_profile', methods=['GET', 'POST'])
def teacher_profile():
    create_teacher_form = CreateTeacherForm(request.form)

    if 'new_teacher' in request.form:

        # read form data
        teacher_code = request.form['teacher_code']
        email = request.form['email']
        phone = request.form['phone']

        teacher = Teacher.query.filter_by(teacher_code=teacher_code).first()
        if teacher:
            return render_template('home/teacher_profile.html', segment='teacher_profile',
                                   msg='Mã giảng viên đã tồn tại',
                                   success=False,
                                   form=create_teacher_form)

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher:
            return render_template('home/teacher_profile.html', segment='teacher_profile',
                                   msg='Email đã tồn tại',
                                   success=False,
                                   form=create_teacher_form)

        teacher = Teacher.query.filter_by(phone=phone).first()
        if teacher:
            return render_template('home/teacher_profile.html', segment='teacher_profile',
                                   msg='Số điện thoại đã tồn tại',
                                   success=False,
                                   form=create_teacher_form)

        teacher = Teacher(**request.form)
        db.session.add(teacher)
        db.session.commit()
        
        return render_template('home/teacher_profile.html', segment='teacher_profile',
                               msg='Thêm giảng viên thành công <a href="/teacher">Teacher List</a>',
                               success=True,
                               form=create_teacher_form)


    return render_template('home/teacher_profile.html', segment='teacher_profile',
                               success=False,
                               form=create_teacher_form)
                            
@blueprint.route('/teacher_profile-update/<int:id>', methods=['GET', 'POST'])
def teacher_profile_update(id):
    create_teacher_form = CreateTeacherForm(request.form)
    found_teacher = Teacher.query.filter_by(id=id).first()
    if 'update_teacher' in request.form:

        # read form data
        teacher_code = request.form['teacher_code']
        email = request.form['email']
        phone = request.form['phone']

        if teacher_code == found_teacher.found_teacher:
            teacher = Teacher.query.filter_by(teacher_code=teacher_code).first()
            if teacher:
                return render_template('home/teacher_profile.html', segment='teacher_profile',
                                    msg='Mã giảng viên đã tồn tại',
                                    success=False,
                                    form=create_teacher_form)

        if email == found_teacher.emal:
            teacher = Teacher.query.filter_by(email=email).first()
            if teacher:
                return render_template('home/teacher_profile.html', segment='teacher_profile',
                                    msg='Email đã tồn tại',
                                    success=False,
                                    form=create_teacher_form)

        if phone == found_teacher.phone:
            teacher = Teacher.query.filter_by(phone=phone).first()
            if teacher:
                return render_template('home/teacher_profile.html', segment='teacher_profile',
                                    msg='Số điện thoại đã tồn tại',
                                    success=False,
                                    form=create_teacher_form)


        teacher = Teacher(**request.form)
        found_teacher.teacher_code = teacher.teacher_code
        found_teacher.first_name = teacher.first_name
        found_teacher.last_name = teacher.last_name
        found_teacher.date_birth = teacher.date_birth
        found_teacher.address = teacher.address
        found_teacher.xa = teacher.xa
        found_teacher.quan = teacher.quan
        found_teacher.city = teacher.city
        found_teacher.email = teacher.email
        found_teacher.phone = teacher.phone
        db.session.commit()

        return render_template('home/teacher_profile.html', segment='teacher_profile',
                               msg='Cập nhập giảng viên thành công <a href="/teacher">Teacher List</a>',
                               success=True,
                               form=create_teacher_form)

    return render_template('home/teacher_profile.html', segment='teacher_profile',
                               success=False,
                               teacher=found_teacher,
                               form=create_teacher_form)




#-------------------------------------WEEKDAY------------------------------------------

@blueprint.route('/weekday', methods=['GET', 'POST'])
def weekday():
    if 'delete' in request.form:
        Weekday.query.filter_by(id=int(request.form['delete'])).delete()
        weekdays = Weekday.query.all()
        db.session.commit()
        return redirect(url_for('home_blueprint.weekday'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.weekday_form_update', id=request.form['edit']))

    weekdays = Weekday.query.all()
    return render_template('home/weekday.html', segment='weekday', weekdays=weekdays)

@blueprint.route('/weekday_form', methods=['GET', 'POST'])
def weekday_form():
    create_weekday_form = CreateWeekdayForm(request.form)

    if 'new_weekday' in request.form:

        weekday = Weekday(**request.form)
        db.session.add(weekday)
        db.session.commit()
        
        return render_template('home/weekday_form.html', segment='weekday_form',
                               msg='Thêm buổi học thành công <a href="/weekday">Weekday List</a>',
                               success=True,
                               form=create_weekday_form)


    return render_template('home/weekday_form.html', segment='weekday_form',
                               success=False,
                               form=create_weekday_form)
                            
@blueprint.route('/weekday_form-update/<int:id>', methods=['GET', 'POST'])
def weekday_form_update(id):
    create_weekday_form = CreateWeekdayForm(request.form)
    found_weekday = Weekday.query.filter_by(id=id).first()
    if 'update_weekday' in request.form:
        weekday = Weekday(**request.form)
        found_weekday.name = weekday.name
        db.session.commit()

        return render_template('home/weekday_form.html', segment='weekday_form',
                               msg='Cập nhập buổi học thành công <a href="/weekday">Weekday List</a>',
                               success=True,
                               form=create_weekday_form)

    return render_template('home/weekday_form.html', segment='weekday_form',
                               success=False,
                               weekday=found_weekday,
                               form=create_weekday_form)



#-------------------------------------CATEGORY------------------------------------------

@blueprint.route('/category', methods=['GET', 'POST'])
def category():
    if 'delete' in request.form:
        Category.query.filter_by(id=int(request.form['delete'])).delete()
        categories = Category.query.all()
        db.session.commit()
        return redirect(url_for('home_blueprint.category'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.category_form_update', id=request.form['edit']))

    categories = Category.query.all()
    return render_template('home/category.html', segment='category', categories=categories)

@blueprint.route('/category_form', methods=['GET', 'POST'])
def category_form():
    create_category_form = CreateCategoryForm(request.form)

    if 'new_category' in request.form:

        # read form data
        name = request.form['name']

        category = Category.query.filter_by(name=name).first()
        if category:
            return render_template('home/category_form.html', segment='category_form',
                                   msg='Bộ môn này đã tồn tại',
                                   success=False,
                                   form=create_category_form)

        category = Category(**request.form)
        db.session.add(category)
        db.session.commit()
        
        return render_template('home/category_form.html', segment='category_form',
                               msg='Thêm bộ môn thành công <a href="/category">Category List</a>',
                               success=True,
                               form=create_category_form)


    return render_template('home/category_form.html', segment='category_form',
                               success=False,
                               form=create_category_form)
                            
@blueprint.route('/category_form-update/<int:id>', methods=['GET', 'POST'])
def category_form_update(id):
    create_category_form = CreateCategoryForm(request.form)
    found_category = Category.query.filter_by(id=id).first()
    if 'update_category' in request.form:

        # read form data
        name = request.form['name']
        if name != found_category.name:
            category = Category.query.filter_by(name=name).first()
            if category:
                return render_template('home/category_form.html', segment='category_form',
                                    msg='Bộ môn này đã tồn tại',
                                    success=False,
                                    form=create_category_form)

        category = Category(**request.form)
        found_category.name = category.name
        db.session.commit()

        return render_template('home/category_form.html', segment='category_form',
                               msg='Cập nhập bộ môn thành công <a href="/category">Category List</a>',
                               success=True,
                               form=create_category_form)

    return render_template('home/category_form.html', segment='category_form',
                               success=False,
                               category=found_category,
                               form=create_category_form)



#-------------------------------------COURSE------------------------------------------

@blueprint.route('/course', methods=['GET', 'POST'])
def course():
    if 'delete' in request.form:
        Course.query.filter_by(id=int(request.form['delete'])).delete()
        courses = db.session.query(Course, Category).join(Course, Category.id == Course.category_id)
        db.session.commit()
        return redirect(url_for('home_blueprint.course'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.course_form_update', id=request.form['edit']))

    courses = db.session.query(Course, Category).join(Course, Category.id == Course.category_id)
    return render_template('home/course.html', segment='course', courses=courses)

@blueprint.route('/course_form', methods=['GET', 'POST'])
def course_form():
    create_course_form = CreateCourseForm(request.form)
    categories =  Category.query.all()
    create_course_form.category_id.choices = [(category.id, category.name) for category in categories]
    # create_course_form.category_name.data = [(category.id) for category in categories]
    if 'new_course' in request.form:

        course = Course(**request.form)
        db.session.add(course)
        db.session.commit()
        
        return render_template('home/course_form.html', segment='course_form',
                               msg='Thêm môn học thành công <a href="/course">Course List</a>',
                               success=True,
                               form=create_course_form)


    return render_template('home/course_form.html', segment='course_form',
                               success=False,
                               form=create_course_form)
                            
@blueprint.route('/course_form-update/<int:id>', methods=['GET', 'POST'])
def course_form_update(id):
    create_course_form = CreateCourseForm(request.form)
    categories =  Category.query.all()
    create_course_form.category_id.choices = [(category.id, category.name) for category in categories]

    found_course = Course.query.filter_by(id=id).first()
    create_course_form.category_id.default = found_course.category_id
    create_course_form.process()

    if 'update_course' in request.form:
                                   
        course = Course(**request.form)
        found_course.course_name = course.course_name
        found_course.category_id = course.category_id
        db.session.commit()

        return render_template('home/course_form.html', segment='course_form',
                               msg='Cập nhập môn học thành công <a href="/course">Course List</a>',
                               success=True,
                               form=create_course_form)

    return render_template('home/course_form.html', segment='course_form',
                               success=False,
                               course=found_course,
                               form=create_course_form)



#-------------------------------------CLASS------------------------------------------

@blueprint.route('/classes', methods=['GET', 'POST'])
def classes():
    if 'delete' in request.form:
        Class.query.filter_by(id=int(request.form['delete'])).delete()
        db.session.commit()
        return redirect(url_for('home_blueprint.classes'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.classes_form_update', id=request.form['edit']))

    classes = db.session.query(Class, Teacher, Course).join(Teacher, Teacher.id == Class.teacher_id).join(Course, Course.id == Class.course_id)
    return render_template('home/classes.html', segment='classes', classes=classes)

@blueprint.route('/classes_form', methods=['GET', 'POST'])
def classes_form():
    create_classes_form = CreateClassForm(request.form)
    teachers = Teacher.query.all()
    create_classes_form.teacher_id.choices = [(teacher.id, teacher.teacher_code + ' | ' + teacher.last_name + ' ' + teacher.first_name) for teacher in teachers]

    courses = Course.query.all()
    create_classes_form.course_id.choices = [(course.id, course.course_name) for course in courses]
    if 'new_class' in request.form:

        # read form data
        lesson = request.form['lesson']

        classes = Class.query.filter_by(lesson=lesson).first()
        if classes:
            return render_template('home/classes_form.html', segment='classes_form',
                                   msg='Lớp học này đã tồn tại',
                                   success=False,
                                   form=create_classes_form)

        classes = Class(**request.form)
        db.session.add(classes)
        db.session.commit()
        
        return render_template('home/classes_form.html', segment='classes_form',
                               msg='Thêm lớp học thành công <a href="/classes">Class List</a>',
                               success=True,
                               form=create_classes_form)


    return render_template('home/classes_form.html', segment='classes_form',
                               success=False,
                               form=create_classes_form)
                            
@blueprint.route('/classes_form-update/<int:id>', methods=['GET', 'POST'])
def classes_form_update(id):
    create_classes_form = CreateClassForm(request.form)

    # read teachers
    teachers =  Teacher.query.all()
    create_classes_form.teacher_id.choices = [(teacher.id, teacher.teacher_code + ' | ' + teacher.last_name + ' ' + teacher.first_name) for teacher in teachers]
    # read courses
    courses = Course.query.all()
    create_classes_form.course_id.choices = [(course.id, course.course_name) for course in courses]
    # set default teacher and course
    found_classes = Class.query.filter_by(id=id).first()
    create_classes_form.teacher_id.default = found_classes.teacher_id
    create_classes_form.course_id.default = found_classes.course_id
    create_classes_form.process()

    if 'update_class' in request.form:

        lesson = request.form['lesson']
        if lesson != found_classes.lesson:
            classes = Class.query.filter_by(lesson=lesson).first()
            if classes:
                return render_template('home/classes_form.html', segment='classes_form',
                                    msg='Lớp học này đã tồn tại',
                                    success=False,
                                    form=create_classes_form)
                                   
        classes = Class(**request.form)
        found_classes.lesson = classes.lesson
        found_classes.start_date = classes.start_date
        found_classes.end_date = classes.end_date
        found_classes.teacher_id = classes.teacher_id
        found_classes.course_id = classes.course_id
        db.session.commit()

        return render_template('home/classes_form.html', segment='classes_form',
                               msg='Cập nhập lớp học thành công <a href="/classes">Class List</a>',
                               success=True,
                               form=create_classes_form)

    return render_template('home/classes_form.html', segment='classes_form',
                               success=False,
                               classes=found_classes,
                               form=create_classes_form)


#-------------------------------------ClassStudent------------------------------------------

@blueprint.route('/class_student', methods=['GET', 'POST'])
def class_student():
    if 'delete' in request.form:
        Class.query.filter_by(id=int(request.form['delete'])).delete()
        class_students = db.session.query(ClassStudent, Class, Student).join(Class, Class.id == ClassStudent.class_id).join(Student, Student.id == ClassStudent.student_id)
        db.session.commit()
        return redirect(url_for('home_blueprint.class_student'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.class_student_form_update', id=request.form['edit']))

    class_students = db.session.query(ClassStudent, Class, Student).join(Class, Class.id == ClassStudent.class_id).join(Student, Student.id == ClassStudent.student_id)
    return render_template('home/class_student.html', segment='class_student', class_students=class_students)

@blueprint.route('/class_student_form', methods=['GET', 'POST'])
def class_student_form():
    create_class_student_form = CreateClassStudentForm(request.form)
    classes = Class.query.all()
    create_class_student_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]

    students = Student.query.all()
    create_class_student_form.student_id.choices = [(student.id, student.student_code + ' | ' + student.last_name + ' ' + student.first_name) for student in students]
    if 'new_class_student' in request.form:

        # read form data
        class_id = request.form['class_id']
        student_id = request.form['student_id']

        class_student = ClassStudent.query.filter_by(class_id=class_id, student_id=student_id).first()
        # class_student = ClassStudent.query.filter_by(class_id=class_id).filter_by(student_id=student_id).first()
        if class_student:
            return render_template('home/class_student_form.html', segment='class_student_form',
                                   msg='Sinh viên này đã tồn tại trong lớp học',
                                   success=False,
                                   form=create_class_student_form)

        class_student = ClassStudent(**request.form)
        db.session.add(class_student)
        db.session.commit()
        
        return render_template('home/class_student_form.html', segment='class_student_form',
                               msg='Thêm sinh viên vào lớp học thành công <a href="/class_student">Class list of students</a>',
                               success=True,
                               form=create_class_student_form)


    return render_template('home/class_student_form.html', segment='class_student_form',
                               success=False,
                               form=create_class_student_form)
                            
@blueprint.route('/class_student_form_update/<int:id>', methods=['GET', 'POST'])
def class_student_form_update(id):
    create_class_student_form = CreateClassStudentForm(request.form)

    # read class
    classes = Class.query.all()
    create_class_student_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]
    # read student
    students = Student.query.all()
    create_class_student_form.student_id.choices = [(student.id, student.student_code + ' | ' + student.last_name + ' ' + student.first_name) for student in students]
    # set default teacher and course
    found_class_student = ClassStudent.query.filter_by(id=id).first()
    create_class_student_form.class_id.default = found_class_student.class_id
    create_class_student_form.student_id.default = found_class_student.student_id
    create_class_student_form.process()

    if 'update_class_student' in request.form:
        
        class_id = request.form['class_id']
        student_id = request.form['student_id']
        if class_id!=found_class_student.class_id and student_id!=found_class_student.student_id:
            class_student = ClassStudent.query.filter_by(class_id=class_id, student_id=student_id).first()
            if class_student:
                return render_template('home/class_student_form.html', segment='class_student_form',
                                    msg='Sinh viên này đã tồn tại trong lớp học',
                                    success=False,
                                    class_student=found_class_student,
                                    form=create_class_student_form)
                                   
        class_student = ClassStudent(**request.form)
        found_class_student.class_id = class_student.class_id
        found_class_student.student_id = class_student.student_id
        db.session.commit()

        return render_template('home/class_student_form.html', segment='class_student_form',
                               msg='Cập nhập sinh viên trong lớp học thành công <a href="/class_student">Class list of students</a>',
                               success=True,
                               form=create_class_student_form)

    return render_template('home/class_student_form.html', segment='class_student_form',
                               success=False,
                               class_student=found_class_student,
                               form=create_class_student_form)


#-------------------------------------ClassWeekday------------------------------------------

@blueprint.route('/class_weekday', methods=['GET', 'POST'])
def class_weekday():
    if 'delete' in request.form:
        ClassWeekday.query.filter_by(id=int(request.form['delete'])).delete()
        db.session.commit()
        return redirect(url_for('home_blueprint.class_weekday'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.class_weekday_form_update', id=request.form['edit']))
    if 'attendance' in request.form:
        return redirect(url_for('home_blueprint.diemdanh', id=(request.form['attendance'])))
        # return render_template('home/diemdanh.html', segment='diemdanh', attendances=attendances)

    class_weekdays = db.session.query(ClassWeekday, Class, Weekday).join(Class, Class.id == ClassWeekday.class_id).join(Weekday, Weekday.id == ClassWeekday.weekday_id)
    return render_template('home/class_weekday.html', segment='class_weekday', class_weekdays=class_weekdays)

@blueprint.route('/class_weekday_form', methods=['GET', 'POST'])
def class_weekday_form():
    create_class_weekday_form = CreateClassWeekdayForm(request.form)
    classes = Class.query.all()
    create_class_weekday_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]

    weekdays = Weekday.query.all()
    create_class_weekday_form.weekday_id.choices = [(weekday.id, weekday.name) for weekday in weekdays]
    if 'new_class_weekday' in request.form:

        # read form data
        class_id = request.form['class_id']
        weekday_id = request.form['weekday_id']

        class_weekday = ClassWeekday.query.filter_by(class_id=class_id, weekday_id=weekday_id).first()
        if class_weekday:
            return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                                   msg='Buổi học của lớp học này đã tồn tại',
                                   success=False,
                                   form=create_class_weekday_form)

        class_weekday = ClassWeekday(**request.form)
        db.session.add(class_weekday)
        db.session.commit()
        
        return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                               msg='Thêm thành công <a href="/class_weekday">Class list of weekdays</a>',
                               success=True,
                               form=create_class_weekday_form)


    return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                               success=False,
                               form=create_class_weekday_form)
                            
@blueprint.route('/class_weekday_form_update/<int:id>', methods=['GET', 'POST'])
def class_weekday_form_update(id):
    create_class_weekday_form = CreateClassWeekdayForm(request.form)

    # read class
    classes = Class.query.all()
    create_class_weekday_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]
    # read weekday
    weekdays = Weekday.query.all()
    create_class_weekday_form.weekday_id.choices = [(weekday.id, weekday.name) for weekday in weekdays]
    # set default teacher and course
    found_class_weekday = ClassWeekday.query.filter_by(id=id).first()
    create_class_weekday_form.class_id.default = found_class_weekday.class_id
    create_class_weekday_form.weekday_id.default = found_class_weekday.weekday_id
    create_class_weekday_form.process()

    if 'update_class_weekday' in request.form:
        
        class_id = request.form['class_id']
        weekday_id = request.form['weekday_id']
        if class_id!=found_class_weekday.class_id and weekday_id!=found_class_weekday.weekday_id:
            class_weekday = ClassWeekday.query.filter_by(class_id=class_id, weekday_id=weekday_id).first()
            if class_weekday:
                return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                                    msg='Buổi học của lớp học này đã tồn tại',
                                    success=False,
                                    class_weekday=found_class_weekday,
                                    form=create_class_weekday_form)
                                   
        class_weekday = ClassWeekday(**request.form)
        found_class_weekday.class_id = class_weekday.class_id
        found_class_weekday.weekday_id = class_weekday.weekday_id
        db.session.commit()

        return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                               msg='Cập nhập thành công <a href="/class_weekday">Class list of weekdays</a>',
                               success=True,
                               form=create_class_weekday_form)

    return render_template('home/class_weekday_form.html', segment='class_weekday_form',
                               success=False,
                               class_weekday=found_class_weekday,
                               form=create_class_weekday_form)


#-------------------------------------ATTENDANCE------------------------------------------

@blueprint.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'delete' in request.form:
        Attendance.query.filter_by(id=int(request.form['delete'])).delete()
        db.session.commit()
        return redirect(url_for('home_blueprint.attendance'))
    if 'edit' in request.form:
        return redirect(url_for('home_blueprint.attendance_form_update', id=request.form['edit']))

    attendances = db.session.query(Attendance, Class, Weekday, Student).join(Class, Class.id == Attendance.class_id).join(Weekday, Weekday.id == Attendance.weekday_id).join(Student, Student.id == Attendance.student_id)
    return render_template('home/attendance.html', segment='attendance', attendances=attendances)

@blueprint.route('/attendance_form', methods=['GET', 'POST'])
def attendance_form():
    create_attendance_form = CreateAttendanceForm(request.form)

    classes = Class.query.all()
    create_attendance_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]

    students = Student.query.all()
    create_attendance_form.student_id.choices = [(student.id, student.student_code + ' | ' + student.last_name + ' ' + student.first_name) for student in students]

    weekdays = Weekday.query.all()
    create_attendance_form.weekday_id.choices = [(weekday.id, weekday.name) for weekday in weekdays]
    if 'new_attendance' in request.form:

        # read form data
        class_id = request.form['class_id']
        weekday_id = request.form['weekday_id']
        student_id = request.form['student_id']

        attendance = Attendance.query.filter_by(class_id=class_id, weekday_id=weekday_id, student_id=student_id).first()
        if attendance:
            return render_template('home/attendance_form.html', segment='attendance_form',
                                   msg='Sinh viên này đã tồn tại trong buổi học này',
                                   success=False,
                                   form=create_attendance_form)

        attendance = Attendance(**request.form)
        db.session.add(attendance)
        db.session.commit()
        
        return render_template('home/attendance_form.html', segment='attendance_form',
                               msg='Thêm sinh viên thành công <a href="/attendance">Attendance List</a>',
                               success=True,
                               form=create_attendance_form)


    return render_template('home/attendance_form.html', segment='attendance_form',
                               success=False,
                               form=create_attendance_form)
                            
@blueprint.route('/attendance_form-update/<int:id>', methods=['GET', 'POST'])
def attendance_form_update(id):
    create_attendance_form = CreateAttendanceForm(request.form)

    # read
    classes = Class.query.all()
    create_attendance_form.class_id.choices = [(clas.id, clas.lesson) for clas in classes]

    students = Student.query.all()
    create_attendance_form.student_id.choices = [(student.id, student.student_code + ' | ' + student.last_name + ' ' + student.first_name) for student in students]

    weekdays = Weekday.query.all()
    create_attendance_form.weekday_id.choices = [(weekday.id, weekday.name) for weekday in weekdays]
    # set default
    found_attendance = Attendance.query.filter_by(id=id).first()
    create_attendance_form.class_id.default = found_attendance.class_id
    create_attendance_form.weekday_id.default = found_attendance.weekday_id
    create_attendance_form.student_id.default = found_attendance.student_id
    create_attendance_form.process()

    if 'update_attendance' in request.form:

        class_id = request.form['class_id']
        weekday_id = request.form['weekday_id']
        student_id = request.form['student_id']
        if class_id!=found_attendance.class_id and weekday_id!=found_attendance.weekday_id and student_id!=found_attendance.student_id:
            attendance = Attendance.query.filter_by(class_id=class_id, weekday_id=weekday_id, student_id=student_id).first()
            if attendance:
                return render_template('home/attendance_form.html', segment='attendance_form',
                                    msg='Sinh viên này đã tồn tại trong buổi học này',
                                    success=False,
                                    form=create_attendance_form)
                                   
        attendance = Attendance(**request.form)
        found_attendance.class_id = attendance.class_id
        found_attendance.weekday_id = attendance.weekday_id
        found_attendance.student_id = attendance.student_id
        found_attendance.status = attendance.status
        db.session.commit()

        return render_template('home/attendance_form.html', segment='attendance_form',
                               msg='Cập nhập sinh viên thành công <a href="/attendance">Attendance List</a>',
                               success=True,
                               form=create_attendance_form)

    return render_template('home/attendance_form.html', segment='attendance_form',
                               success=False,
                               attendance=found_attendance,
                               form=create_attendance_form)



# @blueprint.route('/winemageda')
# def winemageda():
#     df = pd.read_csv("D:/Documents/LTPython/A35225/winemag-data-130k-v2.csv")
#     ndf = df.dropna()
#     top10 = ndf.sort_values(by='price', ascending=False).iloc[0:10]

#     county = df.groupby('country')['Unnamed: 0'].count()
#     #county = df.pivot_table(index='country', values=['Unnamed: 0'], aggfunc='count')
#     data = pd.DataFrame(county)
#     data.columns = ['count']
#     data = data.sort_values(by='count', ascending=False)

#     point = ndf.groupby('points')['Unnamed: 0'].count()
#     point = pd.DataFrame(point)
#     point.columns = ['count']

#     price = ndf.groupby('price')['Unnamed: 0'].count()
#     price = pd.DataFrame(price)
#     price.columns = ['count']
#     return render_template('home/winemageda.html', segment='winemageda', df=df.iterrows(), top10=top10.iterrows(), data=data.iterrows(), point=point.iterrows(), price=price.iterrows())

@blueprint.route('/user', methods=['GET', 'POST'])
def user():
    users = Users.query.all()
    return render_template('home/user.html', segment='user', users=users)

@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None