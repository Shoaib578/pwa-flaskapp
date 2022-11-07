# Todo: HASH PASSWORD
# Todo: PASSWORD THE DATABASE

import mimetypes
import os.path
import re
from ssl import ALERT_DESCRIPTION_DECOMPRESSION_FAILURE
import uuid
import random
import math
from geopy.geocoders import Nominatim
from flask import Flask, current_app, render_template, request, redirect, url_for, session, make_response, send_from_directory
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
# from flask_ngrok import run_with_ngrok
import ntplib
from time import ctime
import pandas as pd

# For PWA deployment ngrok is to be removed.

# template_dir = os.path.abspath('D:/InternWork/PythonDocker - Flask/template')
app = Flask(__name__, template_folder='templates')
# run_with_ngrok(app)
app.secret_key = 'asdasda090293Asd'

app.config['MYSQL_HOST'] = 'ec2-18-215-41-121.compute-1.amazonaws.com'
app.config['MYSQL_USER'] = 'sosxudybookojq'
app.config['MYSQL_PORT'] = 5432

app.config['MYSQL_PASSWORD'] = 'ae3d993776aedd031acb6f36f226898f9bac0c227350188a48bf88ac68bf9fd8'
app.config['MYSQL_DB'] = 'db06o0vvfcjdng'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'timeclockaktus@gmail.com'
app.config['MAIL_PASSWORD'] = 'ziejscjumlsducgf'
# email password: adminPassword123
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mysql = MySQL(app)
mail = Mail(app)
geocoder = Nominatim(user_agent='TimeClock')


create = mysql.connection.cursor()
create.execute("CREATE DATABASE IF NOT EXISTS `db06o0vvfcjdng` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;")
create.close()

# Run in MySQL Workbench
# USE `TimeClock`;
# CREATE TABLE IF NOT EXISTS `users` (
# `id` int(11) NOT NULL AUTO_INCREMENT,
# `username` varchar(100) NOT NULL,
# `email` varchar(100) NOT NULL,
# `password` varchar(255) NOT NULL,
# `macaddress` varchar(255) NOT NULL,
# `admin` int(1) NOT NULL,
# `superadmin` int(1) NOT NULL,
# `recovery` varchar(6) NULL,
# PRIMARY KEY (`id`)
# ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
# INSERT INTO `users` (`id`, `username`, `email`, `password`, `admin`, `superadmin`, `recovery`) VALUES (1, 'test', 'test@test.com', 'test', '0', '0', NULL);

# Clock in/out database set up
# Set @currenttime = current_timestamp();
#
# USE `TimeClock`;
# CREATE TABLE IF NOT EXISTS `clock` (
# `id` int(11) NOT NULL AUTO_INCREMENT,
# `username` varchar(100) NOT NULL,
# `direction` varchar(4) NOT NULL,
# `location` varchar(100) NOT NULL,
# `time` varchar(255) NOT NULL,
# `servertime` varchar(255) NOT NULL,
# PRIMARY KEY (`id`)
# ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
# INSERT INTO `clock` (`id`, `username`, `direction`, `location`, `time`,`servertime`) VALUES (1, 'junleng', 'in', 'test', 'test', "@currenttime");


# Retrieves current time from a network time protocol
def ntp_time():
    ntp_client = ntplib.NTPClient()
    response = ntp_client.request('pool.ntp.org')
    return ctime(response.tx_time)


# Register Service Worker
@app.route('/sw.js', methods = ['GET'])
def sw():
    return current_app.send_static_file('sw.js') # -> returns error mime type ('plain')

# Code below does not retrieve sw.js (returns error)
# j = 'javascript'
# response=make_response(
#                  send_from_directory(current_app.send_static_file('sw.js'), mimetypes=j))
# #change the content header file. Can also omit; flask will handle correctly.
# response.headers['Content-Type'] = 'application/javascript'
# return response


# User Account Functions (Log In/ Log Out)

# Log user into application (Main Page, therefore '/')
@app.route('/', methods=['GET', 'POST'])
def log_in():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        macaddress = hex(uuid.getnode())
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = % s AND password = % s', (username, password,))
        account = cursor.fetchone()
        if account:
            if macaddress == account[4]:
                session['username'] = request.form['username']
                return redirect(url_for('home'))
            else:
                msg = 'Device does not match original sign up device!'
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


# Log user out of application
@app.route('/logout', methods=['GET', 'POST'])
def log_out():
    session.clear()
    return redirect(url_for('log_in'))


