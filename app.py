from settings import database
from flask import Flask, render_template, request, flash, redirect, url_for
from models import Institution, get_all_institutions, Request, Event
from utils import database_add, delete_rows, get_rows, db
import schedulers
import os
from flask_apscheduler import APScheduler
import atexit
import sys


# create app
app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = database
db.init_app(app)

with app.app_context():
    db.create_all()

# scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@scheduler.task('cron', id='update_reports', minute=3)
def update_reports():
    with scheduler.app.app_context():
        schedulers.update_reports()


# Home page
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/admin/institutions')
def admin_institutions():
    # Get the list of institutions
    insts = get_all_institutions()

    return render_template('institutions.html', institutions=insts)


# Create a new institution
@app.route('/admin/institutions/add', methods=['GET', 'POST'])
def add_institution():
    if request.method == 'POST':
        if not request.form['code'] or not request.form['name'] or not request.form['key'] \
                or not request.form['exceptions'] or not request.form['events']:
            flash('Please enter all the fields', 'error')
        else:
            institution = Institution(request.form['code'], request.form['name'], request.form['key'],
                                      request.form['exceptions'], request.form['events'])
            db.session.add(institution)
            db.session.commit()
            flash('Record was successfully added', 'success')
            return redirect(url_for('institution_detail', code=institution.code))
    return render_template('create_inst.html')


# Detail page for a single institution
@app.route('/admin/institutions/<code>')
def institution_detail(code):
    # Get the institution object
    institution = Institution(code, None, None, None, None)
    institution = institution.get_institution()

    return render_template('institution.html', inst=institution)


# Edit page for a single institution
@app.route('/admin/institutions/<code>/edit', methods=['GET', 'POST'])
def institution_edit(code):
    # Get the institution object
    institution = Institution(code, None, None, None, None)
    institution = institution.get_institution()

    if request.method == 'POST':
        if not request.form['code'] or not request.form['name'] or not request.form['key'] \
                or not request.form['exceptions'] or not request.form['events']:
            flash('Please enter all the fields', 'error')
        else:
            institution.code = request.form['code']
            institution.name = request.form['name']
            institution.key = request.form['key']
            institution.exceptions = request.form['exceptions']
            institution.events = request.form['events']
            db.session.commit()
            flash('Record was successfully updated', 'success')
            return redirect(url_for('institution_detail', code=institution.code))
    return render_template('edit_inst.html', inst=institution)


if __name__ == '__main__':
    app.run()
