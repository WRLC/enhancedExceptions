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

# create app
app = Flask(__name__)

# set up logging to work with WSGI server
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

app.config['SCHEDULER_API_ENABLED'] = True
app.config['SESSION_KEY'] = os.urandom(24)
app.config['SHARED_SECRET'] = shared_secret
app.config['SQLALCHEMY_DATABASE_URI'] = database
app.secret_key = app.config['SESSION_KEY']
app.config['LOG_FILE'] = log_file
db.init_app(app)

# create database
with app.app_context():
    db.create_all()

# create scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


# Background task to update the reports
@scheduler.task('cron', id='update_reports', minute=1)
def update_reports():
    with scheduler.app.app_context():
        schedulers.update_reports()


# set up error handlers & templates for HTTP codes used in abort()
#   see http://flask.pocoo.org/docs/1.0/patterns/errorpages/
@app.errorhandler(400)
def badrequest(e):
    return render_template('error_400.html', e=e), 400


@app.errorhandler(403)
def forbidden(e):
    return render_template('unauthorized.html', e=e), 403


@app.errorhandler(500)
def internalerror(e):
    return render_template('error_500.html', e=e), 500


# audit log
audit_log = logging.getLogger('audit')
audit_log.setLevel(logging.INFO)
file_handler = TimedRotatingFileHandler(app.config['LOG_FILE'], when='midnight')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s\t%(message)s'))
audit_log.addHandler(file_handler)


# decorator for pages that need auth
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)

    return decorated


# Home page
@app.route('/')
@auth_required
def index():
    # Check if the user is an admin
    if 'admin' not in session['authorizations']:
        # If not, redirect to the reports page for their institution
        return redirect(url_for('report'), code=session['user_home'])

    # Get the list of institutions
    insts = get_all_institutions()
    updates = get_all_last_updates()

    return render_template('reports.html', institutions=insts, updates=updates)


@app.route('/login')
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    else:
        return render_template('login.html')


@app.route('/login/n', methods=['GET'])
def new_login():
    session.clear()
    if 'wrt' in request.cookies:
        encoded_token = request.cookies['wrt']
        user_data = jwt.decode(encoded_token, app.config['SHARED_SECRET'], algorithms=['HS256'])
        user_login(session, user_data)

        if 'exceptions' in session['authorizations']:
            return redirect(url_for('index'))
        else:
            abort(403)
    else:
        return "no login cookie"


@app.route('/logout')
@auth_required
def logout():
    session.clear()
    return redirect(url_for('index'))


# Report page
@app.route('/<code>')
@auth_required
def report(code):
    if session['user_home'] != code and 'admin' not in session['authorizations']:
        abort(403)
    inst = get_institution_scalar(code)
    statuses = Institution.get_statuses(inst)
    last_update = get_last_update(code)
    requests = []
    for status in statuses:
        reqs = Institution.get_requests(inst, status[0])
        requests.append(reqs)
    return render_template('report.html', requests=requests, inst=inst, statuses=statuses, update=last_update)


# Admin page
@app.route('/admin')
@auth_required
def admin():
    if 'admin' not in session['authorizations']:
        abort(403)
    return render_template('admin.html')


# Institutions admin page
@app.route('/admin/institutions')
@auth_required
def admin_institutions():
    if 'admin' not in session['authorizations']:
        abort(403)

    # Get the list of institutions
    insts = get_all_institutions()
    return render_template('institutions.html', institutions=insts)


# Create a new institution
@app.route('/admin/institutions/add', methods=['GET', 'POST'])
@auth_required
def add_institution():
    if 'admin' not in session['authorizations']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        submit_inst_add_form(request)
    return render_template('create_inst.html')


# Detail page for a single institution
@app.route('/admin/institutions/<code>')
@auth_required
def institution_detail(code):
    if 'admin' not in session['authorizations']:
        abort(403)

    # Get the institution object
    institution = get_institution(code)
    return render_template('institution.html', inst=institution)


# Edit page for a single institution
@app.route('/admin/institutions/<code>/edit', methods=['GET', 'POST'])
@auth_required
def institution_edit(code):
    if 'admin' not in session['authorizations']:
        abort(403)

    # Get the institution object
    institution = get_institution(code)

    if request.method == 'POST':
        submit_inst_edit_form(request, institution)
    return render_template('edit_inst.html', inst=institution)


# Admin page for users
@app.route('/admin/users')
@auth_required
def admin_users():
    if 'admin' not in session['authorizations']:
        abort(403)

    # Get the list of users
    users = db.session.execute(db.select(User).order_by(User.last_login.desc())).scalars()
    return render_template('users.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
