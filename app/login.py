from flask import Blueprint, redirect, render_template, url_for, request, flash,session
from .db import init_db
from werkzeug.security import check_password_hash
import re

bp = Blueprint("login", __name__)
users = init_db("users")

@bp.route('/login', methods = ['GET','POST'])
def login():
    css_file= url_for("static", filename='css/auth.css')

    if request.method == 'POST':
        email = request.form.get('email').strip()
        passw = request.form.get('password').strip()
        rem = request.form.get('rememberMe')
        user = users.find_one({'email': email})
    
        if  not email or not passw:
            flash("Please fill all fields.", 'danger')
            return redirect('/login')
        
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email format.", 'danger')
            return redirect('/register/step1')
        
        if user and check_password_hash(user['password_hash'], passw):
            session.clear()
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session.permanent = bool(rem)
            flash("Logged in Sucessfully.", 'sucess')
            return redirect('/')
        
        else:
            flash("Invalid email or password.", 'danger')
            return redirect('/login')

    return render_template('/auth/login.html', title='Login', login= '/register/step1', css_file=css_file)

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out Sucessfully!', "info")
    return redirect("/login")

