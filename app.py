from settings import database
from flask import Flask, render_template, request, flash, redirect, url_for
from models import db, Institution, get_all_institutions
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = database
db.init_app(app)

with app.app_context():
    db.create_all()


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
