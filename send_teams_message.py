import requests

 
people_queue = [
    {"name": "Shankhajit Sen","mail":"ssen@evertz.com"},
]

 
def send_reminder(person):
    mention = person['name']  # Mention by name
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
                            "text": f"Hi {mention} team, This is a test to check whether the tags are working fine or not. Please ignore it. Thank you!"
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.0",
                    "msteams": {
                        "width": "Full",
                        "entities": [
                            {
                                "type": "mention",
                                "text": mention,
                            }
                        ]
                    }
                }
            }
        ]
    }

    teams_webhook_url = "https://evertz1.webhook.office.com/webhookb2/33be58bf-bed8-4287-bd32-7b739fd3a2f6@e7ca1d1b-0b74-449f-8cc2-a9865bfc0a5f/IncomingWebhook/3fd543a567cb4d55ad46646ef1a798e2/bb4014fc-682b-4603-bb76-e94aff3c8d10"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(teams_webhook_url, json=message, headers=headers)
    if response.status_code == 200:
        print("Reminder sent successfully.")
    else:
        print("Failed to send reminder.")

# Send reminders to each person in the queue
for person in people_queue:
    send_reminder(person)


