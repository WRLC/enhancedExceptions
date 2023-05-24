from settings import database, shared_secret
from flask import Flask, render_template, request, redirect, url_for, session
from models import (
    Institution, get_all_institutions, submit_inst_add_form, submit_inst_edit_form, get_institution_scalar,
    get_institution, User, user_login
)
from utils import db
from functools import wraps
import schedulers
import os
import jwt
from flask_apscheduler import APScheduler
import atexit

# create app
app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SESSION_KEY'] = os.urandom(24)
app.config['SHARED_SECRET'] = shared_secret
app.config['SQLALCHEMY_DATABASE_URI'] = database
app.secret_key = app.config['SESSION_KEY']
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

    return render_template('reports.html', institutions=insts)


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
        session['username'] = user_data['primary_id']
        session['user_home'] = user_data['inst']
        session['display_name'] = user_data['full_name']
        session['authorizations'] = user_data['authorizations']

        user_login(session)

        return redirect(url_for('index'))
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
    inst = get_institution_scalar(code)
    statuses = Institution.get_statuses(inst)
    requests = []
    for status in statuses:
        reqs = Institution.get_requests(inst, status[0])
        requests.append(reqs)
    return render_template('report.html', requests=requests, inst=inst, statuses=statuses)


# Admin page
@app.route('/admin')
@auth_required
def admin():
    if 'admin' not in session['authorizations']:
        return redirect(url_for('index'))
    return render_template('admin.html')


# Institutions admin page
@app.route('/admin/institutions')
@auth_required
def admin_institutions():
    if 'admin' not in session['authorizations']:
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

    # Get the institution object
    institution = get_institution(code)
    return render_template('institution.html', inst=institution)


# Edit page for a single institution
@app.route('/admin/institutions/<code>/edit', methods=['GET', 'POST'])
@auth_required
def institution_edit(code):
    if 'admin' not in session['authorizations']:
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

    # Get the list of users
    users = db.session.execute(db.select(User).order_by(User.last_login.desc())).scalars()
    return render_template('users.html', users=users)


if __name__ == '__main__':
    app.run()
