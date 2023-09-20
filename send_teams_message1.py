import requests

 


people_queue = [
    {"name": "Shankhajit Sen", "mailId": "kkirtiman@evertz.com"},
]

 


def send_reminder(person):
    mention = f"<at>{person['name']}</at>"
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
                            "text": f"Hi {mention} team, This a test to check whether the tags are working fine or not.Please ignore it Thank you! #CSReleaseQA"
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
                                "mentioned": {
                                    "id": person['mailId'],
                                    "name": person['name']
                                }
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










# import requests
# message = {
#     "type": "message",
#     "attachments": [
#         {
#             "contentType": "application/vnd.microsoft.card.adaptive",
#             "content": {
#                 "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
#                 "type": "AdaptiveCard",
#                 "version": "1.4",
#                 "body": [
#                     {
#                         "type": "TextBlock",
#                         "id": "MentionTextBlock",
#                         "text": "Fun with mentions!",
#                         "weight": "Bolder",
#                         "size": "Medium"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "This is user mention. Hi: <at>Kumar Kiritman</at>!",
#                         "size": "Medium"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "And this mentions tag <at>CS Release QA</at>!",
#                         "size": "Medium"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "This is channel mention. Hello: <at>NotificationTest</at>!",
#                         "size": "Medium"
#                     }
#                 ],
#                 "msteams": {
#                     "entities": [
#                         {
#                             "type": "mention",
#                             "text": "<at>Kumar Kirtiman</at>",
#                             "mentioned": {
#                                 "id": "kkirtiman@evertz.com",
#                                 "name": "Kumar Kirtiman"
#                             }
#                         },
#                         {
#                             "type": "mention",
#                             "text": "<at>CS Release QA</at>",
#                             "mentioned": {
#                                 "id": "CS Release QA",
#                                 "name": "CS Release QA"
#                             }
#                         },
#                         {
#                             "type": "mention",
#                             "text": "<at>NotificationTest</at>",
#                             "mentioned": {
#                                 "id": "19%3a7aca7755587a42a995e838b64712ca7f%40thread.tacv2",
#                                 "displayName": "NotificationTest",
#                                 "conversationIdentityType": "channel",
#                                 "conversationIdentityType@odata.type": "#Microsoft.Teams.GraphSvc.conversationIdentityType"
#                             }
#                         }
#                     ]
#                 }
#             }
#         }
#     ]
# }

# TEAMS_WEBHOOK_URL = " https://evertz1.webhook.office.com/webhookb2/33be58bf-bed8-4287-bd32-7b739fd3a2f6@e7ca1d1b-0b74-449f-8cc2-a9865bfc0a5f/IncomingWebhook/3fd543a567cb4d55ad46646ef1a798e2/bb4014fc-682b-4603-bb76-e94aff3c8d10"

# headers = {
#     "Content-Type": "application/json"
# }

# try:
#     response = requests.post(TEAMS_WEBHOOK_URL, json=message, headers=headers)
#     response.raise_for_status()  # Raise an exception for HTTP errors
#     print("Reminder sent successfully.")
# except requests.exceptions.RequestException as e:
#     print(f"Failed to send reminder: {e}")
