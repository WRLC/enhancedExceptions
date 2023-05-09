from settings import database
from flask import Flask, render_template
from models import db, Institution, get_all_institutions

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = database
db.init_app(app)

with app.app_context():
    db.create_all()


# Home page
@app.route('/')
def index():
    return render_template('index.html')


# List of all institutions
@app.route('/institutions')
def institutions():
    # Get the list of institutions
    insts = get_all_institutions()

    return render_template('institutions.html', institutions=insts)


# Detail page for a single institution
@app.route('/institutions/<code>')
def institution_detail(code):
    # Get the institution object
    institution = Institution(code, None, None, None, None)
    institution = institution.get_institution()

    return render_template('institution.html', inst=institution)


# Report page for a single institution
@app.route('/institutions/<code>/report')
def institution_report(code):
    inst = code
    report = []
    return render_template('report.html', report=report, inst=inst)


if __name__ == '__main__':
    app.run()
