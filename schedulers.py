from models import Request, Event, get_all_institutions
from utils import database_add, delete_rows, get_rows


# Update reports for all institutions
def update_reports():
    # Get all institutions
    institutions = get_all_institutions()

    # Loop through the institutions
    for institution in institutions:

        # Delete all existing requests and events for the institution
        delete_rows(Request, institution.code)
        delete_rows(Event, institution.code)

        # Requests
        exceptions = institution.get_exceptions()  # Exceptions report
        exrows = get_rows(exceptions)  # Exceptions report rows

        # Check if there are any requests
        if exrows is not None:

            # Loop through the rows in the exceptions report
            for exrow in exrows:
                exinstance = institution.construct_request(exrow)  # Create a new request object
                database_add(exinstance)  # Add the request to the database

        # Events
        events = institution.get_events()  # Events report
        evrows = get_rows(events)  # Events report rows

        # Check if there are any events
        if evrows is not None:

            # Loop through the rows in the events report
            for evrow in evrows:
                evinstance = institution.construct_event(evrow)  # Create a new event object
                database_add(evinstance)  # Add the event to the database
