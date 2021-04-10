from flask import render_template, flash, request, url_for, redirect, abort, session, Markup
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from application import app, bcrypt, mail, login_manager
from application.classes.user import User
from application.classes.session import Session
from application.forms.forms import RegistrationForm, LoginForm

from datetime import datetime
import os 
import json 
import re
import time
import numpy as np
from bson import ObjectId
import base64
import cv2
import jsonify

@login_manager.user_loader
def load_user(user_id):
    user_id = str(user_id)
    return User.get_by_id(user_id)

@app.route("/home", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def home():
    print(current_user.is_authenticated)
    return render_template("home.html")

@app.route("/start-session")
def start_session():
    return render_template("start_session.html")

@app.route("/end-session/<string:session_id>")
def end_session(session_id):
    # current_session = current_user.get_session_by_id(session_id)
    # current_user.update_session(session_id, end_time=datetime.now, total_time=datetime.now() - current_session.start_time)

    return render_template("end_session.html")

@app.route("/session", methods=["GET", "POST"])
def session():
    session_id = "helllo"
    return render_template("session.html", session_id=session_id)
    

@login_required
@app.route("/account")
def account():
    user = current_user
    sessions = current_user.sessions
    info = [[session.start_time.strftime('%I:%M')] for session in sessions]
    return render_template("account.html", user=user, sessions=sessions, info=info)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    
    print(form.email.data, form.password.data, form.confirm_password.data, form.validate_on_submit())

    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(id=str(ObjectId()), email=form.email.data, password=hashed_pw, _is_active=True, sessions=[])
        user.add()
        flash('Your account has been created', 'success')
        return redirect('login')

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        print(user)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash("Login Unsuccessful. Please check email and password", 'danger')
    
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


import base64

@app.route('/photo')
def photo():
    return render_template('photo.html')


@app.route('/_photo_cap')
def photo_cap():
    photo_base64 = request.args.get('photo_cap')
    header, encoded = photo_base64.split(",", 1)
    binary_data = base64.b64decode(encoded)
    image_name = "capture"

    i = 1
    save_name = image_name + str(i) + ".jpeg"
    while os.path.exists(os.path.join("application", "static", "images", "captures", save_name)):
        i += 1
        save_name = image_name + str(i) + ".jpeg"

    with open(os.path.join("application", "static", "images", "captures", save_name), "wb") as f:
        f.write(binary_data)

    if current_user.is_authenticated:
        pass
        # CALL PROCESSING METHOD HERE

    response = {"Status": "Success"}

    return response