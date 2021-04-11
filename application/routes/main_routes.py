from flask import render_template, flash, request, url_for, redirect, abort, session, Markup
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from application import app, bcrypt, mail, login_manager
from application.classes.user import User
from application.classes.session import Session
from application.forms.forms import RegistrationForm, LoginForm

from utils import getKeyPoints, CheckPosture

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
    if not current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template("start_session.html")

@app.route("/end-session/<string:session_id>")
def end_session(session_id):
    if not current_user.is_authenticated:
        return redirect(url_for('home'))
    # SHOW OVERALL GRAPHS
    # SAVE ALL DATA TO DATABASE

    return render_template("end_session.html", session_id=session_id)

@app.route("/session-summary/<string:session_id>")
def session_summary(session_id):
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    session = current_user.get_session_by_id(session_id)
    if session is None:
        return redirect(url_for('home'))

    data = session.to_dict()
    proximity_data, slump_data, forward_tilt_data, head_tilt_data, shoulder_tilt_data, shoulder_width_data = data['proximity'], data['slump'], data['forward_tilt'], data['head_tilt'], data['shoulder_tilt'], data['shoulder_width']

    return render_template("session_summary.html", proximity_data=proximity_data, slump_data=slump_data, forward_tilt_data=forward_tilt_data, head_tilt_data=head_tilt_data, shoulder_tilt_data=shoulder_tilt_data, shoulder_width_data=shoulder_width_data)

    


@app.route("/session", methods=["GET", "POST"])
def session_setup():
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    current_session = Session(id=str(ObjectId()), start_time=datetime.now())
    current_user.add_session(current_session)
    session_id = current_session.id
    data = current_session.to_dict()

    return redirect(url_for('session', session_id=session_id))

@app.route("/session/<string:session_id>", methods=["GET", "POST"])
def session(session_id):
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    current_session = current_user.get_session_by_id(session_id)

    if current_session is None:
        return redirect(url_for('home'))

    return render_template("session.html", session_id=session_id)
    

@login_required
@app.route("/account")
def account():
    user = current_user
    sessions = current_user.sessions
    info = [[session.id, session.start_time.strftime('%I:%M')] for session in sessions]
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

@app.route('/photo')
def photo():
    return render_template('photo.html')

@app.route('/update_graphs/<string:session_id>')
def update_graphs(session_id):
    if not current_user.is_authenticated:
        return {"Status": "Error"}

    session = current_user.get_session_by_id(session_id)
    print(session_id)
    data = session.to_dict()
    proximity_data, slump_data, forward_tilt_data, head_tilt_data, shoulder_tilt_data, shoulder_width_data = data['proximity'], data['slump'], data['forward_tilt'], data['head_tilt'], data['shoulder_tilt'], data['shoulder_width']

    print(len(proximity_data))

    return render_template("graphs.html", proximity_data=proximity_data, slump_data=slump_data, forward_tilt_data=forward_tilt_data, head_tilt_data=head_tilt_data, shoulder_tilt_data=shoulder_tilt_data, shoulder_width_data=shoulder_width_data)

@app.route('/features')
def features():
    return render_template("features.html")

@app.route('/photo_analysis/<string:session_id>', methods=["GET", "POST"])
def photo_cap(session_id):
    if not current_user.is_authenticated:
        return {"Status": "Error"}

    session = current_user.get_session_by_id(session_id)
    data = session.to_dict()
    print("NEW FRAME:")
    for k, v in data.items():
        print(f"{k}: {v}")
    print("\n\n")

    json = request.get_json()
    photo_base64 = json["image"]

    header, encoded = photo_base64.split(",", 1)
    binary_data = base64.b64decode(encoded)
    nparr = np.fromstring(binary_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    sensitivity_dict = {
        'Proximity' : [101, 1.01],
        'Slump' : [100],
        'Forward Tilt' : [30],
        'Head Tilt' : [30],
        'Shoulder Tilt' : [30],
        'Shoulder Width' : [100]
    }

    if len(data['base_key_points']) == 0:
        current_user.update_session(session_id, **{"base_key_points": getKeyPoints(img)})
        # print("BASE KEY POINTS SET")
    proximity_data, slump_data, forward_tilt_data, head_tilt_data, shoulder_tilt_data, shoulder_width_data = data['proximity'], data['slump'], data['forward_tilt'], data['head_tilt'], data['shoulder_tilt'], data['shoulder_width']
    flags = data['flags']

    key_points = getKeyPoints(img)
    posture_checker = CheckPosture(1, key_points, data['base_key_points'], sensitivity_dict)

    proximity_flag, proximity_val = posture_checker.check_proximity()
    slump_flag, slump_val = posture_checker.check_slump()
    forward_tilt_flag, forward_tilt_val = posture_checker.check_forward_tilt()
    head_tilt_flag, head_tilt_val = posture_checker.check_head_tilt()
    shoulder_tilt_flag, shoulder_tilt_val = posture_checker.check_shoulder_tilt()
    shoulder_width_flag, shoulder_width_val = posture_checker.check_shoulder_width()

    proximity_data.append(proximity_val); slump_data.append(slump_val); forward_tilt_data.append(forward_tilt_val), head_tilt_data.append(head_tilt_val), shoulder_tilt_data.append(shoulder_tilt_val), shoulder_width_data.append(shoulder_tilt_val)
    flags.append([proximity_flag, slump_flag, forward_tilt_flag, head_tilt_flag, shoulder_tilt_flag, shoulder_width_flag])

    current_user.update_session(session_id, **{"proximity": proximity_data, "slump": slump_data, "forward_tilt": forward_tilt_data, "head_tilt": head_tilt_data, "shoulder_tilt": shoulder_tilt_data, "shoulder_width": shoulder_width_data, "flags": flags})

        # print("NEW FRAME")
        # print("Proximity:", proximity_flag, proximity_val)
        # print("Slump:", slump_flag, slump_val)
        # print("Forward Tilt:", forward_tilt_flag, forward_tilt_val)
        # print("Head Tilt:", head_tilt_flag, head_tilt_val)
        # print("Shoulder Tilt:", shoulder_tilt_flag, shoulder_tilt_val)
        # print("Shoulder Width:", shoulder_width_flag, shoulder_width_val)
        # print(key_points)
        # print("\n\n")

    response = {"Status": "Success"}, 200

    return response