from models import Request, Item, Event, get_all_institutions
from utils import database_add, delete_rows, get_report


# Update reports for all institutions
def update_reports():
    # Get all institutions
    institutions = get_all_institutions()

    # Loop through the institutions
    for institution in institutions:

        # Delete all existing requests and events for the institution
        delete_rows(Request, institution.code)
        delete_rows(Item, institution.code)
        delete_rows(Event, institution.code)

        # Requests
        exceptions = get_report(institution.exceptions, institution.key)  # Exceptions report

        # Check if there are any requests
        if exceptions is not None:

            # Loop through the rows in the exceptions report
            for request in exceptions:
                exinstance = institution.construct_request(request)  # Create a new request object
                database_add(exinstance)  # Add the request to the database

        # Items
        items = get_report(institution.items, institution.key)  # Items report

        # Check if there are any items
        if items is not None:

            # Loop through the rows in the items report
            for item in items:
                itinstance = institution.construct_item(item)
                database_add(itinstance)

        # Events
        events = get_report(institution.events, institution.key)  # Events report

        # Check if there are any events
        if events is not None:

            # Loop through the rows in the events report
            for event in events:
                evinstance = institution.construct_event(event)  # Create a new event object
                database_add(evinstance)  # Add the event to the database
