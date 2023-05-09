import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup

db = SQLAlchemy()

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

    def get_events(self):
        params = 'analytics/reports?limit=1000&col_names=true&path=' + self.events + '&apikey=' + self.key
        response = api_call(params)
        events = soupify(response)
        return events


# Request object
class Request(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    fulfillmentreqid = sa.Column(sa.Integer, nullable=False)
    requestorid = sa.Column(sa.String(255), nullable=False)
    borreqstat = sa.Column(sa.String(255), nullable=False)
    internalid = sa.Column(sa.Integer, nullable=False)
    borcreate = sa.Column(sa.Date, nullable=False)
    title = sa.Column(sa.String(255), nullable=False)
    author = sa.Column(sa.String(255), nullable=True)
    networknum = sa.Column(sa.Integer, nullable=True)
    partnerstat = sa.Column(sa.String(255), nullable=False)
    reqsend = sa.Column(sa.DateTime, nullable=True)
    days = sa.Column(sa.Integer, nullable=False)
    requestor = sa.Column(sa.String(255), nullable=False)
    partnername = sa.Column(sa.String(255), nullable=False)
    partnercode = sa.Column(sa.String(255), nullable=False)
    itemid = sa.Column(sa.Integer, nullable=True)
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


# Event object
class Event(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    itemid = sa.Column(sa.Integer, nullable=False)
    eventstart = sa.Column(sa.DateTime, nullable=False)
    instcode = sa.Column(sa.ForeignKey(Institution.code))

    def __init__(self, eventid, itemid, eventstart):
        self.eventid = eventid
        self.itemid = itemid
        self.eventstart = eventstart


####################
# Helper functions #
####################

# Make an API call to Alma
def api_call(params):
    api_route = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/'
    path = api_route + params
    response = requests.request('GET', path).content
    return response


# Turn the API response into a BeautifulSoup object
def soupify(response):
    soup = BeautifulSoup(response, features="xml")
    return soup


# Populate a list of Request objects from the Exceptions report
def get_rows(soup, institution):
    rows = soup.find_all('Row')
    exreport = []
    for row in rows:
        exreport.append(row)

    return exreport


# Get a list of all institutions from the database
def get_all_institutions():
    institutions = db.session.execute(db.select(Institution).order_by(Institution.name)).scalars()
    return institutions
