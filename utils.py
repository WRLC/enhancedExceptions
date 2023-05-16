from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
import requests

# Create a database object
db = SQLAlchemy()

# Map exceptions report columns to database columns
exceptions_map = {
    'fulfillmentreqid': 'Column6',  # Fulfillment request ID
    'requestorid': 'Column14',  # User primary identifier
    'borreqstat': 'Column5',  # Borrowing request status
    'internalid': 'Column7',  # Internal ID
    'borcreate': 'Column4',  # Borrowing creation date
    'title': 'Column3',  # Title
    'author': 'Column1',  # Author
    'networknum': 'Column2',  # Network number
    'partnerstat': 'Column9',  # Partner status
    'reqsend': 'Column10',  # Request sending date
    'days': 'Column15',  # Days in status
    'requestor': 'Column13',  # Requestor
    'partnername': 'Column12',  # Partner name
    'partnercode': 'Column11',  # Partner code
}


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


# Get all the rows from an analytics report
def get_report(path, key):
    params = 'analytics/reports?limit=1000&col_names=true&path=' + path + '&apikey=' + key
    response = api_call(params)
    soup = soupify(response)
    rows = get_rows(soup)
    return rows
