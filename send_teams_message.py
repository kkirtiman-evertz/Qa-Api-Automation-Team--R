import requests

people_queue = [
    {"name": "Kumar", "mailId": "kkirtiman@evertz.com"},
    {"name": "Sen", "mailId": "ssen@evertz.com"},
    {"name": "Anirudh ", "mailId": "avipinkumar@evertz.com"},
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
    teams_webhook_url = "YOUR_TEAMS_WEBHOOK_URL"  # Replace with your actual webhook URL
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(teams_webhook_url, json=message, headers=headers)
    if response.status_code == 200:
        print("Reminder sent successfully.")
    else:
        print("Failed to send reminder.")

# Create mentions for all people in the queue
mentions = [create_mention(person) for person in people_queue]

# Send a single reminder message mentioning all people
send_reminder(mentions)
