from settings import database
from flask import Flask, render_template, request
from models import (
    Institution, get_all_institutions, submit_inst_add_form, submit_inst_edit_form, get_institution_scalar,
    get_institution
)
from utils import db
import schedulers
import os
from flask_apscheduler import APScheduler
import atexit


# create app
app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = database
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
@scheduler.task('cron', id='update_reports', minute=42)
def update_reports():
    with scheduler.app.app_context():
        schedulers.update_reports()


# Home page
@app.route('/')
def index():
    return render_template('index.html')


# List of reports page
@app.route('/reports')
def reports():
    # Get the list of institutions
    insts = get_all_institutions()

    return render_template('reports.html', institutions=insts)


# Report page
@app.route('/reports/<code>')
def report(code):
    inst = get_institution_scalar(code)
    requests = Institution.get_requests(inst)
    return render_template('report.html', requests=requests, inst=inst)


# Admin page
@app.route('/admin')
def admin():
    return render_template('admin.html')


# Institutions admin page
@app.route('/admin/institutions')
def admin_institutions():
    # Get the list of institutions
    insts = get_all_institutions()
    return render_template('institutions.html', institutions=insts)


# Create a new institution
@app.route('/admin/institutions/add', methods=['GET', 'POST'])
def add_institution():
    if request.method == 'POST':
        submit_inst_add_form(request)
    return render_template('create_inst.html')


# Detail page for a single institution
@app.route('/admin/institutions/<code>')
def institution_detail(code):
    # Get the institution object
    institution = get_institution(code)
    return render_template('institution.html', inst=institution)


# Edit page for a single institution
@app.route('/admin/institutions/<code>/edit', methods=['GET', 'POST'])
def institution_edit(code):
    # Get the institution object
    institution = get_institution(code)

    if request.method == 'POST':
        submit_inst_edit_form(request, institution)
    return render_template('edit_inst.html', inst=institution)


if __name__ == '__main__':
    app.run()
