from settings import database, shared_secret, log_file
from flask import Flask, render_template, request, redirect, url_for, session, abort
from models import (
    Institution, get_all_institutions, submit_inst_add_form, submit_inst_edit_form, get_institution_scalar,
    get_institution, User, user_login, get_last_update, get_all_last_updates
)
from utils import db
from functools import wraps
import schedulers
import os
import jwt
from flask_apscheduler import APScheduler
import atexit
import logging
from logging.handlers import TimedRotatingFileHandler
import flask_excel as excel

# create app
app = Flask(__name__)

# set up logging to work with WSGI server
if __name__ != '__main__':  # if running under WSGI
    gunicorn_logger = logging.getLogger('gunicorn.error')  # get the gunicorn logger
    app.logger.handlers = gunicorn_logger.handlers  # set the app logger handlers to the gunicorn logger handlers
    app.logger.setLevel(gunicorn_logger.level)  # set the app logger level to the gunicorn logger level

app.config['SCHEDULER_API_ENABLED'] = True  # enable APScheduler
app.config['SESSION_KEY'] = os.urandom(24)  # generate a random session key
app.config['SHARED_SECRET'] = shared_secret  # set the shared secret for JWT
app.config['SQLALCHEMY_DATABASE_URI'] = database  # set the database URI
app.secret_key = app.config['SESSION_KEY']  # set the session key
app.config['LOG_FILE'] = log_file  # set the audit log file

db.init_app(app)  # initialize SQLAlchemy
excel.init_excel(app)  # initialize Flask-Excel

# database
with app.app_context():  # need to be in app context to create the database
    db.create_all()  # create the database

# scheduler
scheduler = APScheduler()  # create the scheduler
scheduler.init_app(app)  # initialize the scheduler
scheduler.start()  # start the scheduler
atexit.register(lambda: scheduler.shutdown())  # Shut down the scheduler when exiting the app


# Background task to update the reports
@scheduler.task('cron', id='update_reports', minute=55)  # run at 55 minutes past the hour
def update_reports():
    with scheduler.app.app_context():  # need to be in app context to access the database
        schedulers.update_reports()  # update the reports


# set up error handlers & templates for HTTP codes used in abort()
#   see http://flask.pocoo.org/docs/1.0/patterns/errorpages/
# 400 error handler
@app.errorhandler(400)
def badrequest(e):
    return render_template('error_400.html', e=e), 400  # render the error template


# 403 error handler
@app.errorhandler(403)
def forbidden(e):
    return render_template('unauthorized.html', e=e), 403  # render the error template


# 500 error handler
@app.errorhandler(500)
def internalerror(e):
    return render_template('error_500.html', e=e), 500  # render the error template


# audit log
audit_log = logging.getLogger('audit')  # create the audit log
audit_log.setLevel(logging.INFO)  # set the audit log level
file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'], when='midnight')  # create a file handler
file_handler.setLevel(logging.INFO)  # set the file handler level
file_handler.setFormatter(logging.Formatter('%(asctime)s\t%(message)s'))  # set the file handler format
audit_log.addHandler(file_handler)  # add the file handler to the audit log


# decorator for pages that need auth
def auth_required(f):
    @wraps(f)  # preserve the original function's metadata
    def decorated(*args, **kwargs):  # the wrapper function
        if 'username' not in session:  # if the user is not logged in
            return redirect(url_for('login'))  # redirect to the login page
        else:
            return f(*args, **kwargs)  # otherwise, call the original function

    return decorated


# Home page
@app.route('/')
@auth_required
def index():
    # Check if the user is an admin
    if 'admin' not in session['authorizations']:
        # If not, redirect to the reports page for their institution
        return redirect(url_for('report', code=session['user_home']))

    insts = get_all_institutions()  # get all institutions
    updates = get_all_last_updates()  # get all last updates

    return render_template('reports.html', institutions=insts, updates=updates)


# Login page
@app.route('/login')
def login():
    if 'username' in session:  # if the user is already logged in
        return redirect(url_for('index'))  # redirect to the home page
    else:
        return render_template('login.html')  # otherwise, render the login page


