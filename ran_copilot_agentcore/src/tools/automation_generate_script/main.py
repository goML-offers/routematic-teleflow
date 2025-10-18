import json
import os
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function simulates the generation of a configuration script
    based on a structured recommendation.
    In a real-world scenario, this would use a template engine or more complex logic.
    """
    load_dotenv()

    recommendation = event.get('recommendation', {})
    target_vendor = event.get('target_vendor', 'Ericsson')
    
    if not recommendation:
        return {'statusCode': 400, 'body': json.dumps({"error": "A recommendation object is required."})}

    print(f"GenerateScript Tool: Simulating script generation for vendor '{target_vendor}'.")
    
    # Mocked script generation logic
    rec_title = recommendation.get('title', 'Unknown Recommendation')
    
    if "Revert Parameter Change" in rec_title:
        # This is a highly simplified example
        script_body = f"""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <managed-element>
    <gnb-du-function>
      <attributes>
        <!-- Generated based on recommendation: '{rec_title}' -->
        <!-- Logic to revert specific parameter would go here -->
        <tx-power>40</tx-power>
      </attributes>
    </gnb-du-function>
  </managed-element>
</config>
        """.strip()
        
        script_language = "XML_NetConf"
    else:
        script_body = "# No specific action defined for this recommendation type."
        script_language = "text"

    response_body = {
        "script_language": script_language,
        "script_body": script_body
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "target_vendor": "Ericsson",
        "recommendation": {
            "title": "Revert Parameter Change to Resolve Critical Alarms",
            "justification": "RCA indicates a recent power parameter change is the likely cause."
        }
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
