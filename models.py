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
    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.String(255), nullable=False)
    name = sa.Column(sa.String(255), nullable=False)
    key = sa.Column(sa.String(255), nullable=True)
    exceptions = sa.Column(sa.String(255), nullable=True)
    transit = sa.Column(sa.String(255), nullable=True)

    def __init__(self, code, name, key, exceptions, transit):
        self.code = code
        self.name = name
        self.key = key
        self.exceptions = exceptions
        self.transit = transit

    # Get a single institution from the database
    def get_institution(self):
        institution = db.one_or_404(
            db.select(Institution).filter_by(code=self.code),
            description=f"Institution '{self.code}' not found",
        )
        return institution

    # Get a single institution from the database as a scalar
    def get_institution_scalar(self):
        institution = db.session.execute(db.select(Institution).filter_by(code=self.code)).scalar_one()
        return institution

    # Get a single institution's exceptions report from the Alma Analytics API
    def get_exceptions(self):
        params = 'analytics/reports?limit=1000&col_names=true&path=' + self.exceptions + '&apikey=' + self.key
        response = api_call(params)
        exceptions = soupify(response)
        return exceptions


# Request object
class Request:
    def __init__(
        self, fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author, networknum, partnerstat,
        reqsend, days, requestor, partnername, partnercode
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

    # Populate Request object from a row in the Exceptions report
    def populate_from_report(self, row):
        try:
            self.author = row.Column1.get_text()
        except AttributeError:
            self.author = None

        try:
            self.networknum = row.Column2.get_text()
        except AttributeError:
            self.networknum = None

        self.title = row.Column3.get_text()
        self.borcreate = row.Column4.get_text()
        self.borreqstat = row.Column5.get_text()
        self.fulfillmentreqid = row.Column6.get_text()
        self.internalid = row.Column7.get_text()
        self.partnerstat = row.Column8.get_text()

        try:
            self.reqsend = row.Column9.get_text()

        except AttributeError:
            self.reqsend = None

        self.partnercode = row.Column10.get_text()
        self.partnername = row.Column11.get_text()
        self.requestor = row.Column12.get_text()
        self.requestorid = row.Column13.get_text()

        try:
            self.days = row.Column14.get_text()
        except AttributeError:
            self.days = None

        return self

    # Get Borrowing Request details from Alma User/Fulfillment API
    def get_request(self, key):
        params = 'users/' + self.requestorid + '/requests/' + self.fulfillmentreqid + '?apikey=' + key
        response = api_call(params)
        request = soupify(response)
        return request


class Event:
    def __init__(self, eventid):
        self.eventid = eventid


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
def get_rows(soup):
    rows = soup.find_all('Row')
    exreport = []
    for row in rows:
        instance = Request(None, None, None, None, None, None, None, None, None, None, None, None, None, None)
        instance.populate_from_report(row)
        exreport.append(instance)

    return exreport


# Get a list of all institutions from the database
def get_all_institutions():
    institutions = db.session.execute(db.select(Institution).order_by(Institution.name)).scalars()
    return institutions
