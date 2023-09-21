import requests

people_queue = [
    {"name": "Kumar", "mailId": "kkirtiman@evertz.com"},
   
]

def create_mention(person):
    mention = f"<at>{person['name']}</at>"
    return mention

def send_reminder(mentions):
    message = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": "Channel Service Release Reminder"
                        },
                        {
                            "type": "TextBlock",
                            "wrap": True,
                            "text": f"Hi {', '.join(mentions)} team, This is a test to check whether the tags are working fine or not. Please ignore it. Thank you!"
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.0",
                    "msteams": {
                        "width": "Full",
                        "entities": [
                            {
                                "type": "mention",
                                "text": ', '.join(mentions),
                                "mentioned": [
                                    {"id": person['mailId'], "name": person['name']} for person in people_queue
                                ]
                            }
                        ]
                    }
                }
            }
        ]
    }
    teams_webhook_url = "https://evertz1.webhook.office.com/webhookb2/33be58bf-bed8-4287-bd32-7b739fd3a2f6@e7ca1d1b-0b74-449f-8cc2-a9865bfc0a5f/IncomingWebhook/3fd543a567cb4d55ad46646ef1a798e2/bb4014fc-682b-4603-bb76-e94aff3c8d10"  # Replace with your actual webhook URL
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(teams_webhook_url, json=message, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        print("Reminder sent successfully.")
    except Exception as e:
        print(f"Failed to send reminder: {str(e)}")

# Create mentions for all people in the queue
mentions = [create_mention(person) for person in people_queue]

# Send a single reminder message mentioning all people
send_reminder(mentions)
