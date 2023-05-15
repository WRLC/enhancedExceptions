import sqlalchemy as sa
from flask import flash, redirect, url_for
from utils import construct_request_tuple, db


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
    # TODO: Rewrite this to use item table
    def get_requests(self):
        requests = db.session.execute(db.select(
            Request.borreqstat, Request.internalid, Request.borcreate, Request.title, Request.author,
            Request.networknum, Request.partnerstat, Request.reqsend, Request.days, Request.requestor,
            Request.partnername, Request.partnercode, Event.eventstart
        ).join(Item, Item.fulfillmentreqid == Request.fulfillmentreqid, isouter=True).join(
            Event, Event.itemid == Item.itemid, isouter=True
        ).filter(
            Request.instcode == self.code
        ).order_by(
            Request.borreqstat, Request.internalid.desc(), Request.borcreate.desc(), Request.reqsend.desc()
        )).all()
        return requests

    # Construct a request object from a single row in the exceptions report
    def construct_request(self, exrow):
        request_tuple = construct_request_tuple(exrow)

        # Create a new request object
        exinstance = Request(request_tuple[0], request_tuple[1], request_tuple[2], request_tuple[3], request_tuple[4],
                             request_tuple[5], request_tuple[6], request_tuple[7], request_tuple[8], request_tuple[9],
                             request_tuple[10], request_tuple[11], request_tuple[12], request_tuple[13],
                             self.code)

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
    id = sa.Column(sa.Integer, primary_key=True)
    fulfillmentreqid = sa.Column(sa.String(255), nullable=False)
    requestorid = sa.Column(sa.String(255), nullable=False)
    borreqstat = sa.Column(sa.String(255), nullable=False)
    internalid = sa.Column(sa.BigInteger, nullable=False)
    borcreate = sa.Column(sa.Date, nullable=False)
    title = sa.Column(sa.String(510), nullable=True)
    author = sa.Column(sa.String(255), nullable=True)
    networknum = sa.Column(sa.String(255), nullable=True)
    partnerstat = sa.Column(sa.String(255), nullable=False)
    reqsend = sa.Column(sa.DateTime, nullable=True)
    days = sa.Column(sa.Integer, nullable=True)
    requestor = sa.Column(sa.String(255), nullable=False)
    partnername = sa.Column(sa.String(255), nullable=False)
    partnercode = sa.Column(sa.String(255), nullable=False)
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
    id = sa.Column(sa.Integer, primary_key=True)
    itemid = sa.Column(sa.BigInteger, nullable=False)
    fulfillmentreqid = sa.Column(sa.String(255), nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, itemid, fulfillmentreqid, instcode):
        self.itemid = itemid
        self.fulfillmentreqid = fulfillmentreqid
        self.instcode = instcode


# Event object
class Event(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    itemid = sa.Column(sa.BigInteger)
    eventstart = sa.Column(sa.DateTime, nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, itemid, eventstart, instcode):
        self.itemid = itemid
        self.eventstart = eventstart
        self.instcode = instcode


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
