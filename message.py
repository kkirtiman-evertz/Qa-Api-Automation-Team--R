#test
#test
import json

people_queue = [
    {"name": "Kumar", "mailId": "kkirtiman@evertz.com"},
    # {"name": "Halima", "mailId": "halimaa@evertz.com"},
    # {"name": "Ashish", "mailId": "asonone@evertz.com"},
    # Add more people as needed
]

def construct_message(people):
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
                            "markdown": True,
                            "text": f"""
                            Hi {mention_text} team,\n This is a **final test** before moving forward.\n
                            You can start assigning tickets to yourself.\n
                            Thank you!
                            ### Full Changelog 
                            - Full change log 

                            ### QA Check List
                            - Check 1 

                            ### Mention Team:
                            {mention_text}
                            """
                        },
                        {
                            "type": "TextBlock",
                            "wrap": True,
                            "markdown": True,
                            "text": f"""
                            **Full Changelog**  :  https://github.com/kkirtiman-evertz/Qa-Api-Automation-Team--R/
                            """
                        },
                        {
                            "type": "TextBlock",
                            "wrap": True,
                            "markdown": True,
                            "text": f"""
                            **QA Check List**  :  check 3
                            """
                        },
                        {
                            "type": "TextBlock",
                            "wrap": True,
                            "markdown": True,
                            "text": f"""
                            **Mention Team**  :  {mention_text}
                            """
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

    return message

message = construct_message(people_queue)

print(json.dumps(message))