# Login handler
@app.route('/login/n', methods=['GET'])
def new_login():
    session.clear()  # clear the session
    if 'wrt' in request.cookies:  # if the login cookie is present
        encoded_token = request.cookies['wrt']  # get the login cookie
        user_data = jwt.decode(encoded_token, app.config['SHARED_SECRET'], algorithms=['HS256'])  # decode the token
        user_login(session, user_data)  # log the user in

        if 'exceptions' in session['authorizations']:  # if the user is an exceptions user
            return redirect(url_for('index'))  # redirect to the home page
        else:
            abort(403)  # otherwise, abort with a 403 error
    else:
        return "no login cookie"  # if the login cookie is not present, return an error


# Logout handler
@app.route('/logout')
@auth_required
def logout():
    session.clear()  # clear the session
    return redirect(url_for('index'))  # redirect to the home page


# Report page
@app.route('/<code>')
@auth_required
def report(code):
    if session['user_home'] != code and 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin and not at their home institution, abort with a 403 error

    inst = get_institution_scalar(code)  # get the institution
    statuses = Institution.get_statuses(inst)  # get the statuses
    last_update = get_last_update(code)  # get the last update
    requests = []  # initialize the requests list
    for status in statuses:  # for each status
        reqs = Institution.get_requests(inst, status[0])  # get the requests for that status
        requests.append(reqs)  # add the requests to the list

    return render_template('report.html', requests=requests, inst=inst, statuses=statuses, update=last_update)


# Report download
@app.route('/<code>/download')
@auth_required
def report_download(code):
    if session['user_home'] != code and 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin and not at their home institution, abort with a 403 error

    inst = get_institution_scalar(code)  # get the institution
    reqs = Institution.get_all_requests(inst)  # get all requests for the institution

    # Set up the columns for the Excel file
    columns = ['Borrowing Request Status', 'Internal ID', 'Borrowing Request Date', 'Title', 'Author', 'Network Number',
               'Requestor', 'Partner Active Status', 'Request Sending Date', 'Days Since Request', 'Partner Name',
               'Partner Code', 'In Transit Start']

    return excel.make_response_from_query_sets(reqs, columns, 'xlsx', file_name=code)  # return the Excel file


# Admin page
@app.route('/admin')
@auth_required
def admin():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error
    return render_template('admin.html')  # otherwise, render the admin page


# Institutions admin page
@app.route('/admin/institutions')
@auth_required
def admin_institutions():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    insts = get_all_institutions()  # get all institutions
    return render_template('institutions.html', institutions=insts)  # render the institutions admin page


# Create a new institution
@app.route('/admin/institutions/add', methods=['GET', 'POST'])
@auth_required
def add_institution():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error
    if request.method == 'POST':  # if the form has been submitted
        submit_inst_add_form(request)  # submit the form

    return render_template('create_inst.html')  # render the create institution page


# Detail page for a single institution
@app.route('/admin/institutions/<code>')
@auth_required
def institution_detail(code):
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    institution = get_institution(code)  # get the institution object
    return render_template('institution.html', inst=institution)  # render the institution detail page


# Edit page for a single institution
@app.route('/admin/institutions/<code>/edit', methods=['GET', 'POST'])
@auth_required
def institution_edit(code):
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    institution = get_institution(code)  # get the institution object

    if request.method == 'POST':  # if the form has been submitted
        submit_inst_edit_form(request, institution)  # submit the form

    return render_template('edit_inst.html', inst=institution)  # render the institution edit page


# Admin page for users
@app.route('/admin/users')
@auth_required
def admin_users():
    if 'admin' not in session['authorizations']:
        abort(403)  # if the user is not an admin, abort with a 403 error

    users = db.session.execute(db.select(User).order_by(User.last_login.desc())).scalars()  # get all users
    return render_template('users.html', users=users)  # render the users admin page


if __name__ == '__main__':
    app.run(debug=True)
