# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for
import pandas as pd
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass


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

@blueprint.route('/profile')
def profile():
    user = Users(**request.form)
    return render_template('accounts/profile.html',
                                   msg='User Profile',
                                   user=current_user)
# @blueprint.route('/student')
# def student():
#     df = pd.read_csv('D:/Documents/LTPython/week1/advanced_python.csv', sep = ';')
#     return render_template('homew/student.html',
#                                    msg='Student List',
#                                    rows=df.iterrows())
                        
# @blueprint.route('/winemageda')
# def winemageda():
#     df = pd.read_csv("D:/Documents/LTPython/week4/winemag-data-130k-v2.csv")
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
#     return render_template('homew/winemageda.html', top10=top10.iterrows(), data=data.iterrows(), point=point.iterrows(), price=price.iterrows())


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
