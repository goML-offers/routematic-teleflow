import json
import os
import uuid
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function simulates the creation of a trouble ticket in an
    external system like Jira or ServiceNow.
    In a real-world scenario, this would make an API call to that system.
    """
    load_dotenv()

    assignee = event.get('assignee', 'RAN_Team')
    title = event.get('title', 'No Title Provided')
    details = event.get('details', {})
    
    if not details:
        return {'statusCode': 400, 'body': json.dumps({"error": "details from a recommendation are required."})}

    print(f"CreateTicket Tool: Simulating creation of ticket for '{assignee}' with title '{title}'.")
    
    # Mocked ticket creation logic
    ticket_id = f"INC-{str(uuid.uuid4())[:6].upper()}"
    
    print(f"--- Ticket Details ---")
    print(f"ID: {ticket_id}")
    print(f"Title: {title}")
    print(f"Assignee: {assignee}")
    print(f"Justification: {details.get('justification')}")
    print(f"Steps: {details.get('steps')}")
    print(f"----------------------")

    response_body = {
        "ticket_id": ticket_id,
        "status": "Created",
        "details": f"Successfully created ticket {ticket_id} and assigned it to {assignee}."
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "assignee": "RAN_Optimization_Team",
        "title": "High RRC Failures on Cell 12345",
        "details": {
            "justification": "RCA indicates a recent power parameter change is the likely cause.",
            "steps": ["Step 1: Revert change.", "Step 2: Monitor."]
        }
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
