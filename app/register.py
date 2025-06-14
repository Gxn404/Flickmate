from flask import Blueprint, url_for, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash
from .db import init_db
from .utils import is_pass_strong
import logging
import time
import re

bp = Blueprint("register", __name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [ %(levelname)s]  %(message)s')
users = init_db("users")

@bp.route('/register/step1', methods=['GET', 'POST'])
def RPage1():
    css_file= url_for("static", filename='css/auth.css')
    if request.method == 'POST':
        fname = request.form.get('fname','').strip()
        lname = request.form.get('lname','').strip()
        email = request.form.get('email','').strip()

        if not fname or not email or not lname:
            flash("Please fill all fields.", 'danger')
            return redirect('/register/step1')
        
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email format.", 'danger')
            return redirect('/register/step1')
        
        if users.find_one({'email': email}):
            flash("Email already exists. Try logging in.", 'danger')
            return redirect('/register/step1')

        session['registration'] = {
            'fname': fname,
            'lname': lname,
            'email': email,
            'username': f'{fname}_{lname}'
        }
    
        return redirect('/register/step2')

  
    return render_template('/auth/register/register_step1.html', title='Register', css_file=css_file, rstep1= '/login', data = session.get('registration',{}))

@bp.route('/register/step2', methods = ['GET', 'POST'])
def RPage2():

    reg_data = session.get('registration')
    if not reg_data:
        flash("Please complete Step1 first.", "danger")
        return redirect('/register/step1')

    if request.method == 'POST':
        passw = request.form.get('password').strip()
        cpassw = request.form.get('confirm_password').strip()
        agree_terms = request.form.get('checkbox')

        if "back" in request.form:
            return redirect('/register/step1')

        if not passw or not cpassw or agree_terms == '':
            flash("Password and agreements are required.", "danger")

        if not is_pass_strong(passw):
            flash('Password must be strong with at least 8-15 characters long and include uppercase, lowercase, number, and special character.', 'danger')
            return redirect('/register/step2')
            
        pass_hash = generate_password_hash(passw)

        users.insert_one({
            **reg_data,
            "password_hash": pass_hash,
            "registered_on": time.asctime()
        })

        flash('Registration successful!', 'success')
        session.clear()
        logging.info(f'pash: {pass_hash}')
        return redirect('/login')

    css_file= url_for("static", filename='css/auth.css')
    return render_template('auth/register/register_step2.html', title='Register', css_file=css_file, rstep2= '/login')