# User sign up to create an account
@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'email' in request.form and 'password' in request.form:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirmpassword = request.form['confirmPassword']
        macaddress = hex(uuid.getnode())
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT * FROM users WHERE username = % s''', (username,))
        usernamedup = cursor.fetchone()
        cursor.execute('''SELECT * FROM users WHERE email = % s''', (email,))
        account = cursor.fetchone()
        if usernamedup:
            msg = "Username is already in use !"
        elif account:
            msg = 'Email has already been registered with an account !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not password or not email:
            msg = 'Please fill out the form !'
        elif password != confirmpassword:
            msg = 'Passwords do not match!'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s, % s, 0, 0, NULL)',
                           (username, email, password, macaddress,))
            mysql.connection.commit()
            msg = 'You have successfully registered !'

    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('signup.html', msg=msg)


# Gets an email from the user and sends a forget password email to them
@app.route('/forget', methods=['POST', 'GET'])
def forget():
    msg = ''
    if request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT * FROM users WHERE email = % s''', (email,))
        account = cursor.fetchone()
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not account:
            msg = 'Account does not exist!'
        else:
            # generates random 6 digit code --> send to email (will do tmr)
            digits = [i for i in range(0, 10)]
            random_str = ""
            for i in range(6):
                index = math.floor(random.random() * 10)
                random_str += str(digits[index])
            cursor.execute('''UPDATE users SET recovery = % s WHERE email = % s''', (random_str, email))
            mysql.connection.commit()
            email = Message('Reset Password', sender='timeclockaktus@gmail.com', recipients=[email])
            email.html = "Dear,<br>" \
                         "Your recovery code to recover your password is " + random_str + ". You can recover your password here: http://127.0.0.1:5000/changepassword . <br>" \
                                                                                          "Yours sincerely, <br>" \
                                                                                          "TimeClock"
            mail.send(email)
            msg = "Email has been sent!"
            return redirect(url_for('change_password'))
    return render_template('forget.html', msg=msg)


# Displays page for user to change password (Recovery Code Portion)
@app.route('/changepassword', methods=['POST', 'GET'])
def change_password():
    msg = ''
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        username = request.form['username']
        password = request.form['password']
        confirmPassword = request.form['confirmPassword']
        OTP = request.form['otpcode']
        account = cursor.execute('''SELECT * FROM users WHERE username = % s AND recovery = % s''', (username, OTP,))
        if account == 1:
            if password == confirmPassword:
                cursor.execute('''UPDATE users SET password = % s WHERE username = %s''', (password, username))
                mysql.connection.commit()
                msg = 'Password has been changed!'
            elif password != confirmPassword:
                msg = 'Password does not match!'
        else:
            msg = 'Username/ OTP is incorrect!'
    return render_template('changepassword.html', msg=msg)



# Main user functions (Clock In/ Out)

@app.route('/home', methods=['POST', 'GET'])
# Displays home page (individual user clock in and all clock ins for admins)
def home():
    if request.method == 'POST':
        direction = request.form["direction"]
        location = request.form['address']
        time = request.form['timeclocked']
        if location != "" and time != "":
            username = session.get("username")
            servertime = str(ntp_time())
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO clock VALUES (NULL, % s, % s, % s, % s, % s)',
                            (username, direction, location, time, servertime))
            mysql.connection.commit()
            cursor.execute('INSERT INTO userview VALUES (NULL, % s, % s, % s, % s, % s)',
                            (username, direction, location, time, servertime))
            mysql.connection.commit()
        else:
            pass
    username = session.get("username")
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT * FROM userview WHERE username = % s ORDER BY id DESC''', (username,))
    data = cursor.fetchall()
    # Data is clock in and clock out data and sAdmin checks if the user is a super admin and admin checks if the user is an admin
    return render_template('home.html', data=data, len=len(data))


# Delete user info from main admin page
@app.route('/delusertime/<int:id>', methods=['POST', 'GET'])
def delusertime(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM userview WHERE id = % s', (id,))
    cursor.fetchone()
    mysql.connection.commit()
    return redirect(url_for('home'))


@app.route('/about')
# Displays about page (Not completed)
def about_page():
    username = session.get("username")
    cursor = mysql.connection.cursor()
    # superadmin = cursor.execute('''SELECT * FROM users WHERE (username = % s AND superadmin = 1)''', (username,))
    return render_template('about.html')


if __name__ == '__main__':
    app.run()
