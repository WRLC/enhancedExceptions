import sqlalchemy as sa
from utils import soupify, api_call, construct_request_tuple, db


####################
#  Object Classes  #
####################

# Institution object
class Institution(db.Model):
    code = sa.Column(sa.String(255), primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    key = sa.Column(sa.String(255), nullable=True)
    exceptions = sa.Column(sa.String(255), nullable=True)
    events = sa.Column(sa.String(255), nullable=True)

    def __init__(self, code, name, key, exceptions, events):
        self.code = code
        self.name = name
        self.key = key
        self.exceptions = exceptions
        self.events = events

    # Get a single institution from the database
    def get_institution(self):
        institution = db.one_or_404(
            db.select(Institution).filter_by(code=self.code),
            description=f"Institution '{self.code}' not found",
        )
        return institution

    # Get a single institution's exceptions report from the Alma Analytics API
    def get_exceptions(self):
        params = 'analytics/reports?limit=1000&col_names=true&path=' + self.exceptions + '&apikey=' + self.key
        response = api_call(params)
        exceptions = soupify(response)
        return exceptions

    # Construct a request object from a single row in the exceptions report
    def construct_request(self, exrow):
        request_tuple = construct_request_tuple(exrow)

        # Create a new request object
        exinstance = Request(request_tuple[0], request_tuple[1], request_tuple[2], request_tuple[3], request_tuple[4],
                             request_tuple[5], request_tuple[6], request_tuple[7], request_tuple[8], request_tuple[9],
                             request_tuple[10], request_tuple[11], request_tuple[12], request_tuple[13],
                             request_tuple[14], self.code)

        return exinstance

    # Get a single institution's events report from the Alma Analytics API
    def get_events(self):
        params = 'analytics/reports?limit=1000&col_names=true&path=' + self.events + '&apikey=' + self.key
        response = api_call(params)
        events = soupify(response)
        return events

    # Construct an event object from a single row in the events report
    def construct_event(self, evrow):
        eventtype = evrow.Column1.get_text()  # Event type description
        eventdate = evrow.Column2.get_text()  # Event start date
        evinstance = Event(eventtype, eventdate, self.code)  # Create a new event object

        return evinstance


# Request object
class Request(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    fulfillmentreqid = sa.Column(sa.BigInteger, nullable=False)
    requestorid = sa.Column(sa.String(255), nullable=False)
    borreqstat = sa.Column(sa.String(255), nullable=False)
    internalid = sa.Column(sa.BigInteger, nullable=False)
    borcreate = sa.Column(sa.Date, nullable=False)
    title = sa.Column(sa.String(255), nullable=False)
    author = sa.Column(sa.String(255), nullable=True)
    networknum = sa.Column(sa.BigInteger, nullable=True)
    partnerstat = sa.Column(sa.String(255), nullable=False)
    reqsend = sa.Column(sa.DateTime, nullable=True)
    days = sa.Column(sa.Integer, nullable=True)
    requestor = sa.Column(sa.String(255), nullable=False)
    partnername = sa.Column(sa.String(255), nullable=False)
    partnercode = sa.Column(sa.String(255), nullable=False)
    itemid = sa.Column(sa.BigInteger, nullable=True)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(
        self, fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author, networknum, partnerstat,
        reqsend, days, requestor, partnername, partnercode, itemid, instcode
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
        self.itemid = itemid
        self.instcode = instcode


# Event object
class Event(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    itemid = sa.Column(sa.BigInteger, nullable=False)
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
