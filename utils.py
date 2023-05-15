from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
import requests

db = SQLAlchemy()


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


# Get rows from the BeautifulSoup object
def get_rows(soup):
    rows = soup.find_all('Row')
    if len(rows) == 0:
        return None
    return rows


# Delete all rows from a table for a given institution
def delete_rows(obtype, instcode):
    objs = obtype.query.filter_by(instcode=instcode).all()
    for obj in objs:
        db.session.delete(obj)
        db.session.commit()


# Add a row to the database
def database_add(dbrow):
    db.session.add(dbrow)  # Add the request to the database
    db.session.commit()  # Commit the request to the database


# Construct a request object from a single row in the exceptions report
def construct_request_tuple(exrow):
    fulfillmentreqid = exrow.Column6.get_text()  # Fulfillment request ID
    requestorid = exrow.Column14.get_text()  # User primary identifier
    borreqstat = exrow.Column5.get_text()  # Borrowing request status
    internalid = exrow.Column7.get_text()  # Internal ID
    borcreate = exrow.Column4.get_text()  # Borrowing creation date

    # Check for a title
    try:
        title = exrow.Column3.get_text()  # Title
    except AttributeError:
        title = None

    # Check for an author
    try:
        author = exrow.Column1.get_text()  # Author
    except AttributeError:
        author = None  # If no author, set to None

    # Check for a network number
    try:
        networknum = exrow.Column2.get_text()  # Network number
    except AttributeError:
        networknum = None  # If no network number, set to None

    partnerstat = exrow.Column9.get_text()  # Partner active status

    # Check for a request sending date
    try:
        reqsend = exrow.Column10.get_text()  # Request sending date
    except AttributeError:
        reqsend = None  # If no request sending date, set to None

    # Check for a days since request
    try:
        days = exrow.Column15.get_text()  # Days since request
    except AttributeError:
        days = None  # If no days since request, set to None

    requestor = exrow.Column13.get_text()  # Requestor
    partnername = exrow.Column12.get_text()  # Partner name
    partnercode = exrow.Column11.get_text()  # Partner code

    request = (fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author, networknum, partnerstat,
               reqsend, days, requestor, partnername, partnercode)

    return request


# Get all the rows from an analytics report
def get_report(path, key):
    params = 'analytics/reports?limit=1000&col_names=true&path=' + path + '&apikey=' + key
    response = api_call(params)
    soup = soupify(response)
    rows = get_rows(soup)
    return rows
