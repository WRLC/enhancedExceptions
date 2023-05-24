import sqlalchemy as sa
from flask import flash, redirect, url_for
from utils import db, exceptions_map
from datetime import datetime
from settings import admins


####################
#  Object Classes  #
####################

# Institution object
class Institution(db.Model):
    code = sa.Column(sa.String(255), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    key = sa.Column(sa.String(255), nullable=True)
    exceptions = sa.Column(sa.String(255), nullable=True)
    items = sa.Column(sa.String(255), nullable=True)
    events = sa.Column(sa.String(255), nullable=True)

    def __init__(self, code, name, key, exceptions, items, events):
        self.code = code
        self.name = name
        self.key = key
        self.exceptions = exceptions
        self.items = items
        self.events = events

    # Get a single institution's requests from the database
    def get_requests(self, status):
        requests = db.session.execute(db.select(
            Request.borreqstat, Request.internalid, Request.borcreate, Request.title, Request.author,
            Request.networknum, Request.partnerstat, Request.reqsend, Request.days, Request.requestor,
            Request.partnername, Request.partnercode, Event.eventstart
        ).join(Item, Item.fulfillmentreqid == Request.fulfillmentreqid, isouter=True).join(
            Event, Event.itemid == Item.itemid, isouter=True
        ).filter(
            Request.instcode == self.code,
            Request.borreqstat == status
        ).order_by(
            Request.borreqstat, Request.internalid.desc(), Request.borcreate.desc(), Request.reqsend.desc()
        )).all()
        return requests

    # Get a single institution's borrowing request statuses from the database
    def get_statuses(self):
        statuses = db.session.execute(db.select(
            Request.borreqstat, sa.func.count(Request.borreqstat)
        ).filter(
            Request.instcode == self.code
        ).group_by(
            Request.borreqstat
        )).all()
        return statuses

    # Construct a request object from a single row in the exceptions report
    def construct_request(self, exrow):
        exinstance = Request(None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                             self.code)

        for key, value in exceptions_map.items():
            try:
                setattr(exinstance, key, exrow.find(value).get_text())
            except AttributeError:
                pass

        return exinstance

    # Construct an item object from a single row in the items report
    def construct_item(self, itrow):
        itemid = itrow.Column1.get_text()  # Item ID
        fulfillmentreqid = itrow.Column2.get_text()  # Fulfillment request ID
        itinstance = Item(itemid, fulfillmentreqid, self.code)  # Create a new item object

        return itinstance

    # Construct an event object from a single row in the events report
    def construct_event(self, evrow):
        itemid = evrow.Column2.get_text()  # Event type description
        eventstart = evrow.Column1.get_text()  # Event start date
        evinstance = Event(itemid, eventstart, self.code)  # Create a new event object

        return evinstance


# Request object
class Request(db.Model):
    id = sa.Column(sa.BigInteger, primary_key=True)
    fulfillmentreqid = sa.Column(sa.String(255), nullable=True)
    requestorid = sa.Column(sa.String(255), nullable=True)
    borreqstat = sa.Column(sa.String(255), nullable=True)
    internalid = sa.Column(sa.String(255), nullable=True)
    borcreate = sa.Column(sa.Date, nullable=True)
    title = sa.Column(sa.String(510), nullable=True)
    author = sa.Column(sa.String(255), nullable=True)
    networknum = sa.Column(sa.String(255), nullable=True)
    partnerstat = sa.Column(sa.String(255), nullable=True)
    reqsend = sa.Column(sa.DateTime, nullable=True)
    days = sa.Column(sa.Integer, nullable=True)
    requestor = sa.Column(sa.String(255), nullable=True)
    partnername = sa.Column(sa.String(255), nullable=True)
    partnercode = sa.Column(sa.String(255), nullable=True)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(
        self, fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author, networknum, partnerstat,
        reqsend, days, requestor, partnername, partnercode, instcode
    ):
        self.fulfillmentreqid = fulfillmentreqid
        self.requestorid = requestorid
        self.borreqstat = borreqstat
        self.internalid = internalid
        self.borcreate = borcreate
        self.title = title
        self.author = author
        self.networknum = networknum
        self.partnerstat = partnerstat
        self.reqsend = reqsend
        self.days = days
        self.requestor = requestor
        self.partnername = partnername
        self.partnercode = partnercode
        self.instcode = instcode


# Item object
class Item(db.Model):
    id = sa.Column(sa.BigInteger, primary_key=True)
    itemid = sa.Column(sa.String(255), nullable=False)
    fulfillmentreqid = sa.Column(sa.String(255), nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, itemid, fulfillmentreqid, instcode):
        self.itemid = itemid
        self.fulfillmentreqid = fulfillmentreqid
        self.instcode = instcode


# Event object
class Event(db.Model):
    id = sa.Column(sa.BigInteger, primary_key=True)
    itemid = sa.Column(sa.String(255), nullable=False)
    eventstart = sa.Column(sa.DateTime, nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, itemid, eventstart, instcode):
        self.itemid = itemid
        self.eventstart = eventstart
        self.instcode = instcode


class Inst_update(db.Model):
    id = sa.Column(sa.BigInteger, primary_key=True)
    instcode = sa.Column(sa.ForeignKey(Institution.code))
    last_update = sa.Column(sa.DateTime, nullable=False)

    def __init__(self, instcode, last_update):
        self.instcode = instcode
        self.last_update = last_update


class User(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(255), nullable=False)
    displayname = sa.Column(sa.String(255), nullable=True)
    instcode = sa.Column(sa.ForeignKey(Institution.code))
    admin = sa.Column(sa.Boolean, nullable=False)
    last_login = sa.Column(sa.DateTime, nullable=True)

    def __init__(self, username, displayname, instcode, admin, last_login):
        self.username = username
        self.displayname = displayname
        self.instcode = instcode
        self.admin = admin
        self.last_login = last_login


####################
#  Helper Methods  #
####################

# Get a list of all institutions from the database
def get_all_institutions():
    institutions = db.session.execute(db.select(Institution).order_by(Institution.name)).scalars()
    return institutions


# Get a single institution from the database
def get_institution(code):
    institution = db.one_or_404(
        db.select(Institution).filter_by(code=code),
        description=f"Institution '{code}' not found",
    )
    return institution


# Get a single institution from the database as a scalar
def get_institution_scalar(code):
    inst = db.session.execute(db.select(Institution).filter(Institution.code == code)).scalar_one()
    return inst


# Validate and submit the add institution form
def submit_inst_add_form(request):
    if not request.form['code'] or not request.form['name'] or not request.form['key'] or not \
            request.form['exceptions'] or not request.form['items'] or not request.form['events']:
        flash('Please enter all the fields', 'error')
    else:
        institution = Institution(request.form['code'], request.form['name'], request.form['key'],
                                  request.form['exceptions'], request.form['items'], request.form['events'])
        db.session.add(institution)
        db.session.commit()
        flash('Record was successfully added', 'success')
        return redirect(url_for('institution_detail', code=institution.code))


# Validate and submit the edit institution form
def submit_inst_edit_form(request, institution):
    if not request.form['code'] or not request.form['name'] or not request.form['key'] \
            or not request.form['exceptions'] or not request.form['items'] or not request.form['events']:
        flash('Please enter all the fields', 'error')
    else:
        institution.code = request.form['code']
        institution.name = request.form['name']
        institution.key = request.form['key']
        institution.exceptions = request.form['exceptions']
        institution.items = request.form['items']
        institution.events = request.form['events']
        db.session.commit()
        flash('Record was successfully updated', 'success')
        return redirect(url_for('institution_detail', code=institution.code))


# Check if the user exists in the database
def check_user(username):
    user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
    return user


# Set the last login time for the user
def set_last_login(user):
    user.last_login = datetime.now()  # Set the last login time to the current time
    db.session.commit()  # Commit the changes


# Set the user's admin status based on the database
def set_user_admin(user, session):
    if user.admin is True:  # Check if the user is an admin
        session['authorizations'].append('admin')  # If they are, add the admin authorization to the session


# Check if the username is in the admin list
def admincheck_user(session):
    if session['username'] in admins:  # Check if the user is an admin
        admincheck = True  # If they are, set admincheck to True
    else:
        admincheck = False  # If they are not, set admincheck to False

    return admincheck


# Add the user to the database
def add_user(session, admincheck):

    # Create the user object
    user = User(session['username'], session['display_name'], session['user_home'], admincheck, datetime.now())
    db.session.add(user)  # Add the user to the database
    db.session.commit()  # Commit the changes


# Log the user in
def user_login(session, user_data):

    # Set the session variables
    session['username'] = user_data['primary_id']  # Set the username
    session['user_home'] = user_data['inst']  # Set the user's home institution
    session['display_name'] = user_data['full_name']  # Set the user's display name
    session['authorizations'] = user_data['authorizations']  # Set the user's authorizations

    user = check_user(session['username'])  # Check if the user exists in the database

    # If the user is in the database...
    if user is not None:
        set_last_login(user)  # ..set the last login time for the user
        set_user_admin(user, session)  # ..set the user's admin status

    # If the user isn't in the database...
    else:
        admincheck = admincheck_user(session)  # ...check if the user is an admin
        add_user(session, admincheck)  # ...add the user to the database


# Add an update to the database
def add_update(instcode, last_update):
    update = Inst_update(instcode, last_update)  # Create the update object
    db.session.add(update)  # Add the update to the database
    db.session.commit()  # Commit the changes


def get_last_update(instcode):
    update = db.session.execute(
        db.select(Inst_update).filter(Inst_update.instcode == instcode).order_by(sa.desc(
            Inst_update.last_update))).first()
    return update


def get_all_last_updates():
    updates = db.session.execute(
        db.select(Inst_update.instcode, sa.func.max(Inst_update.last_update)).group_by(Inst_update.instcode)).scalars()
    return updates
