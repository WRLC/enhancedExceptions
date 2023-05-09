from models import Institution, Request, Event, get_rows
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def update_reports():

    # Get all institutions
    institutions = Institution.get_all_institutions()

    # Loop through the institutions
    for institution in institutions:

        # Get the institution object
        inst = Institution.get_institution(institution.code)

        # Delete all existing requests for the institution
        db.session.delete(Request).where(Request.instcode == inst.code)
        db.session.commit()

        # Delete all existing events for the institution
        db.session.delete(Event).where(Event.instcode == inst.code)
        db.session.commit()

        # Get the institution's current requests
        exceptions = institution.get_exceptions()
        exrows = get_rows(exceptions)

        # Check if there are any requests
        if exrows is not None:

            # Loop through the rows in the exceptions report
            for exrow in exrows:
                fulfillmentreqid = exrow.Column6.get_text()  # Fulfillment request ID
                requestorid = exrow.Column14.get_text()  # User primary identifier
                borreqstat = exrow.Column5.get_text()  # Borrowing request status
                internalid = exrow.Column7.get_text()  # Internal ID
                borcreate = exrow.Column4.get_text()  # Borrowing creation date
                title = exrow.Column3.get_text()  # Title

                # Check for an author
                if exrow.Column1.get_text():
                    author = exrow.Column1.get_text()  # Author
                else:
                    author = None  # If no author, set to None

                # Check for a network number
                if exrow.Column2.get_text():
                    networknum = exrow.Column2.get_text()  # Network number
                else:
                    networknum = None  # If no network number, set to None

                partnerstat = exrow.Column9.get_text()  # Partner active status

                # Check for a request sending date
                if exrow.Column10.get_text():
                    reqsend = exrow.Column10.get_text()  # Request sending date
                else:
                    reqsend = None  # If no request sending date, set to None

                # Check for a days since request
                if exrow.Column15.get_text():
                    days = exrow.Column15.get_text()  # Days since request
                else:
                    days = None  # If no days since request, set to None

                requestor = exrow.Column13.get_text()  # Requestor
                partnername = exrow.Column12.get_text()  # Partner name
                partnercode = exrow.Column11.get_text()  # Partner code

                # Check for an item ID
                if exrow.Column8.get_text():
                    itemid = exrow.Column8.get_text()  # Item ID
                else:
                    itemid = None  # If no item ID, set to None

                # Create a new request object
                exinstance = Request(fulfillmentreqid, requestorid, borreqstat, internalid, borcreate, title, author,
                                     networknum, partnerstat, reqsend, days, requestor, partnername, partnercode,
                                     itemid,
                                     inst.code)

                db.session.add(exinstance)  # Add the request to the database
                db.session.commit()  # Commit the request to the database

        # Get the institution's current events
        events = institution.get_events()
        evrows = get_rows(events)

        # Check if there are any events
        if evrows is not None:

            # Loop through the rows in the events report
            for evrow in evrows:

                # Create a new event object
                evinstance = Event(evrow.Column1.get_text(), evrow.Column2.get_text(), inst.code)

                db.session.add(evinstance)  # Add the event to the database
                db.session.commit()  # Commit the event to the database
