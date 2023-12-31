import requests

people_queue = [
    {"name": "Kumar", "mailId": "kkirtiman@evertz.com"},
    # {"name": "Halima", "mailId": "halimaa@evertz.com"},
    # {"name": "Ashish", "mailId": "asonone@evertz.com"},
    # Add more people as needed
]

def send_reminder(people):
    mentions = [f"<at>{person['name']}</at>" for person in people]
    mention_text = ", ".join(mentions)
    
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
                            "text": f"""Hi {mention_text} team,\n This is a **final test** before moving forward.\n
                            You can start assigning tickets to yourself.\n
                            Thank you!"""
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.0",
                    "msteams": {
                        "width": "Full",
                        "entities": [
                            {"type": "mention", "text": mention, "mentioned": {"id": person['mailId'], "name": person['name']}}
                            for person, mention in zip(people, mentions)
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

# Send a reminder message to all people in the queue
send_reminder(people_queue)
