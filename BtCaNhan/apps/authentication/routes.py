# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for, Flask, Response
from flask_login import (
    current_user,
    login_user,
    logout_user,
)
from numpy import empty

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass

import pandas as pd
import cv2

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        photo = request.form['photo']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template('accounts/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))

# Home Work

@blueprint.route("/userprofile")
def userprofile():
    return render_template("home/userProfile.html", user=current_user)


dfDsLop = pd.read_csv(r"apps\authentication\advanced_python.csv", sep=';')


@blueprint.route("/listusers")
def listUsers():
    return render_template("home/listUsers.html", users=dfDsLop.iterrows(), length=len(dfDsLop.index), segment="listusers")


@blueprint.route("/queryusers")
def queryUsers():
    return render_template("home/queryUsers.html", segment="queryusers")


@blueprint.route("/resultqueryusers", methods=['POST', 'GET'])
def resultqueryusers():
    studentCode = dfDsLop[dfDsLop['student code'].str.upper(
    ).str.contains(request.form.get("Search").upper())]
    studentClass = dfDsLop[dfDsLop['CN'].str.upper().str.contains(
        request.form.get("Search").upper())]

    result = studentCode if(studentClass.empty) else studentClass
    return render_template("home/listUsers.html", users=result.iterrows(), length=len(result.index), segment="queryusers")


dfWinemag = pd.read_csv(
    r"apps\authentication\winemagLite-data-130k-v2.csv", index_col=0)


@blueprint.route("/showwinemags")
def show():
    return render_template("home/listWinemags.html", winemags=dfWinemag.iterrows(), length=len(dfWinemag.index),  segment='showwinemags')


# @blueprint.route("/resultquerywinemags", methods=['POST', 'GET'])
# def resultQueryWinemags():
#     country = dfWinemag[dfWinemag['country'].str.upper(
#     ).str.contains(request.form.get("Search").upper())]

#     result = country

#     return render_template("home/listWinemags.html", winemags=result.iterrows(), length=len(result.index), segment='showwinemags')


@blueprint.route("/chartwinemags")
def bar():
    dfWinemag.dropna(subset=["price"], inplace=True)

    labels = dfWinemag['winery']
    values = dfWinemag['price']
    colors = [
        "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
        "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
        "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]
    
    return render_template('home/chartWinemags.html', columnsDateframe=dfWinemag.columns.values, title='Biểu đồ giữa winery và price', max=100, labels=labels, values=values, colors=colors, set=zip(values, labels, colors), segment="chartwinemags")


@blueprint.route("/selectchart", methods=['GET', 'POST'])
def selectBar():
    selectx = request.form.get('x')
    selecty = request.form.get('y')

    dfWinemag.dropna(subset=[selectx], inplace=True)
    dfWinemag.dropna(subset=[selecty], inplace=True)

    labels = dfWinemag[selectx]
    values = dfWinemag[selecty]
    colors = [
        "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
        "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
        "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]

    return render_template('home/chartWinemags.html', columnsDateframe=dfWinemag.columns.values, title="Biểu đồ giữa " + selectx+" và "+selecty, max=100, labels=labels, values=values, colors=colors, set=zip(values, labels, colors), segment="chartwinemags")

# Project 2

@blueprint.route('/camera')
def camera():
    return render_template('home/camera.html', segment='camera')

@blueprint.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:

        ## read the camera frame
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
# C:\Users\admin\Videos\Captures
